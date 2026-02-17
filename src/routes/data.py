from fastapi import APIRouter , FastAPI, Depends , UploadFile,status,Request
import os
from helpers.config import get_settings, Settings
from controllers import DataController , ProjectController,ProcessController
import fastapi.responses as JsonResponse
import aiofiles
from models import ResponseSignal,ProjectModel
import logging
from models.db_schemas import project
from models.db_schemas.project import Project
from routes.schemas.data import ProcessFileRequest
from models.ProjectModel import ProjectModel
from models.ChunkModel import ChunkModel
from models.db_schemas import DataChunk,asset
from models.AssetModel import AssetModel
from models.enums.AssetTypeEnum import AssetTypeEnum


logger = logging.getLogger('uvicorn.error')

data_router = APIRouter(
    prefix="/api/v1/data",
    tags=["api_v1", "data"]
)

@data_router.post("/upload/{project_id}")


async def upload_data(request: Request, project_id: int, file: UploadFile,
                      app_settings: Settings = Depends(get_settings)):
        
    
    project_model = await ProjectModel.create_instances(
        db_client=request.app.state.db_client
    )

    project = await project_model.get_project_or_create_one(
        project_id=project_id
    )

    # validate the file properties
    data_controller = DataController()

    is_valid, result_signal = data_controller.validate_uploaded_file(file=file)

    if not is_valid:
        return JsonResponse.JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={
                "signal": result_signal
            }
        )

    project_dir_path = ProjectController().get_project_path(project_id=project_id)
    file_path, file_id = data_controller.generate_unique_filepath(
        orig_file_name=file.filename,
        project_id=project_id
    )

    try:
        async with aiofiles.open(file_path, "wb") as f:
            while chunk := await file.read(app_settings.FILE_DEFAULT_CHUNK_SIZE):
                await f.write(chunk)
    except Exception as e:

        logger.error(f"Error while uploading file: {e}")

        return JsonResponse.JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={
                "signal": ResponseSignal.FILE_UPLOAD_FAILED.value
            }
        )
    asset_model = await AssetModel.create_instances(db_client=request.app.state.db_client)
    asset_resource = asset.Asset(
            asset_project_id=project.project_id,
            asset_type=AssetTypeEnum.FILE.value,
            asset_name=file_id,
            asset_size=os.path.getsize(file_path)
        )
    asset_record = await asset_model.create_asset(asset=asset_resource)

    return JsonResponse.JSONResponse(
            content={
                "signal": ResponseSignal.FILE_UPLOAD_SUCCESS.value,
                "file_id": str(asset_record.asset_id),
                "project_id": str(project.project_id)
            }
        )


@data_router.post("/process/{project_id}")
async def process_file(project_id: int, process_request: ProcessFileRequest , request: Request):
    
    chunk_size = process_request.chunk_size
    overlap_size = process_request.overlap_size
    do_reset = process_request.do_reset

    project_model = await ProjectModel.create_instances(
        db_client=request.app.state.db_client
    )
    project = await project_model.get_project_or_create_one(project_id=project_id)

    process_controller = ProcessController(project_id=project_id)

    asset_model = await AssetModel.create_instances(db_client=request.app.state.db_client)

    chunk_model = await ChunkModel.create_instances(db_client=request.app.state.db_client)

    project_files_ids = {}

    if process_request.file_id is not None:
        asset_record = await asset_model.get_asset_record(
            asset_project_id=project.project_id,
            asset_name=process_request.file_id
        )
        if asset_record is None:
            return JsonResponse.JSONResponse(content=ResponseSignal.FILE_NOT_FOUND.value,
                                              status_code=status.HTTP_400_BAD_REQUEST)
        
        project_files_ids = {asset_record.asset_id : asset_record.asset_name}
    else:
        asset_model = await AssetModel.create_instances(db_client=request.app.state.db_client)
        project_files = await asset_model.get_all_project_assets(
            asset_project_id=project.project_id,
            asset_type=AssetTypeEnum.FILE.value
        )
        project_files_ids = {record.asset_id : record.asset_name for record in project_files}

    if len(project_files_ids) == 0:
        return JsonResponse.JSONResponse(content=ResponseSignal.NO_FILES_TO_PROCESS.value,
                                          status_code=status.HTTP_400_BAD_REQUEST)
    
    no_records = 0
    no_processed_files = 0

    if do_reset == 1:
            _ = await chunk_model.delete_chunks_by_project_id(
                project_id=project.project_id
            )

    for asset_id,file_id in project_files_ids.items():
        file_content = process_controller.get_file_content(file_id=file_id)

        if file_content is None or len(file_content) == 0:
            logger.warning(f"No content extracted from file: {file_id} in project: {project_id}")
            continue

        file_chunks = process_controller.process_file_content(file_content=file_content,
                                                            file_id=file_id,
                                                            chunk_size=chunk_size,
                                                            overlap_size=overlap_size)
        
        if file_chunks is None or len(file_chunks) == 0:
            return JsonResponse.JSONResponse(content=ResponseSignal.PROCESSING_FAILED.value,
                                            status_code=status.HTTP_400_BAD_REQUEST)
        

        file_chunks_records = [
            DataChunk(
                chunk_text=chunk.page_content,
                chunk_metadata=chunk.metadata,
                chunk_order=i+1,
                chunk_project_id=project.project_idid,
                chunk_asset_id=asset_id
            )
            for i, chunk in enumerate(file_chunks)
        ]

        no_records = await chunk_model.insert_many_chunks(chunks=file_chunks_records)
        no_processed_files += 1

    return JsonResponse.JSONResponse(
        content={
            "signal": ResponseSignal.PROCESSING_SUCCESS.value,
            "inserted_chunks": no_records,
            "processed_files": no_processed_files
        }
    )




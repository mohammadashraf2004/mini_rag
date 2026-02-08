from fastapi import APIRouter , FastAPI, Depends , UploadFile,status
import os
from helpers.config import get_settings, Settings
from controllers import DataController , ProjectController
import fastapi.responses as JsonResponse
import aiofiles
from models import ResponseSignal
import logging

logger = logging.getLogger('uvicorn.error')

data_router = APIRouter(
    prefix="/api/v1/data",
    tags=["api_v1", "data"]
)

@data_router.post("/upload/{project_id}")

async def upload_data(project_id: str,file : UploadFile,
                      settings : Settings = Depends(get_settings)):
    
    
    is_valid, message = DataController().validate_uploaded_file(file=file
    )

    if not is_valid:
        return JsonResponse.JSONResponse(content=ResponseSignal.FILE_TYPE_NOT_SUPPORTED.value,
                                          status_code=status.HTTP_400_BAD_REQUEST)


    project_dir_path = ProjectController().get_project_path(project_id=project_id) 
    file_path = DataController().generate_unique_filepath(orig_file_name=file.filename, project_id=project_id)
    try:
        async with aiofiles.open(file_path, 'wb') as out_file:
            while chunk := await file.read(settings.FILE_DEFAULT_CHUNK_SIZE):  # Read the file in chunks
                await out_file.write(chunk) 
    except Exception as e:
        
        logger.error(f"Error saving file: {e}")

        return JsonResponse.JSONResponse(content=ResponseSignal.FILE_UPLOAD_FAILED.value,
                                          status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)

    

    return JsonResponse.JSONResponse(content=ResponseSignal.FILE_UPLOAD_SUCCESS.value,
                                      status_code=status.HTTP_200_OK) 


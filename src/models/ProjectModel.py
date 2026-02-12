from .BaseDataModel import BaseDataModel
from .enums.DataBaseEnum import DataBaseEnum
from models.db_schemas import Project

class ProjectModel(BaseDataModel):

    def __init__(self, db_client: object):
        super().__init__(db_client = db_client)
        self.collection = self.db_client[DataBaseEnum.COLLECTIONS_PROJECT_NAME.value]

    async def create_project(self, project: Project) -> str:
         
        result = await self.collection.insert_one(project.dict(exclude={"_id"}))
        project._id = result.inserted_id
        return project

    async def get_project_or_create_one(self, project_id: str) -> Project:

        record = await self.collection.find_one({"project_id": project_id})
        if record is None:
            project = Project(project_id=project_id)
            project = await self.create_project(project)

            return project
        
        return Project(**record)
    
    async def get_all_documents(self, page: int = 1, page_size: int = 10):

        total_documents = await self.collection.count_documents({})
        total_pages = total_documents // page_size
        if total_documents % page_size > 0:
            total_pages += 1

        cursor = self.collection.find().skip((page - 1) * page_size).limit(page_size)
        projects = [Project(**doc) for doc in await cursor.to_list(length=page_size)]


from .BaseDataModel import BaseDataModel
from .enums.DataBaseEnum import DataBaseEnum
from models.db_schemas import DataChunk
from bson import ObjectId
from pymongo import InsertOne

class ChunkModel(BaseDataModel):

    def __init__(self, db_client: object):
        super().__init__(db_client = db_client)
        self.collection = self.db_client[DataBaseEnum.COLLECTIONS_CUNK_NAME.value]

    async def init_collection(self):
        all_collections = await self.db_client.list_collection_names()
        if DataBaseEnum.COLLECTIONS_CUNK_NAME.value not in all_collections:
            self.collection = await self.db_client.create_collection(DataBaseEnum.COLLECTIONS_CUNK_NAME.value)
            indexes = DataChunk.get_indexes() 
            for index in indexes: 
                await self.collection.create_index( index["key"],
                                                    name=index["name"],
                                                    unique=index["unique"] )
                
    @classmethod
    async def create_instances(cls, db_client: object):
        instance = cls(db_client)
        await instance.init_collection()
        return instance

    async def create_chunk(self, chunk: DataChunk) -> str:
         
        result = await self.collection.insert_one(chunk.dict())
        chunk._id = result.inserted_id
        return chunk
    
    async def get_chunk(self, chunk_id: str):

        result = await self.collection.find_one({"_id": ObjectId(chunk_id)})
        return DataChunk(**result) if result else None
    

    async def insert_many_chunks(self, chunks: list, batch_size: int = 100):
        
        for i in range(0, len(chunks), batch_size):
            batch = chunks[i:i + batch_size]
            operations = [InsertOne(chunk.dict()) for chunk in batch]
            await self.collection.bulk_write(operations)

        return len(chunks)
    
    async def delete_chunks_by_project_id(self, project_id: ObjectId):
        result = await self.collection.delete_many({
            "chunk_project_id": project_id
        })

        return result.deleted_count
    
    async def get_project_chunks(self, project_id: ObjectId, page: int = 1, page_size: int = 50):
        results = await self.collection.find({
            "chunk_project_id": project_id
        }).skip((page - 1) * page_size).limit(page_size).to_list(length=None)

        return [DataChunk(**result) for result in results]
    
from .BaseController import BaseController
from models.db_schemas import Project , DataChunk
from stores.llm.LLMEnums import DocumentTypeEnum
from typing import List

class NLPController(BaseController):
    def __init__(self, vector_db_client, generation_client, embedding_client):
        super().__init__()

        self.vector_db_client = vector_db_client
        self.generation_client = generation_client
        self.embedding_client = embedding_client

    def create_collection_name(self, project_id):
        return f"collection_{project_id}".strip()
    
    def reset_vector_db_collection(self, project : Project):
        collection_name = self.create_collection_name(project.project_id)
        return self.vector_db_client.delete_collection(collection_name)
    
    def get_vector_db_collection_info(self, project : Project):
        collection_name = self.create_collection_name(project.project_id)
        collection_info = self.vector_db_client.get_collection_info(collection_name = collection_name)

        return collection_info
    
    def index_into_vector_db(self, project : Project, chunks : List[DataChunk],
                            do_reset = False):
        collection_name = self.create_collection_name(project.project_id)
        
        texts = [chunk.text for chunk in chunks]
        metadatas = [chunk.metadata for chunk in chunks]

        vectors = [
            self.embedding_client.embed_text(text=text, 
                                             document = DocumentTypeEnum.DOCUMENT) 
            for text in texts
        ]

        #CRETE COLLECTION IF NOT EXISTS
        _ = self.vector_db_client.create_collection(collection_name = collection_name,
                                                    texts = texts,
                                                    metadatas = metadatas,
                                                    vectors = vectors)
        
        #insert INTO database
        _ = self.vector_db_client.insert_many(collection_name = collection_name,
                                        texts = texts,
                                        metadatas = metadatas,
                                        vectors = vectors)
        
        pass
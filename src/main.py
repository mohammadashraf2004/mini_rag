from fastapi import FastAPI
from routes import base, data
from motor.motor_asyncio import AsyncIOMotorClient
from helpers.config import get_settings
from stores.llm.LLMProviderFactory import LLMProviderFactory

app = FastAPI()

@app.on_event("startup")
async def startup_db_client():
    settings = get_settings()
    # 1. Store the connection (to close it later)
    app.state.mongo_conn = AsyncIOMotorClient(settings.MONGO_URI)
    
    # 2. Store the specific database object
    app.state.db_client = app.state.mongo_conn[settings.MONGO_DB_NAME]

    llm_provider_factory = LLMProviderFactory(settings)
    #generation client
    app.state.generation_client = llm_provider_factory.create_provider(provider=settings.GENERATION_BACKEND)
    app.state.generation_client.set_generation_model(settings.GENERATION_MODEL_ID)

    #embedding client
    app.state.embedding_client = llm_provider_factory.create_provider(provider=settings.EMBEDDING_BACKEND)
    app.state.embedding_client.set_embedding_model(model_id=settings.EMBEDDING_MODEL_ID, embedding_size=settings.EMBEDDING_MODEL_SIZE)

    app
    
@app.on_event("shutdown")
async def shutdown_db_client():
    # Properly close the connection
    if hasattr(app.state, "mongo_conn"):
        app.state.mongo_conn.close()
        print("🛑 MongoDB connection closed")

#app.router.lifespan.on_event("startup")(startup_db_client)
#app.router.lifespan.on_event("shutdown")(shutdown_db_client)


app.include_router(base.base_router)
app.include_router(data.data_router)




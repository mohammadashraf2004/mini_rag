from fastapi import FastAPI
from routes import base, data ,nlp
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from helpers.config import get_settings
from stores.llm.LLMProviderFactory import LLMProviderFactory
from stores.vectordb.VectorDBProviderFactory import VectorDBProviderFactory
from stores.llm.templates.template_parser import TemplateParser


app = FastAPI()


async def startup_span():
    settings = get_settings()
    # 1. Store the connection (to close it later)
    postgres_conn = f"postgresql+asyncpg://{settings.POSTGRES_USERNAME}:{settings.POSTGRES_PASSWORD}@{settings.POSTGRES_HOST}:{settings.POSTGRES_PORT}/{settings.POSTGRES_MAIN_DATABASE}"

    app.db_engine = create_async_engine(postgres_conn)
    app.db_client = sessionmaker(
        app.db_engine, class_=AsyncSession, expire_on_commit=False
    )

    llm_provider_factory = LLMProviderFactory(settings)
    vector_db_provider_factory = VectorDBProviderFactory(config=settings,db_client=app.db_client)
    #generation client
    app.state.generation_client = llm_provider_factory.create(provider=settings.GENERATION_BACKEND)
    app.state.generation_client.set_generation_model(model_id =settings.GENERATION_MODEL_ID)

    #embedding client
    app.state.embedding_client = llm_provider_factory.create(provider=settings.EMBEDDING_BACKEND)
    app.state.embedding_client.set_embedding_model(model_id=settings.EMBEDDING_MODEL_ID,
                                                    embedding_size=settings.EMBEDDING_MODEL_SIZE)

    app.state.vectordb_client = vector_db_provider_factory.create(provider=settings.VECTOR_DB_BACKEND)
    await app.state.vectordb_client.connect()

    app.state.template_parser = TemplateParser(
        language=settings.PRIMARY_LANG,
        default_language=settings.DEFAULT_LANG,
    )


async def shutdown_span():
    # Properly close the connection
    if hasattr(app.state, "mongo_conn"):
        app.state.mongo_conn.close()
        print("🛑 MongoDB connection closed")

app.on_event("startup")(startup_span)
app.on_event("shutdown")(shutdown_span)


app.include_router(base.base_router)
app.include_router(data.data_router)
app.include_router(nlp.nlp_router)




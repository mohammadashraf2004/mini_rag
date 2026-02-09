from fastapi import FastAPI
from routes import base_router, data_router
from motor.motor_asyncio import AsyncIOMotorClient
from helpers.config import Settings


app = FastAPI()
@app.on_event("startup")
async def startup_db_client():
    settings = Settings()
    app.mongodb_conn = AsyncIOMotorClient(settings.MONGO_URI)
    app.mongodb_client = app.mongodb_conn[settings.MONGO_DB_NAME]

@app.on_event("shutdown")
async def shutdown_db_client(): 
    app.mongodb_conn.close()

app.include_router(base_router)
app.include_router(data_router)




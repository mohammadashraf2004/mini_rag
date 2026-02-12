from fastapi import FastAPI
from routes import base, data
from motor.motor_asyncio import AsyncIOMotorClient
from helpers.config import get_settings

app = FastAPI()

@app.on_event("startup")
async def startup_db_client():
    settings = get_settings()
    # 1. Store the connection (to close it later)
    app.state.mongo_conn = AsyncIOMotorClient(settings.MONGO_URI)
    
    # 2. Store the specific database object
    app.state.db_client = app.state.mongo_conn[settings.MONGO_DB_NAME]
    
@app.on_event("shutdown")
async def shutdown_db_client():
    # Properly close the connection
    if hasattr(app.state, "mongo_conn"):
        app.state.mongo_conn.close()
        print("🛑 MongoDB connection closed")


app.include_router(base.base_router)
app.include_router(data.data_router)




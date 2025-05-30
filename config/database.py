from motor.motor_asyncio import AsyncIOMotorClient
from config.settings import settings


class Database:
    client: AsyncIOMotorClient = None
    database = None


db = Database()


async def get_database() -> AsyncIOMotorClient:
    return db.database


async def connect_to_mongo():
    """Create database connection"""
    db.client = AsyncIOMotorClient(settings.mongodb_url)
    db.database = db.client[settings.database_name]
    print("Connected to MongoDB")


async def close_mongo_connection():
    """Close database connection"""
    if db.client:
        db.client.close()
        print("Disconnected from MongoDB")
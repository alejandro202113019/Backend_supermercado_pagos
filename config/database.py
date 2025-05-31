from motor.motor_asyncio import AsyncIOMotorClient
from config.settings import settings


class Database:
    client: AsyncIOMotorClient = None
    database = None


db = Database()


async def get_database():
    """Retorna la instancia de la base de datos"""
    if db.database is None:
        # Si no hay conexión, crear una nueva
        await connect_to_mongo()
    return db.database


async def connect_to_mongo():
    """Create database connection"""
    try:
        db.client = AsyncIOMotorClient(settings.mongodb_url)
        db.database = db.client[settings.database_name]
        
        # Probar la conexión
        await db.client.admin.command('ping')
        print("Connected to MongoDB")
        
    except Exception as e:
        print(f"Error connecting to MongoDB: {e}")
        raise


async def close_mongo_connection():
    """Close database connection"""
    if db.client:
        db.client.close()
        db.database = None
        print("Disconnected from MongoDB")
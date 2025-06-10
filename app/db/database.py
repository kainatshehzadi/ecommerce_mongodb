from motor.motor_asyncio import AsyncIOMotorClient
import os
from dotenv import load_dotenv

load_dotenv()

MONGO_URL = os.getenv("MONGO_URL")
DB_NAME = "ecommerce"

client = None
db = None

async def connect_to_mongo():
    global client, db
    client = AsyncIOMotorClient(MONGO_URL)
    db = client[DB_NAME]

def get_db():
    return db

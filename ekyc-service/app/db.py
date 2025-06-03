from motor.motor_asyncio import AsyncIOMotorClient
from bson import ObjectId
import bcrypt
import datetime
from app.config import MONGODB_URI

mongo_uri = MONGODB_URI
client = AsyncIOMotorClient(mongo_uri)  
db = client["test"]
usercccds_collection = db["usercccds"]
users_collection=db["users"]

async def get_business_users(businessId:str):
    users_cursor = users_collection.find({})
    users = []
    async for user in users_cursor:
        user["businessId"] = businessId
        users.append(user)
    return users

async def insert_user_cccd(doc: dict):
    return await usercccds_collection.insert_one(doc)
from motor.motor_asyncio import AsyncIOMotorClient
from bson import ObjectId
import bcrypt
import datetime
from app.config import MONGODB_URI


mongo_uri = MONGODB_URI
client = AsyncIOMotorClient(mongo_uri)  
db = client["test"]
users_collection = db["users"]
usercccds_collection = db["usercccds"]
otp_collection = db["otps"]

async def get_user_by_email(email: str):
    return await users_collection.find_one({"email": email})

async def check_db_connection():
    try:
        await db.command("ping")
        print("✅ DB connection successful")
        return True
    except Exception as e:
        print("❌ DB connection failed:", e)
        return False

async def get_all_users():
    users_cursor = users_collection.find({})
    users = []
    async for user in users_cursor:
        user["_id"] = str(user["_id"])  
        users.append(user)
    return users

async def get_user_by_id(user_id: str):
    return await users_collection.find_one({"_id": ObjectId(user_id)})

async def get_user_by_email(email: str):
    return await users_collection.find_one({"email": email})

async def create_user(data):
    hashed_password = bcrypt.hashpw(data.password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")
    
    user_doc = {
        "username": data.username,
        "email": data.email,
        "password": hashed_password,
        "businessId": ObjectId(data.businessId),
        "role":"user",
        "createdAt": datetime.datetime.utcnow(),
        "updatedAt": datetime.datetime.utcnow(),
    }

    result = await users_collection.insert_one(user_doc)
    return result.inserted_id

async def get_usercccd_by_userId(user_id:str):
    return await usercccds_collection.find_one({"userId":user_id})
from app.db import db
from app.models.verificationLog_model import VerificationLogSchema
async def create_verification_log(data: VerificationLogSchema):
    collection = db["verificationlogs"]
    doc = data.dict()
    result = await collection.insert_one(doc)
    doc["_id"] = str(result.inserted_id)
    return doc

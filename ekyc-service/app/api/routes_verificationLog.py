from datetime import datetime
from http.client import HTTPException
from fastapi import APIRouter
from fastapi.responses import JSONResponse
from app.models.verificationLog_model import VerificationLogSchema
from app.services.verificationLog_service import create_verification_log

router = APIRouter()

@router.post("/verification-log")
async def log_verification(data: VerificationLogSchema):
    try:
        log = await create_verification_log(data)
        if isinstance(log.get("timestamp"), datetime):
            log["timestamp"] = log["timestamp"].isoformat()
        return JSONResponse(content={"success": True, "log": log})
    except Exception as e:
        print("Verification log error:", e)
        raise HTTPException(500, "Failed to create verification log")
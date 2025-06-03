from fastapi import APIRouter, UploadFile, Form
from app.services.voice_service import process_voice_enroll, process_voice_verify

router = APIRouter()

@router.post("/voice-enroll")
async def voice_enroll(user_id: str = Form(...), file: UploadFile = Form(...)):
    return await process_voice_enroll(user_id, file)

@router.post("/voice-verify")
async def voice_verify(user_id: str = Form(...), file: UploadFile = Form(...)):
    return await process_voice_verify(user_id, file)

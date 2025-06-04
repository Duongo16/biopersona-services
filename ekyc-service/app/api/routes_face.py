from fastapi import APIRouter, UploadFile, File, Request, HTTPException
from app.services.face_service import process_face_verification
from app.utils.token import get_token_from_header

router = APIRouter()

@router.post("/face-verify")
async def face_verify(request: Request, faceImage: UploadFile = File(...)):
    token = get_token_from_header(request)
    if not token:
        raise HTTPException(status_code=401, detail="Unauthorized hihi")

    return await process_face_verification(token, faceImage)
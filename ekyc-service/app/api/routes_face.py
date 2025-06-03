from fastapi import APIRouter, UploadFile, File, Request, HTTPException
from app.services.face_service import process_face_verification

router = APIRouter()

@router.post("/face-verify")
async def face_verify(request: Request, faceImage: UploadFile = File(...)):
    token = request.cookies.get("token")
    if not token:
        raise HTTPException(status_code=401, detail="Unauthorized hihi")

    return await process_face_verification(token, faceImage)
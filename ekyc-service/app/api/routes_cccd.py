from fastapi import APIRouter, UploadFile, File, Request, HTTPException, Depends
from app.services.cccd_service import get_user_cccd_info, process_cccd_register
from typing import Dict

router = APIRouter()

@router.post("/cccd-register")
async def cccd_register(
    request: Request,
    idFront: UploadFile = File(...),
    idBack: UploadFile = File(...)
) -> Dict:
    token = request.cookies.get("token")
    if not token:
        raise HTTPException(status_code=401, detail="Unauthorized")

    return await process_cccd_register(token, idFront, idBack)

@router.get("/cccd-info")
async def cccd_info(request: Request):
    token = request.cookies.get("token")
    if not token:
        raise HTTPException(status_code=401, detail="Unauthorized")

    return await get_user_cccd_info(token)

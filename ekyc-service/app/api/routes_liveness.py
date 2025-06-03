from fastapi import APIRouter, UploadFile, Form, HTTPException
from fastapi.responses import JSONResponse
from app.services.liveness_service import process_liveness_check

router = APIRouter()

@router.post("/liveness-check")
async def liveness_check(userId: str = Form(...), video: UploadFile = Form(...)):
    try:
        result = await process_liveness_check(userId, video)
        return JSONResponse(content=result)
    except HTTPException as e:
        return JSONResponse(status_code=e.status_code, content={"message": e.detail})
    except Exception as e:
        return JSONResponse(status_code=500, content={"message": f"Lỗi kiểm tra liveness: {str(e)}"})

from fastapi import UploadFile, HTTPException
from app.db import usercccds_collection
from app.config import FPT_AI_API_KEY
from app.utils.cloud_file import download_file_from_cloud
import aiohttp
import os

async def process_liveness_check(user_id: str, video: UploadFile):
    # Tìm user
    user = await usercccds_collection.find_one({"userId": user_id})
    if not user or "faceUrl" not in user:
        raise HTTPException(status_code=404, detail="Không tìm thấy ảnh khuôn mặt")

    # Đọc file video và ảnh từ Cloudinary
    video_bytes = await video.read()
    cmnd_bytes = await download_file_from_cloud(user["faceUrl"])

    # Tạo form data gửi FPT.AI
    form_data = aiohttp.FormData()
    form_data.add_field("video", video_bytes, filename="video.webm", content_type="video/webm")
    form_data.add_field("cmnd", cmnd_bytes, filename="face.jpg", content_type="image/jpeg")

    headers = {
        "api-key": FPT_AI_API_KEY
    }

    async with aiohttp.ClientSession() as session:
        async with session.post("https://api.fpt.ai/dmp/liveness/v3", data=form_data, headers=headers) as res:
            result = await res.json()
            if (
                result.get("code") != "200"
                or result.get("liveness", {}).get("code") != "200"
                or result.get("face_match", {}).get("code") != "200"
            ):
                raise HTTPException(status_code=400, detail=result.get("message", "Lỗi từ FPT.AI"))

            return {
                "is_live": result["liveness"]["is_live"] == "true",
                "is_match": result["face_match"]["isMatch"] == "true",
                "similarity": float(result["face_match"].get("similarity", 0)),
                "spoofProb": float(result["liveness"].get("spoof_prob", 0)),
            }

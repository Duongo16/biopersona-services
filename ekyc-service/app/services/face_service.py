import requests
import datetime
import cloudinary.uploader
from bson import ObjectId
from fastapi import HTTPException, UploadFile
from app.config import FPT_AI_API_KEY
from app.db import usercccds_collection
from app.utils.security import decode_jwt_token

async def process_face_verification(token: str, face_image: UploadFile):
    # Giải mã JWT token để lấy userId
    decoded = decode_jwt_token(token)
    user_id = decoded.get("id")
    if not user_id:
        raise HTTPException(status_code=401, detail="Token không hợp lệ hoặc thiếu thông tin người dùng.")

    # Tìm thông tin CCCD của người dùng
    user_cccd = await usercccds_collection.find_one({"userId": user_id})
    if not user_cccd:
        raise HTTPException(status_code=400, detail="Người dùng chưa đăng ký CCCD.")

    # Kiểm tra định dạng ảnh hợp lệ
    allowed_types = ["image/png", "image/jpeg", "image/jpg"]
    if face_image.content_type not in allowed_types:
        raise HTTPException(
            status_code=400,
            detail="Định dạng ảnh không hợp lệ. Chỉ chấp nhận PNG và JPG."
        )

    # Lấy ảnh CCCD từ Cloudinary
    cccd_front_url = user_cccd.get("idFrontUrl")
    if not cccd_front_url:
        raise HTTPException(status_code=400, detail="Không tìm thấy URL ảnh CCCD.")

    cccd_response = requests.get(cccd_front_url, stream=True)
    if cccd_response.status_code != 200:
        raise HTTPException(status_code=400, detail="Không thể tải ảnh CCCD từ Cloudinary.")

    # Chuẩn bị form dữ liệu cho API FPT.AI
    input_files = [
        ("file[]", ("cccd.jpg", cccd_response.raw, "image/jpeg")),
        ("file[]", (face_image.filename, await face_image.read(), face_image.content_type)),
    ]

    try:
        fpt_response = requests.post(
            "https://api.fpt.ai/dmp/checkface/v1",
            files=input_files,
            headers={"api-key": FPT_AI_API_KEY}
        )
        fpt_response.raise_for_status()
        fpt_data = fpt_response.json()
    except requests.RequestException as e:
        raise HTTPException(status_code=400, detail=f"Lỗi khi gọi API FPT.AI: {str(e)}")
    except ValueError:
        raise HTTPException(status_code=500, detail="Phản hồi từ FPT.AI không phải định dạng JSON.")

    similarity = fpt_data.get("data", {}).get("similarity", 0)

    if similarity >= 80:
        face_image.file.seek(0)
        try:
            upload_result = cloudinary.uploader.upload(face_image.file, folder="biopersona/face-url")
            face_url = upload_result["secure_url"]
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Lỗi khi upload ảnh khuôn mặt: {str(e)}")
        
        user = await usercccds_collection.find_one({"userId": user_id})
        if not user:
            raise HTTPException(status_code=404, detail="Không tìm thấy user.")
        if user.get("voiceVector") is not None and len(user.get("voiceVector")) > 0:
            await usercccds_collection.update_one(
                {"userId": user_id},
                {
                    "$set": {
                        "faceUrl": face_url,
                        "verified":True,
                        "updatedAt": datetime.datetime.now()
                    }
                }
            )
        else:
            await usercccds_collection.update_one(
                {"userId": user_id},
                {
                    "$set": {
                        "faceUrl": face_url,
                        "updatedAt": datetime.datetime.now()
                    }
                }
            )

        return {
            "message": f"Khuôn mặt đã được xác minh và lưu thành công. Điểm tương đồng: {similarity}",
            "similarity": similarity
        }

    return {
        "message": "Khuôn mặt không khớp với ảnh CCCD.",
        "similarity": similarity
    }

import datetime
import traceback
import requests
import cloudinary.uploader
from bson import ObjectId
from fastapi import HTTPException
from app.config import FPT_AI_API_KEY
from app.utils.cloud_file import file_to_data_uri
from app.db import insert_user_cccd, usercccds_collection, get_business_users
from app.utils.security import decode_jwt_token  

async def process_cccd_register(token, id_front_file, id_back_file):
    decoded = decode_jwt_token(token)
    user_id = decoded["id"]
    business_id = decoded["businessId"]

    allowed_types = ["image/png", "image/jpeg", "image/jpg"]
    if id_front_file.content_type not in allowed_types or id_back_file.content_type not in allowed_types:
        raise HTTPException(status_code=400, detail="File type not allowed")

    # Gửi ảnh mặt trước tới FPT.AI
    form = {
        "type": (None, "identity_card"),
        "image": (id_front_file.filename, await id_front_file.read(), id_front_file.content_type),
    }
    response = requests.post(
        "https://api.fpt.ai/vision/idr/vnm",
        files=form,
        headers={
            "api-key": FPT_AI_API_KEY,
        },
    )

    if response.status_code != 200 or "data" not in response.json():
        raise HTTPException(status_code=400, detail="FPT AI không trả về kết quả hợp lệ")

    fpt_data = response.json()["data"][0]
    extracted_id = fpt_data["id"]
    extracted_name = fpt_data["name"]
    extracted_dob = fpt_data["dob"]

    users = await get_business_users(business_id)
    user_ids = [ObjectId(user["_id"]) for user in users]
    existing = await usercccds_collection.find_one({"idNumber": extracted_id, "userId": {"$in": user_ids}})
    if existing:
        raise HTTPException(status_code=400, detail="CCCD đã được đăng ký ở doanh nghiệp này")

    # Upload lên Cloudinary
    id_front_file.file.seek(0)
    front_result = cloudinary.uploader.upload(id_front_file.file, folder="biopersona/id-fronts")

    id_back_file.file.seek(0)
    back_result = cloudinary.uploader.upload(id_back_file.file, folder="biopersona/id-backs")


    # Lưu DB
    cccd_doc = {
        "userId": user_id,
        "idNumber": extracted_id,
        "fullName": extracted_name,
        "dateOfBirth": extracted_dob,
        "idFrontUrl": front_result["secure_url"],
        "idBackUrl": back_result["secure_url"],
        "verified": False,
        "createdAt": datetime.datetime.now(),
    }

    await insert_user_cccd(cccd_doc)

    return {
        "message": "CCCD verified and saved successfully",
        "extractedID": extracted_id,
        "extractedName": extracted_name,
        "extractedDOB": extracted_dob,
        "frontUrl": front_result["secure_url"],
        "backUrl": back_result["secure_url"],
    }

async def get_user_cccd_info(token: str):
    try:
        decoded = decode_jwt_token(token)
        user_id = decoded["id"]

        user_cccd = await usercccds_collection.find_one({"userId": user_id})
        if not user_cccd:
            raise HTTPException(status_code=404, detail="CCCD not registered")

        return {
            "idNumber": user_cccd["idNumber"],
            "fullName": user_cccd["fullName"],
            "dateOfBirth": user_cccd["dateOfBirth"],
            "idFrontUrl": user_cccd["idFrontUrl"],
            "idBackUrl": user_cccd["idBackUrl"],
            "verified": user_cccd.get("verified", False),
            "faceUrl": user_cccd.get("faceUrl"),
            "voiceVector": user_cccd.get("voiceVector"),
        }

    except Exception as e:
        print("Error fetching CCCD info:", e)
        traceback.print_exc()
        raise HTTPException(status_code=500, detail="Failed to fetch CCCD info")
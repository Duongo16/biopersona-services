import datetime
import bcrypt
import secrets
from fastapi import Body, HTTPException, Request
from fastapi.responses import JSONResponse
from datetime import timedelta
from jose import JWTError, jwt
from app.models.auth import BusinessRegisterRequest, LoginRequest
from app.db import get_user_by_email, get_user_by_id, users_collection, otp_collection
from app.utils.security import decode_jwt_token, hash_password, verify_password, create_jwt_token
from app.config import JWT_SECRET
from app.models.user import UpdateUserRequest
from bson import ObjectId


async def login_user(data: LoginRequest):
    user = await get_user_by_email(data.email)
    if not user:
        raise HTTPException(status_code=404, detail="Email không tồn tại")

    if not verify_password(data.password, user["password"]):
        raise HTTPException(status_code=401, detail="Mật khẩu không đúng")

    if user.get("isBanned", False):
        raise HTTPException(status_code=403, detail="Tài khoản đã bị ban")

    token_exp = timedelta(days=7) if data.rememberMe else timedelta(hours=1)
    token = create_jwt_token(user, token_exp)

    response = JSONResponse(content={"message": "Đăng nhập thành công"})
    response.set_cookie(
        key="token",
        value=token,
        httponly=True,
        secure=False,  # đổi True nếu dùng HTTPS
        max_age=int(token_exp.total_seconds()),
        path="/"
    )
    return response

async def register_business_user(data: BusinessRegisterRequest):
    # Kiểm tra email tồn tại
    existing = await users_collection.find_one({"email": data.email})
    if existing:
        return {"success": False, "message": "Email này đã được sử dụng."}

    # Hash mật khẩu
    hashed = bcrypt.hashpw(data.password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
    
    
    api_key = secrets.token_hex(16)  # 32 hex characters

    user = {
        "username": data.username,
        "email": data.email,
        "password": hashed,
        "role": "business",
        "apiKey": api_key,
        "createdAt": datetime.datetime.utcnow(),
        "updatedAt": datetime.datetime.utcnow(),
    }

    await users_collection.insert_one(user)
    await otp_collection.delete_one({"email": data.email})

    return {"success": True, "apiKey": api_key}

async def change_password(request: Request, currentPassword: str, newPassword: str):
    token = request.cookies.get("token")
    if not token:
        raise HTTPException(status_code=401, detail="Unauthorized")

    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=["HS256"])
        user_id = payload.get("id")
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")

    if not user_id:
        raise HTTPException(status_code=400, detail="Invalid user ID in token")

    user = await get_user_by_id(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="Không tìm thấy người dùng")

    if not verify_password(currentPassword, user["password"]):
        raise HTTPException(status_code=401, detail="Mật khẩu hiện tại không đúng")

    hashed = hash_password(newPassword)
    await users_collection.update_one({"_id": user["_id"]}, {"$set": {"password": hashed}})

    return {"message": "✅ Đổi mật khẩu thành công"}

async def update_user(request: Request, data: UpdateUserRequest):
    token = request.cookies.get("token")
    if not token:
        raise HTTPException(status_code=401, detail="Chưa đăng nhập")

    decoded = decode_jwt_token(token)
    user_id = decoded.get("id")

    username = data.username
    if not username or not isinstance(username, str) or username.strip() == "":
        raise HTTPException(status_code=400, detail="Tên người dùng không hợp lệ")

    result = await users_collection.update_one(
        {"_id":  ObjectId(user_id)},
        {"$set": {
            "username": username.strip(),
            "updatedAt": datetime.datetime.now()
        }}
    )

    if result.modified_count == 0:
        raise HTTPException(status_code=400, detail="Không thể cập nhật user "+ username.strip())

    return {"message": "Cập nhật người dùng thành công"}
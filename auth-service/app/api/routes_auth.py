from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import random
import smtplib
import string
import bcrypt
from fastapi import APIRouter, Body, Response, Request, HTTPException
from fastapi.responses import JSONResponse
from app.models.auth import BusinessRegisterRequest, ForgotPasswordRequest, LoginRequest, RegisterRequest, SendOTPRequest, VerifyOTPRequest
from app.services.auth_service import change_password, login_user, register_business_user, update_user
from app.db import check_db_connection, create_user, get_all_users, get_user_by_email, get_usercccd_by_userId, users_collection
from app.models.user import UpdateUserRequest, UserResponse
from typing import List
from app.utils.security import decode_jwt_token
from app.db import get_user_by_id
from app.services.otp_service import generate_otp, send_otp_email, verify_otp
from app.config import EMAIL_USER, EMAIL_PASS

router = APIRouter()

@router.get("/health")
async def health_check():
    return {"status": "ok"}

@router.get("/db-status")
async def db_status():
    if await check_db_connection():
        return {"status": "connected"}
    else:
        return {"status": "failed"}

@router.post("/login")
async def login(data: LoginRequest):
    return await login_user(data)

@router.get("/users", response_model=List[UserResponse])
async def list_users():
    raw_users = await get_all_users()
    return [
        {"id": user["_id"], "email": user["email"], "username": user.get("username")}
        for user in raw_users
    ]

@router.post("/logout")
async def logout(response: Response):
    response.delete_cookie(key="token", path="/")
    return {"message": "Đăng xuất thành công"}

@router.get("/me")
async def get_me(request: Request):
    token = request.cookies.get("token")
    if not token:
        raise HTTPException(status_code=401, detail="Unauthorized")

    try:
        payload = decode_jwt_token(token)
        user_id = payload.get("id")
        if not user_id:
            raise HTTPException(status_code=401, detail="Invalid token")

        user = await get_user_by_id(user_id)
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        userCCCD = await get_usercccd_by_userId(user_id)

        return {
            "user": {
            "id": str(user["_id"]),
            "email": user["email"],
            "username": user.get("username"),
            "role": user.get("role"),
            "businessId": str(user.get("businessId")),
            "createdAt": user.get("createdAt"),
            "updatedAt": user.get("updatedAt"),
            "verified": userCCCD.get("verified", False) if userCCCD else None
            }
        }

    except Exception as e:
        print("❌ Error in /me:", e)
        raise HTTPException(status_code=401, detail="Unauthorized")

@router.post("/register")
async def register_user(data: RegisterRequest):
    existing = await get_user_by_email(data.email)
    if existing:
        raise HTTPException(status_code=400, detail="Email hoặc tên người dùng đã tồn tại")

    try:
        user_id = await create_user(data)
        return JSONResponse(content={"message": "Tạo tài khoản thành công", "id": str(user_id)}, status_code=201)
    except Exception as e:
        print("❌ Error in register:", e)
        raise HTTPException(status_code=500, detail="Lỗi máy chủ")
    
@router.post("/send-otp")
async def send_otp(data: SendOTPRequest):
    try:
        otp_code = await generate_otp(data.email)
        send_otp_email(data.email, otp_code)
        return {"message": "OTP sent"}
    except Exception as e:
        print("❌ Error sending OTP:", e)
        raise HTTPException(status_code=500, detail="Failed to send OTP")
    
@router.post("/verify-otp")
async def verify_otp_route(data: VerifyOTPRequest):
    result = await verify_otp(data.email, data.otp)

    if not result["valid"]:
        raise HTTPException(status_code=400, detail=result["reason"])

    return {"message": "Email verified"}

@router.post("/register-business")
async def register_business(data: BusinessRegisterRequest):
    try:
        result = await register_business_user(data)
        if not result["success"]:
            raise HTTPException(status_code=400, detail=result["message"])
        return {"message": "Đăng ký business thành công", "apiKey": result["apiKey"]}
    except Exception as e:
        print("❌ Error registering business:", e)
        raise HTTPException(status_code=500, detail="Đã xảy ra lỗi khi đăng ký business.")
    
@router.post("/forgot-password")
async def forgot_password(data: ForgotPasswordRequest):
    try:
        email = data.email
        if not email:
            raise HTTPException(status_code=400, detail="Email là bắt buộc")

        user = await users_collection.find_one({"email": email})
        if not user:
            raise HTTPException(status_code=404, detail="Không tìm thấy người dùng")

        # Tạo mật khẩu mới ngẫu nhiên
        new_password = "".join(random.choices(string.ascii_letters + string.digits, k=8))
        hashed_password = bcrypt.hashpw(new_password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

        await users_collection.update_one(
            {"_id": user["_id"]},
            {"$set": {"password": hashed_password}}
        )

        # Gửi email
        sender_email = EMAIL_USER
        sender_pass = EMAIL_PASS

        msg = MIMEMultipart("alternative")
        msg["Subject"] = "🔐 Mật khẩu mới từ hệ thống"
        msg["From"] = sender_email
        msg["To"] = email

        html_content = f"""
        <p>Chào {user.get("username", "bạn")},</p>
        <p>Mật khẩu mới của bạn là: <strong>{new_password}</strong></p>
        <p>Vui lòng đăng nhập và đổi lại mật khẩu ngay sau đó.</p>
        <p>Trân trọng,<br/>Đội ngũ hỗ trợ</p>
        """

        msg.attach(MIMEText(html_content, "html"))

        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
            server.login(sender_email, sender_pass)
            server.sendmail(sender_email, email, msg.as_string())

        return JSONResponse(
            status_code=200,
            content={"message": "✅ Mật khẩu mới đã được gửi đến email của bạn"}
        )

    except Exception as e:
        print("❌ Forgot password error:", e)
        raise HTTPException(status_code=500, detail="❌ Lỗi hệ thống")
    
@router.patch("/change-password")
async def change_password_route(
    request: Request,
    currentPassword: str = Body(...),
    newPassword: str = Body(...)
):
    return await change_password(request, currentPassword, newPassword)

@router.put("/update-account")
async def update_account(
    request: Request,
    data: UpdateUserRequest = Body(...)
):
    
    return await update_user(request, data)
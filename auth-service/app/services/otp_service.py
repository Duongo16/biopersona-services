import random
from datetime import datetime, timedelta
from app.db import otp_collection
from pydantic import EmailStr
import smtplib
from email.mime.text import MIMEText

async def generate_otp(email: EmailStr):
    otp_code = str(random.randint(100000, 999999))
    expires_at = datetime.utcnow() + timedelta(minutes=5)

    await otp_collection.update_one(
        {"email": email},
        {"$set": {"otp": otp_code, "expiresAt": expires_at}},
        upsert=True
    )

    return otp_code

def send_otp_email(email: str, otp_code: str):
    try:
        smtp_user = "duongnthe186310@fpt.edu.vn"
        smtp_pass = "pgdrmgzfsfgnjgfr"

        msg = MIMEText(f"Your verification code is: {otp_code}. It will expire in 5 minutes.", "html")
        msg["Subject"] = "BIOPERSONA: Your OTP Code"
        msg["From"] = smtp_user
        msg["To"] = email

        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
            server.login(smtp_user, smtp_pass)
            server.send_message(msg)
    except Exception as e:
        raise Exception("❌ Failed to send email:", e)

async def verify_otp(email: str, otp: str):
    record = await otp_collection.find_one({"email": email})
    if not record:
        return {"valid": False, "reason": "Không tìm thấy mã"}

    if record["otp"] != otp:
        return {"valid": False, "reason": "Mã không đúng"}

    if record["expiresAt"] < datetime.utcnow():
        return {"valid": False, "reason": "Mã đã hết hạn"}

    await otp_collection.delete_one({"email": email})
    return {"valid": True}

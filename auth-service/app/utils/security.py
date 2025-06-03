import bcrypt
import jwt
from datetime import datetime, timedelta
from typing import Dict
from fastapi import HTTPException
from app.config import JWT_SECRET

ALGORITHM = "HS256"

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return bcrypt.checkpw(plain_password.encode(), hashed_password.encode())

def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")

def create_jwt_token(user: Dict, expires_delta: timedelta):
    payload = {
        "id": str(user["_id"]),
        "username": user["username"],
        "email": user["email"],
        "role": user["role"],
        "businessId": str(user["businessId"]) if user.get("businessId") else None,
        "exp": datetime.utcnow() + expires_delta
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=ALGORITHM)

def decode_jwt_token(token: str):
    try:
        return jwt.decode(token, JWT_SECRET, algorithms=[ALGORITHM])
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")

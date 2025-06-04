from jose import JWTError, jwt
from fastapi import HTTPException
from app.config import JWT_SECRET

ALGORITHM = "HS256"

def decode_jwt_token(token: str):
    print("🔐 decode_jwt_token(): token =", token)
    try:
        decoded = jwt.decode(token, JWT_SECRET, algorithms=["HS256"])
        print("✅ decode_jwt_token(): decoded =", decoded)
        return decoded
    except JWTError as e:
        print("❌ JWT decode error:", str(e))
        raise


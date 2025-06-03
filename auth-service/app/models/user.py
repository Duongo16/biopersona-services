from pydantic import BaseModel, EmailStr

class UserResponse(BaseModel):
    id: str
    email: EmailStr
    username: str | None = None  # tùy dữ liệu bạn có

    class Config:
        orm_mode = True

class UpdateUserRequest(BaseModel):
    username: str

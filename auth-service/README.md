auth-service/
└── app/
├── api/
│ └── routes_auth.py # Định nghĩa tất cả route auth ở đây
├── models/
│ └── auth.py # Định nghĩa schema cho Login, Register, OTP...
├── services/
│ └── auth_service.py # Các hàm xử lý login_user, register_user,...
├── utils/
│ └── security.py # Mã hoá mật khẩu, JWT, gửi OTP,...
└── db.py # Truy cập database (MongoDB)

Setup:
pip install motor: thư viện MongoDB async driver được dùng với FastAPI để kết nối MongoDB.
pip install PyJWT: thư viện cung cấp module jwt

uvicorn app.main:app --reload

import cloudinary
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api import routes_cccd, routes_face, routes_voice, routes_liveness, routes_verificationLog
from app.config import CLOUDINARY_API_KEY, CLOUDINARY_API_SECRET, CLOUDINARY_CLOUD_NAME

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000",
    "https://biopersonahihi.vercel.app"],  
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

cloudinary.config(
    cloud_name=CLOUDINARY_CLOUD_NAME,
    api_key=CLOUDINARY_API_KEY,
    api_secret=CLOUDINARY_API_SECRET
)

app.include_router(routes_cccd.router, prefix="/ekyc")
app.include_router(routes_face.router, prefix="/ekyc")
app.include_router(routes_voice.router, prefix="/ekyc")
app.include_router(routes_liveness.router, prefix="/ekyc")
app.include_router(routes_verificationLog.router, prefix="/ekyc")


@app.get("/")
def root():
    return {"message": "eKYC Service Running 🚀"}

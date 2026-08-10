import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.core.config import settings
from app.core.database import engine, Base
from app.api.v1.api import api_router

# Create DB tables
Base.metadata.create_all(bind=engine)

import tempfile

# Ensure upload dirs exist in temp directory to avoid OneDrive file lock issues
upload_dir = os.path.join(tempfile.gettempdir(), "chatassist_uploads")
os.makedirs(os.path.join(upload_dir, "invoices"), exist_ok=True)
os.makedirs(os.path.join(upload_dir, "qrcodes"), exist_ok=True)

app = FastAPI(
    title=settings.PROJECT_NAME,
    openapi_url=f"{settings.API_V1_STR}/openapi.json"
)

# Set CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router, prefix=settings.API_V1_STR)
app.include_router(api_router, prefix="/api")
app.mount("/uploads", StaticFiles(directory=upload_dir), name="uploads")




@app.get("/")
def root():
    return {"message": "ChatAssist Platform API is running", "version": "1.0.0", "docs": "/docs"}

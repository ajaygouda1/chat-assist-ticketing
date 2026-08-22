import os
import tempfile
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.core.config import settings
from app.api.v1.api import api_router
from app.core.middleware import TraceAndSecurityMiddleware, custom_http_exception_handler, unhandled_exception_handler

# Ensure upload dirs exist in temp directory
upload_dir = os.path.join(tempfile.gettempdir(), "chatassist_uploads")
os.makedirs(os.path.join(upload_dir, "invoices"), exist_ok=True)
os.makedirs(os.path.join(upload_dir, "qrcodes"), exist_ok=True)

app = FastAPI(
    title=settings.PROJECT_NAME,
    openapi_url=f"{settings.API_V1_STR}/openapi.json"
)

# Custom Exception Handlers & Trace Middleware
app.add_middleware(TraceAndSecurityMiddleware)
app.add_exception_handler(HTTPException, custom_http_exception_handler)
app.add_exception_handler(Exception, unhandled_exception_handler)

# Configure CORS origins cleanly
origins = [
    "http://localhost:5173",
    "http://127.0.0.1:5173",
    "http://localhost:3000",
]
if settings.FRONTEND_ORIGIN and settings.FRONTEND_ORIGIN not in origins:
    origins.append(settings.FRONTEND_ORIGIN)

# Allow wildcard origins if explicitly specified, but set allow_credentials accordingly
allow_all = "*" in origins or os.getenv("ALLOW_ALL_ORIGINS", "false").lower() == "true"

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"] if allow_all else origins,
    allow_credentials=not allow_all,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router, prefix=settings.API_V1_STR)
app.include_router(api_router, prefix="/api")

if os.path.exists(upload_dir):
    app.mount("/uploads", StaticFiles(directory=upload_dir), name="uploads")

@app.get("/")
def root():
    return {"message": "ChatAssist Platform API is running", "version": "1.0.0", "docs": "/docs"}

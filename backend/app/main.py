import os
from fastapi import FastAPI, HTTPException

from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.core.config import settings
from app.core.database import engine, Base
from app.api.v1.api import api_router

# Create DB tables
Base.metadata.create_all(bind=engine)

# Auto-migration helper for SQLite schema updates
with engine.connect() as conn:
    for stmt in [
        "ALTER TABLE booking_drafts ADD COLUMN idempotency_key VARCHAR;",
        "ALTER TABLE events ADD COLUMN max_tickets_per_booking INTEGER DEFAULT 10;",
        "ALTER TABLE users ADD COLUMN is_verified BOOLEAN DEFAULT 0;",
        "ALTER TABLE users ADD COLUMN refresh_token VARCHAR;",
        "ALTER TABLE users ADD COLUMN reset_token VARCHAR;",
        "ALTER TABLE users ADD COLUMN reset_token_expires DATETIME;",
        "ALTER TABLE scan_logs ADD COLUMN gate_id INTEGER;",
        "ALTER TABLE scan_logs ADD COLUMN offline_sync BOOLEAN DEFAULT 0;"
    ]:
        try:
            from sqlalchemy import text
            conn.execute(text(stmt))
            conn.commit()
        except Exception:
            pass

import tempfile

# Ensure upload dirs exist in temp directory to avoid OneDrive file lock issues
upload_dir = os.path.join(tempfile.gettempdir(), "chatassist_uploads")
os.makedirs(os.path.join(upload_dir, "invoices"), exist_ok=True)
os.makedirs(os.path.join(upload_dir, "qrcodes"), exist_ok=True)

from app.core.middleware import TraceAndSecurityMiddleware, custom_http_exception_handler, unhandled_exception_handler
from fastapi.exceptions import RequestValidationError

app = FastAPI(
    title=settings.PROJECT_NAME,
    openapi_url=f"{settings.API_V1_STR}/openapi.json"
)

# Custom Exception Handlers & Trace Middleware
app.add_middleware(TraceAndSecurityMiddleware)
app.add_exception_handler(HTTPException, custom_http_exception_handler)
app.add_exception_handler(Exception, unhandled_exception_handler)

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

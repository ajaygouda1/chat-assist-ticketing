import os
import tempfile

class Settings:
    PROJECT_NAME: str = "ChatAssist Platform"
    API_V1_STR: str = "/api/v1"
    ENV: str = os.getenv("ENV", "development")
    SECRET_KEY: str = os.getenv("SECRET_KEY", "super-secret-key-chatassist-2026")
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7  # 7 days
    
    DEFAULT_DB_PATH: str = os.path.join(tempfile.gettempdir(), "chatassist.db").replace("\\", "/")
    # PostgreSQL primary, SQLite fallback
    DATABASE_URL: str = os.getenv("DATABASE_URL", f"sqlite:///{DEFAULT_DB_PATH}")
    REDIS_URL: str = os.getenv("REDIS_URL", "redis://localhost:6379/0")
    
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")
    QR_SIGNING_SECRET: str = os.getenv("QR_SIGNING_SECRET", os.getenv("SECRET_KEY", "super-secret-key-chatassist-2026"))
    RAZORPAY_WEBHOOK_SECRET: str = os.getenv("RAZORPAY_WEBHOOK_SECRET", "whsec_chatassist_2026")

    # Admin Platform Settings
    PLATFORM_COMMISSION_PCT: float = float(os.getenv("PLATFORM_COMMISSION_PCT", "5.0"))
    PAYMENT_PROCESSING_PCT: float = float(os.getenv("PAYMENT_PROCESSING_PCT", "2.0"))
    SEAT_HOLD_DURATION_MINUTES: int = int(os.getenv("SEAT_HOLD_DURATION_MINUTES", "10"))
    WAITLIST_CLAIM_DURATION_MINUTES: int = int(os.getenv("WAITLIST_CLAIM_DURATION_MINUTES", "15"))

    def validate(self):
        if self.ENV == "production" and self.SECRET_KEY == "super-secret-key-chatassist-2026":
            print("WARNING: Default SECRET_KEY used in production environment!")

settings = Settings()
settings.validate()





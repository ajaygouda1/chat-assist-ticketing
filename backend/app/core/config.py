import os
import tempfile

class Settings:
    PROJECT_NAME: str = "ChatAssist Platform"
    API_V1_STR: str = "/api/v1"
    ENV: str = os.getenv("ENV", "development").lower()
    SECRET_KEY: str = os.getenv("SECRET_KEY", "super-secret-key-chatassist-2026")
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7  # 7 days
    
    DEFAULT_DB_PATH: str = os.path.join(tempfile.gettempdir(), "chatassist.db").replace("\\", "/")
    DATABASE_URL: str = os.getenv("DATABASE_URL", f"sqlite:///{DEFAULT_DB_PATH}")
    REDIS_URL: str = os.getenv("REDIS_URL", "redis://localhost:6379/0")
    
    FRONTEND_ORIGIN: str = os.getenv("FRONTEND_ORIGIN", "http://localhost:5173")
    
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")
    AI_PROVIDER: str = os.getenv("AI_PROVIDER", "gemini").lower()
    GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY", "")
    AI_MODEL: str = os.getenv("AI_MODEL", "")
    QR_SIGNING_SECRET: str = os.getenv("QR_SIGNING_SECRET", os.getenv("SECRET_KEY", "super-secret-key-chatassist-2026"))
    
    RAZORPAY_KEY_ID: str = os.getenv("RAZORPAY_KEY_ID", "rzp_test_mockkey123")
    RAZORPAY_KEY_SECRET: str = os.getenv("RAZORPAY_KEY_SECRET", "mock_razorpay_secret_123")
    RAZORPAY_WEBHOOK_SECRET: str = os.getenv("RAZORPAY_WEBHOOK_SECRET", "whsec_chatassist_2026")
    PAYMENT_MODE: str = os.getenv("PAYMENT_MODE", "mock").lower()

    # Admin Platform Settings
    PLATFORM_COMMISSION_PCT: float = float(os.getenv("PLATFORM_COMMISSION_PCT", "5.0"))
    PAYMENT_PROCESSING_PCT: float = float(os.getenv("PAYMENT_PROCESSING_PCT", "2.0"))
    SEAT_HOLD_DURATION_MINUTES: int = int(os.getenv("SEAT_HOLD_DURATION_MINUTES", "10"))
    WAITLIST_CLAIM_DURATION_MINUTES: int = int(os.getenv("WAITLIST_CLAIM_DURATION_MINUTES", "15"))

    def validate(self):
        if self.ENV == "production":
            if not self.DATABASE_URL or "sqlite" in self.DATABASE_URL:
                raise ValueError("DATABASE_URL must be provided and must be a production database (PostgreSQL/Neon) in production environment.")
            if self.SECRET_KEY in ["super-secret-key-chatassist-2026", "mock_secret_key", ""]:
                raise ValueError("SECRET_KEY must be set to a secure secret in production environment.")
            if self.QR_SIGNING_SECRET in ["super-secret-key-chatassist-2026", "mock_secret_key", ""]:
                raise ValueError("QR_SIGNING_SECRET must be set to a secure secret in production environment.")
            if self.RAZORPAY_KEY_ID == "rzp_test_mockkey123" or self.RAZORPAY_KEY_SECRET == "mock_razorpay_secret_123":
                if self.PAYMENT_MODE != "mock":
                    raise ValueError("RAZORPAY_KEY_ID and RAZORPAY_KEY_SECRET must be configured in production unless PAYMENT_MODE=mock.")

settings = Settings()
settings.validate()

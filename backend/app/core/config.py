import os
import tempfile

class Settings:
    PROJECT_NAME: str = "ChatAssist Platform"
    API_V1_STR: str = "/api/v1"
    SECRET_KEY: str = os.getenv("SECRET_KEY", "super-secret-key-chatassist-2026")
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7  # 7 days
    
    DEFAULT_DB_PATH: str = os.path.join(tempfile.gettempdir(), "chatassist.db").replace("\\", "/")
    DATABASE_URL: str = os.getenv("DATABASE_URL", f"sqlite:///{DEFAULT_DB_PATH}")
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")
    QR_SIGNING_SECRET: str = os.getenv("QR_SIGNING_SECRET", os.getenv("SECRET_KEY", "super-secret-key-chatassist-2026"))

settings = Settings()




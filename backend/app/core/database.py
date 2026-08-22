import os
import sys
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from sqlalchemy.pool import NullPool
from app.core.config import settings

db_url = settings.DATABASE_URL

# Test safety guard
is_testing = "pytest" in sys.modules or "PYTEST_CURRENT_TEST" in os.environ
if is_testing:
    # If URL looks like production Neon DB, refuse to run test to protect production data
    if "neon.tech" in db_url.lower() or "neondb" in db_url.lower():
        raise RuntimeError("CRITICAL SAFETY GUARD TRIGGERED: Tests are attempting to run against a production Neon database!")
    # Use SQLite in-memory or temp file for isolated testing if not explicitly configured with TEST_DATABASE_URL
    test_url = os.getenv("TEST_DATABASE_URL")
    if test_url:
        db_url = test_url
    else:
        db_url = f"sqlite:///{settings.DEFAULT_DB_PATH}"

# Normalize postgres URL schema for psycopg driver if necessary
if db_url.startswith("postgres://"):
    db_url = db_url.replace("postgres://", "postgresql+psycopg://", 1)
elif db_url.startswith("postgresql://") and "+psycopg" not in db_url and "+psycopg2" not in db_url:
    try:
        import psycopg
        db_url = db_url.replace("postgresql://", "postgresql+psycopg://", 1)
    except ImportError:
        pass

if "sqlite" in db_url:
    engine = create_engine(
        db_url,
        connect_args={"check_same_thread": False, "timeout": 30}
    )
else:
    # Serverless safe PostgreSQL / Neon engine
    engine = create_engine(
        db_url,
        pool_pre_ping=True,
        pool_size=5,
        max_overflow=10,
        pool_recycle=1800,
        connect_args={"connect_timeout": 10}
    )

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

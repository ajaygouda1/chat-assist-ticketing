import os
import sys
import pytest

# Ensure backend directory is in sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.core.database import Base, engine, SessionLocal
from app.seed_demo import seed_demo_data

@pytest.fixture(scope="session", autouse=True)
def setup_test_database():
    """Initializes the test database and seeds demo data."""
    Base.metadata.create_all(bind=engine)
    seed_demo_data()
    yield

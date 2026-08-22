from sqlalchemy import Column, Integer, String, DateTime, Boolean, ForeignKey, JSON
from datetime import datetime
from app.core.database import Base

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    name = Column(String, nullable=False)
    hashed_password = Column(String, nullable=False)
    role = Column(String, default="customer")  # customer, organizer, gate_staff, admin, super_admin
    phone = Column(String, nullable=True)
    referral_code = Column(String, unique=True, nullable=True)
    is_active = Column(Boolean, default=True)
    is_verified = Column(Boolean, default=False)
    refresh_token = Column(String, nullable=True)
    reset_token = Column(String, nullable=True)
    reset_token_expires = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)


class OrganizerProfile(Base):
    __tablename__ = "organizer_profiles"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), unique=True, nullable=False)
    organization_name = Column(String, nullable=False)
    kyc_status = Column(String, default="UNVERIFIED")  # UNVERIFIED, PENDING, VERIFIED, REJECTED, SUSPENDED
    badge_verified = Column(Boolean, default=False)
    kyc_documents = Column(JSON, default=dict)
    created_at = Column(DateTime, default=datetime.utcnow)


class OrganizerMember(Base):
    __tablename__ = "organizer_members"

    id = Column(Integer, primary_key=True, index=True)
    organizer_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    member_user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    role = Column(String, default="VIEWER")  # OWNER, MANAGER, FINANCE, CHECK_IN_STAFF, VIEWER
    permissions = Column(JSON, default=list)
    created_at = Column(DateTime, default=datetime.utcnow)

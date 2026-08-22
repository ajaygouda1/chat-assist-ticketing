import os
from datetime import datetime, timedelta
from app.core.database import SessionLocal, engine, Base
from app.models.user import User, OrganizerProfile
from app.models.ticket import Event, Ticket
from app.models.seating import Seat
from app.services.seating_service import initialize_event_seats
from app.models.promo import PromoCode
from app.models.notification import Notification
from app.core.security import get_password_hash

def seed_demo_data():
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()

    print("--- SEEDING DEMO DATA FOR CHATASSIST ---")

    # 1. Super Admin
    if not db.query(User).filter(User.email == "admin@chatassist.com").first():
        admin = User(
            email="admin@chatassist.com",
            name="Super Admin",
            hashed_password=get_password_hash("admin123"),
            role="super_admin",
            phone="+919999900000",
            referral_code="REF-ADMIN-DEMO"
        )
        db.add(admin)
        db.commit()

    # 2. Organizers
    orgs_data = [
        {"email": "tech@events.com", "name": "Tech Events India", "org_name": "Tech Events Inc."},
        {"email": "music@events.com", "name": "Indie Music Live", "org_name": "Soundscape Productions"},
        {"email": "workshop@events.com", "name": "Dev Masters Academy", "org_name": "Dev Masters LLC"}
    ]

    organizer_users = []
    for od in orgs_data:
        user = db.query(User).filter(User.email == od["email"]).first()
        if not user:
            user = User(
                email=od["email"],
                name=od["name"],
                hashed_password=get_password_hash("password123"),
                role="organizer",
                phone="+919876500001",
                referral_code=f"REF-ORG-{od['name'][:4].upper()}"
            )
            db.add(user)
            db.commit()
            db.refresh(user)

            profile = OrganizerProfile(
                user_id=user.id,
                organization_name=od["org_name"],
                kyc_status="VERIFIED",
                badge_verified=True
            )
            db.add(profile)
            db.commit()
        organizer_users.append(user)

    # 3. Customers
    cust = db.query(User).filter(User.email == "demo@customer.com").first()
    if not cust:
        cust = User(
            email="demo@customer.com",
            name="Demo Customer",
            hashed_password=get_password_hash("password123"),
            role="customer",
            phone="+919876543210",
            referral_code="REF-CUST-DEMO"
        )
        db.add(cust)
        db.commit()
        db.refresh(cust)

    # 4. Events
    events_data = [
        {
            "title": "India AI & Deep Learning Summit",
            "description": "Full-day developer conference on LLMs, agentic workflows, and real-time AI inference.",
            "category": "Tech",
            "location": "NIMHANS Convention Centre, Bengaluru",
            "date_str": "Sat, 15 Sep 2026",
            "event_datetime": datetime.utcnow() + timedelta(days=25),
            "price": 499.0,
            "total_capacity": 500,
            "available_tickets": 450,
            "organizer_id": organizer_users[0].id,
            "status": "PUBLISHED"
        },
        {
            "title": "React 19 & Fullstack Next.js Masterclass",
            "description": "Hands-on workshop building fast server components and reactive state machines.",
            "category": "Workshop",
            "location": "Koramangala Tech Park, Bengaluru",
            "date_str": "Sun, 20 Sep 2026",
            "event_datetime": datetime.utcnow() + timedelta(days=30),
            "price": 299.0,
            "total_capacity": 150,
            "available_tickets": 120,
            "organizer_id": organizer_users[2].id,
            "status": "PUBLISHED"
        },
        {
            "title": "Bangalore Open Air Indie Fest 2026",
            "description": "Live indie rock, fusion jazz, electronic synthpop under the stars.",
            "category": "Music",
            "location": "Indiranagar Open Arena, Bengaluru",
            "date_str": "Fri, 25 Sep 2026",
            "event_datetime": datetime.utcnow() + timedelta(days=35),
            "price": 799.0,
            "total_capacity": 1000,
            "available_tickets": 850,
            "organizer_id": organizer_users[1].id,
            "status": "PUBLISHED"
        }
    ]

    for ed in events_data:
        ev = db.query(Event).filter(Event.title == ed["title"]).first()
        if not ev:
            ev = Event(**ed)
            db.add(ev)
            db.commit()
            db.refresh(ev)

            from app.services.tier_inventory_service import create_or_update_event_tiers
            create_or_update_event_tiers(db, ev, [
                {"name": "General", "price": ed["price"], "total_quantity": ed["total_capacity"], "min_per_order": 1, "max_per_order": 10},
                {"name": "VIP Pass", "price": ed["price"] * 1.5, "total_quantity": 50, "min_per_order": 1, "max_per_order": 10},
                {"name": "Standard", "price": ed["price"], "total_quantity": 100, "min_per_order": 1, "max_per_order": 10}
            ])
            initialize_event_seats(db, ev.id)

    # 5. Promos
    if not db.query(PromoCode).filter(PromoCode.code == "WELCOME20").first():
        promo = PromoCode(
            code="WELCOME20",
            discount_type="PERCENTAGE",
            discount_value=20.0,
            max_uses=200,
            min_order_amount=200.0
        )
        db.add(promo)
        db.commit()

import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

    print("[OK] DEMO SEEDING COMPLETED SUCCESSFULLY!")

if __name__ == "__main__":
    seed_demo_data()


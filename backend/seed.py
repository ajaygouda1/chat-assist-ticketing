import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.core.database import SessionLocal, engine, Base
from app.models.user import User
from app.models.ticket import Event, Ticket
from app.models.payment import Payment
from app.models.ml_models import Coupon
from app.core.security import get_password_hash


def seed_database():
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()

    # Create demo users if not present
    SUPER_ADMIN_EMAIL = "ajaymgouda999@gmail.com"
    SUPER_ADMIN_PASSWORD = os.getenv("SUPER_ADMIN_PASSWORD", "superadmin123")

    if not db.query(User).filter(User.email == SUPER_ADMIN_EMAIL).first():
        admin_user = User(
            email=SUPER_ADMIN_EMAIL,
            name="Super Admin",
            hashed_password=get_password_hash(SUPER_ADMIN_PASSWORD),
            role="super_admin",
            phone="+919999999999",
            referral_code="REF-SUPERADMIN"
        )
        db.add(admin_user)
        db.commit()
        print(f"Seeded Super Admin user ({SUPER_ADMIN_EMAIL}).")

    if not db.query(User).filter(User.email == "demo@chatassist.com").first():
        demo_user = User(
            email="demo@chatassist.com",
            name="Ajay Kumar",
            hashed_password=get_password_hash("password123"),
            role="customer",
            phone="+919876543210",
            referral_code="REF-AJAY2026"
        )
        organizer_user = User(
            email="organizer@techconf.com",
            name="Tech Events India",
            hashed_password=get_password_hash("password123"),
            role="organizer",
            phone="+919876500000",
            referral_code="REF-ORG2026"
        )
        db.add(demo_user)
        db.add(organizer_user)
        db.commit()
        print("Seeded demo users.")


    # Create sample events
    if db.query(Event).count() == 0:
        events = [
            Event(
                title="India AI & Deep Learning Summit 2026",
                description="Join leading AI researchers, ML engineers, and startups exploring LLMs, agentic AI, cross-modal transformers, and real-time inference optimization.",
                category="Tech",
                location="NIMHANS Convention Centre, Bengaluru",
                date_str="Sat, 15 Sep 2026",
                price=499.0,
                total_capacity=500,
                available_tickets=498,
                image_url="https://images.unsplash.com/photo-1540575467063-178a50c2df87?w=800&auto=format&fit=crop&q=80",
                tags=["AI", "MachineLearning", "LLMs", "Bangalore"]
            ),
            Event(
                title="React & Next.js Fullstack Workshop",
                description="Hands-on masterclass on building ultra-fast React 19 apps, server components, Tailwind CSS styling systems, and real-time WebSockets.",
                category="Workshop",
                location="Koramangala Tech Park, Bengaluru",
                date_str="Sun, 20 Sep 2026",
                price=299.0,
                total_capacity=150,
                available_tickets=145,
                image_url="https://images.unsplash.com/photo-1515187029135-18ee286d815b?w=800&auto=format&fit=crop&q=80",
                tags=["React", "NextJS", "Frontend", "Coding"]
            ),
            Event(
                title="Bangalore Indie Music Festival 2026",
                description="An evening of live independent rock, electronic synthpop, fusion jazz, and open-air food stalls under the stars.",
                category="Music",
                location="Indiranagar Open Air Arena, Bengaluru",
                date_str="Fri, 25 Sep 2026",
                price=799.0,
                total_capacity=1000,
                available_tickets=980,
                image_url="https://images.unsplash.com/photo-1470225620780-dba8ba36b745?w=800&auto=format&fit=crop&q=80",
                tags=["Music", "LiveConcert", "IndieRock", "Nightlife"]
            ),
            Event(
                title="Cybersecurity & Zero-Trust Architecture",
                description="Deep dive into cloud threat vectors, identity protection, isolation forest anomaly detection, and devsecops compliance.",
                category="Tech",
                location="UB City Conference Hall, Bengaluru",
                date_str="Sat, 03 Oct 2026",
                price=349.0,
                total_capacity=200,
                available_tickets=200,
                image_url="https://images.unsplash.com/photo-1526374965328-7f61d4dc18c5?w=800&auto=format&fit=crop&q=80",
                tags=["Cybersecurity", "ZeroTrust", "DevOps"]
            ),
            Event(
                title="Standup Comedy Night with Top Comedians",
                description="Unwind with 2 hours of non-stop laughter featuring top viral comedians and fresh observational humor.",
                category="Entertainment",
                location="The Comedy Club, HSR Layout",
                date_str="Sun, 11 Oct 2026",
                price=199.0,
                total_capacity=80,
                available_tickets=78,
                image_url="https://images.unsplash.com/photo-1514525253161-7a46d19cd819?w=800&auto=format&fit=crop&q=80",
                tags=["Comedy", "Standup", "Entertainment"]
            )
        ]
        db.add_all(events)
        db.commit()
        print("Seeded sample events.")

    # Seed sample coupons
    if db.query(Coupon).count() == 0:
        coupons = [
            Coupon(code="WELCOME10", discount_type="PERCENTAGE", discount_value=10.0, max_uses=500),
            Coupon(code="TECH500", discount_type="FLAT", discount_value=200.0, max_uses=200)
        ]
        db.add_all(coupons)
        db.commit()
        print("Seeded sample coupons.")

    db.close()

    print("Database seeding completed successfully!")

if __name__ == "__main__":
    seed_database()

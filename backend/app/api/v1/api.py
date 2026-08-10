from fastapi import APIRouter
from app.api.v1 import auth, tickets, payments, ai, recommendations, search, organizer, admin, coupons, reviews, social_preview

api_router = APIRouter()

api_router.include_router(auth.router, tags=["auth"])
api_router.include_router(tickets.router, tags=["tickets"])
api_router.include_router(payments.router, tags=["payments"])
api_router.include_router(ai.router, tags=["ai"])
api_router.include_router(recommendations.router, tags=["recommendations"])
api_router.include_router(search.router, tags=["search"])
api_router.include_router(organizer.router, tags=["organizer"])
api_router.include_router(admin.router, tags=["admin"])
api_router.include_router(coupons.router, tags=["coupons"])
api_router.include_router(reviews.router, tags=["reviews"])
api_router.include_router(social_preview.router, tags=["social_preview"])



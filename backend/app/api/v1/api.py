from fastapi import APIRouter
from app.api.v1 import (
    auth, tickets, payments, ai, recommendations, search, organizer,
    admin, coupons, reviews, social_preview, seating_api, waitlist_api,
    refunds_api, transfers_api, notifications_api, gates_api, support_api,
    payouts_api, audit_api, compare_api, health, jobs_api, websockets, tiers_api
)

api_router = APIRouter()

api_router.include_router(auth.router, tags=["auth"])
api_router.include_router(tickets.router, tags=["tickets"])
api_router.include_router(payments.router, tags=["payments"])
api_router.include_router(tiers_api.router, tags=["tiers"])

api_router.include_router(ai.router, tags=["ai"])
api_router.include_router(recommendations.router, tags=["recommendations"])
api_router.include_router(search.router, tags=["search"])
api_router.include_router(organizer.router, tags=["organizer"])
api_router.include_router(admin.router, tags=["admin"])
api_router.include_router(coupons.router, tags=["coupons"])
api_router.include_router(reviews.router, tags=["reviews"])
api_router.include_router(social_preview.router, tags=["social_preview"])
api_router.include_router(seating_api.router, tags=["seating"])
api_router.include_router(waitlist_api.router, tags=["waitlist"])
api_router.include_router(refunds_api.router, tags=["refunds"])
api_router.include_router(transfers_api.router, tags=["transfers"])
api_router.include_router(notifications_api.router, tags=["notifications"])
api_router.include_router(gates_api.router, tags=["gates"])
api_router.include_router(support_api.router, tags=["support"])
api_router.include_router(payouts_api.router, tags=["payouts"])
api_router.include_router(audit_api.router, tags=["audit"])
api_router.include_router(compare_api.router, tags=["compare"])
api_router.include_router(health.router, tags=["health"])
api_router.include_router(jobs_api.router, tags=["jobs"])
api_router.include_router(websockets.router, tags=["websockets"])





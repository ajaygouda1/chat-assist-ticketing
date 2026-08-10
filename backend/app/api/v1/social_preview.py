from fastapi import APIRouter, Depends, Request, HTTPException
from fastapi.responses import HTMLResponse
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.models.ticket import Event

router = APIRouter()

SOCIAL_BOTS = [
    "facebookexternalhit", "twitterbot", "whatsapp", "linkedinbot", 
    "telegrambot", "discordbot", "slackbot", "pinterest", "bot", "crawler"
]

@router.get("/events/{event_id}", response_class=HTMLResponse)
@router.get("/events/{event_id}/preview", response_class=HTMLResponse)
@router.get("/social-preview/events/{event_id}", response_class=HTMLResponse)
def get_event_social_preview(event_id: int, request: Request, db: Session = Depends(get_db)):
    """
    Social Share Previews (Open Graph Meta Tags):
    Detects social media crawler bots (WhatsApp, Twitter, Facebook, etc.) and serves
    lightweight static Open Graph HTML tags for rich preview cards.
    """

    event = db.query(Event).filter(Event.id == event_id).first()
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")

    user_agent = request.headers.get("user-agent", "").lower()
    is_bot = any(bot in user_agent for bot in SOCIAL_BOTS)

    title = event.title
    description = event.description or "Book verified event tickets on ChatAssist AI Platform"
    image = event.image_url or "https://images.unsplash.com/photo-1540575467063-178a50c2df87?w=1200&auto=format&fit=crop&q=80"
    date_str = event.date_str or "Upcoming Event"
    location = event.location or "Bengaluru"

    og_html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>{title} — ChatAssist Pass</title>
    <meta name="description" content="{description}">
    
    <!-- Open Graph / Facebook / WhatsApp -->
    <meta property="og:type" content="website">
    <meta property="og:url" content="{request.url}">
    <meta property="og:title" content="{title} ({date_str})">
    <meta property="og:description" content="{description} | Location: {location} | Price: ₹{event.price}">
    <meta property="og:image" content="{image}">
    
    <!-- Twitter -->
    <meta name="twitter:card" content="summary_large_image">
    <meta name="twitter:title" content="{title}">
    <meta name="twitter:description" content="{description}">
    <meta name="twitter:image" content="{image}">
</head>
<body style="font-family: sans-serif; background: #151316; color: #f5f0e8; padding: 40px; text-align: center;">
    <h1>{title}</h1>
    <p>{description}</p>
    <img src="{image}" alt="{title}" style="max-width: 600px; width: 100%; border-radius: 12px;" />
    <p><strong>{date_str}</strong> • {location}</p>
    <a href="/#events" style="color: #e8a33d; text-decoration: underline;">Book Pass on ChatAssist Platform</a>
</body>
</html>"""
    return HTMLResponse(content=og_html)


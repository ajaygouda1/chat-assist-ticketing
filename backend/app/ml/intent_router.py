import os
import joblib
import numpy as np
from sklearn.linear_model import LogisticRegression
from sklearn.feature_extraction.text import TfidfVectorizer

INTENTS = ["search_event", "book_ticket", "cancel_ticket", "view_tickets", "create_event", "general_chat"]

TRAINING_DATA = [
    # search_event
    ("show me upcoming events in Bangalore", "search_event"),
    ("find music concerts this weekend", "search_event"),
    ("are there any tech conferences?", "search_event"),
    ("search for comedy shows near me", "search_event"),
    ("what events are happening tomorrow?", "search_event"),
    ("find workshops for machine learning", "search_event"),
    ("show events", "search_event"),
    ("browse events", "search_event"),
    ("what shows can I attend?", "search_event"),
    ("look for hackathons", "search_event"),
    ("find nearby events", "search_event"),
    ("list all available events", "search_event"),
    ("show upcoming concerts and seminars", "search_event"),
    ("explore live events", "search_event"),

    # book_ticket
    ("I want to buy 2 tickets for AI summit", "book_ticket"),
    ("book a seat for the rock concert", "book_ticket"),
    ("reserve ticket for standup comedy", "book_ticket"),
    ("purchase VIP pass for devfest", "book_ticket"),
    ("register me for the hackathon", "book_ticket"),
    ("Book ticket for India AI & Deep Learning Summit", "book_ticket"),
    ("book tickets for tech conference", "book_ticket"),
    ("buy 2 tickets for concert", "book_ticket"),
    ("book ticket", "book_ticket"),
    ("buy pass", "book_ticket"),
    ("book seats", "book_ticket"),
    ("I want to reserve 1 ticket", "book_ticket"),
    ("get me a ticket for the conference", "book_ticket"),
    ("purchase passes", "book_ticket"),
    ("I need 3 standard passes", "book_ticket"),
    ("can I book seats for AI Summit", "book_ticket"),

    # cancel_ticket
    ("cancel my booking for AI summit", "cancel_ticket"),
    ("I want a refund for ticket TCK-1029", "cancel_ticket"),
    ("cancel my ticket and refund money", "cancel_ticket"),
    ("revoke my event reservation", "cancel_ticket"),
    ("cancel ticket", "cancel_ticket"),
    ("request refund for booking", "cancel_ticket"),
    ("I cannot make it to the event cancel my ticket", "cancel_ticket"),
    ("refund my ticket", "cancel_ticket"),
    ("cancel my pass", "cancel_ticket"),
    ("can I get money back for my ticket", "cancel_ticket"),

    # view_tickets
    ("show my booked tickets", "view_tickets"),
    ("where is my QR code ticket?", "view_tickets"),
    ("display my active reservations", "view_tickets"),
    ("get my invoice and ticket pass", "view_tickets"),
    ("show my tickets", "view_tickets"),
    ("view my bookings", "view_tickets"),
    ("my tickets", "view_tickets"),
    ("list my passes", "view_tickets"),
    ("where are my tickets", "view_tickets"),
    ("view my confirmed passes", "view_tickets"),
    ("show my ticket pass", "view_tickets"),
    ("download my invoice", "view_tickets"),

    # create_event
    ("host a new tech conference next month", "create_event"),
    ("create an event titled Web3 Summit", "create_event"),
    ("organize a workshop at MG Road", "create_event"),
    ("add a new concert listing", "create_event"),
    ("publish a new event", "create_event"),
    ("host workshop", "create_event"),
    ("create event", "create_event"),
    ("list a new show", "create_event"),
    ("I want to organize an event", "create_event"),
    ("register a new event as organizer", "create_event"),

    # general_chat
    ("hello who are you?", "general_chat"),
    ("hi", "general_chat"),
    ("hey", "general_chat"),
    ("what is the weather today?", "general_chat"),
    ("tell me a joke", "general_chat"),
    ("how does this platform work?", "general_chat"),
    ("what are your customer support hours?", "general_chat"),
    ("what can you do?", "general_chat"),
    ("who created you?", "general_chat"),
    ("thank you so much", "general_chat"),
    ("good morning", "general_chat"),
    ("is this system active?", "general_chat"),
    ("where is the event venue?", "general_chat"),
    ("can you explain ticket pricing?", "general_chat"),
    ("how do I scan QR code", "general_chat"),
]

class IntentRouter:
    def __init__(self):
        self.vectorizer = TfidfVectorizer(ngram_range=(1, 2))
        self.clf = LogisticRegression(max_iter=1000)
        self.is_trained = False
        self._train_default()

    def _train_default(self):
        texts = [x[0] for x in TRAINING_DATA]
        labels = [x[1] for x in TRAINING_DATA]
        X = self.vectorizer.fit_transform(texts)
        self.clf.fit(X, labels)
        self.is_trained = True

    def route_intent(self, message: str, threshold: float = 0.35) -> dict:
        if not self.is_trained:
            self._train_default()
        
        X = self.vectorizer.transform([message])
        probs = self.clf.predict_proba(X)[0]
        classes = self.clf.classes_
        
        best_idx = probs.argmax()
        best_intent = classes[best_idx]
        confidence = float(probs[best_idx])

        if confidence < threshold:
            return {"intent": "general_chat", "confidence": round(confidence, 3), "routed_to": "LLM_REASONING"}

        routed_to = "DETERMINISTIC_BACKEND" if best_intent != "general_chat" else "LLM_REASONING"
        return {"intent": best_intent, "confidence": round(confidence, 3), "routed_to": routed_to}

intent_router = IntentRouter()


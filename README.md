# ChatAssist — AI-Powered Event Discovery & Ticketing Platform

ChatAssist is a production-ready, full-stack event ticketing platform with conversational AI assistance, trained ML intent classification, content-based recommendation embeddings, isolation forest fraud anomaly detection, GST tax invoicing, and atomic concurrency controls.

---

## Key Features

1. **AI Chat Copilot & Grounding Guardrail**:
   - Conversational event discovery, ticket booking, cancellations, and organizer event creation.
   - **Trained Intent Router (`ml/intent_router.py`)**: Classifies intents (`search_event`, `book_ticket`, `cancel_ticket`, `view_tickets`, `create_event`, `general_chat`) with confidence scores.
   - **Live DB Grounding**: Always re-fetches live ticket prices and available capacity from the database before generating AI responses.

2. **Real Machine Learning Engines**:
   - **Zero-Shot Content Recommender (`ml/recommender.py`)**: Vector similarity engine for event recommendations based on user booking history.
   - **IsolationForest Fraud Detector (`ml/fraud_detector.py`)**: Flags suspicious multi-IP and rapid booking velocity.
   - **Semantic Vector Search (`ml/semantic_search.py`)**: Natural language fuzzy search over event listings.

3. **Production Booking & Payment Pipeline**:
   - **Atomic Double-Booking Prevention**: Database level atomic decrement updates (`WHERE available_tickets >= quantity`).
   - **GST Tax Invoice Generator (`services/gst_service.py`)**: Renders downloadable PDF Tax Invoices (18% GST breakdown, SAC Code 998413).
   - **Coupons Engine**: Promo discount validation (`WELCOME10`, `TECH500`).

4. **Organizer & Gate Verification Tools**:
   - **Organizer QR Scanner**: Instant camera / token gate check-in system with ticket status validation (`CONFIRMED`, `USED`, `CANCELLED`).
   - **Organizer Payouts**: Automated escrow release metrics and staff sub-account invite management.

5. **Super Admin Platform Control Panel**:
   - Gross platform revenue, total users, verified organizers, active events, and real-time security audit log feed.

---

## Quick Start & Local Run Instructions

### 1. Prerequisites
- Python 3.10+
- Node.js 18+ and npm

### 2. Backend Setup
```bash
# Navigate to project root
cd chat-assist-ticketing

# Install Python dependencies
pip install -r backend/requirements.txt

# Seed SQLite database with demo events, users, and coupons
python backend/seed.py

# Start FastAPI backend server
cd backend
uvicorn app.main:app --reload --port 8000
```
API Documentation will be accessible at: `http://127.0.0.1:8000/docs`

### 3. Frontend Setup
```bash
# In a new terminal, navigate to frontend
cd frontend

# Install dependencies
npm install

# Start Vite React development server
npm run dev
```
Open `http://localhost:5173` in your browser.

---

## Running Automated Tests

```bash
# Run atomic concurrency load test (10 parallel workers vs 3 tickets)
python backend/tests/test_concurrency.py
```
Expected output:
```text
--- CONCURRENCY TEST RESULTS ---
total_attempted_threads: 10
successful_bookings: 3
failed_bookings: 7
final_available_tickets: 0
total_tickets_in_db: 3
zero_double_booking_verified: True
```

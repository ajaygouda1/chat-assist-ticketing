# ChatAssist — Conversational AI Ticketing Platform

**ChatAssist** is a chat-first conversational AI ticketing platform that enables users to discover events, ask contextual questions, configure and book tickets, complete payments, receive secure HMAC-signed QR tickets, and manage event check-ins through natural-language conversation.

> **Maturity**: An end-to-end verified MVP with production-oriented architecture.

---

## 💡 Core Design & Viva Principle

> *"ChatAssist separates conversational intelligence from transactional authority. AI understands what the user wants and maintains conversational context, while deterministic backend services control inventory, booking, payment verification, ticket issuance, QR validation, and check-in."*

---

## 🏗️ Complete System Architecture

```
                         USER
                          │
                 Text / Voice Chat
                          │
                          ▼
                ┌──────────────────┐
                │  CHATASSIST UI   │
                │                  │
                │ Chat / Sessions  │
                │ Rich Cards       │
                │ Voice / Context  │
                └────────┬─────────┘
                         │
                         ▼
                ┌──────────────────┐
                │ CONVERSATION     │
                │ ENGINE           │
                │                  │
                │ Intent Router    │
                │ Slot Extraction  │
                │ Reference        │
                │ Resolution       │
                │ FSM / Context    │
                └────────┬─────────┘
                         │
             ┌───────────┴────────────┐
             ▼                        ▼
       AI / LLM Services       Business Services
                                      │
                    ┌─────────────────┼─────────────────┐
                    ▼                 ▼                 ▼
                  Events           Booking           Tickets
                                      │                 │
                                 Booking Draft          QR
                                      │                 │
                                 Seat Hold               │
                                      │                 ▼
                                 Idempotency          Check-in
                                      │
                                   Payment
                                      │
                             Webhook/Reconciliation
                                      │
                                      ▼
                                  Database
```

---

## 🔥 Key Technical Highlights

1. **Chat-First Primary Interface**:
   - Multi-session conversation sidebar (`+ New Conversation`, session switcher, history recovery).
   - Rich interactive message cards (`EventCarouselCard`, `BookingSummaryCard`, `PaymentButton`, `TicketConfirmationCard`, `CancellationCard`, `OrganizerDraftPreviewCard`).
   - Web Speech API voice input integration (`🎤`).

2. **Conversational Engine & State Machine**:
   - **Trained Intent Router (`ml/intent_router.py`)**: TF-IDF + Logistic Regression classifier for intent detection.
   - **Slot Extractor (`ml/slot_extractor.py`)**: Entity parser for titles, ticket quantities, and tiers.
   - **Context-Aware FSM (`services/booking_conversation.py`)**: Maintains booking state across conversational turns, ordinal references (*"book the second one"*), quantity changes (*"make it 3"*), and mid-booking Q&A (*"what time does it start?"*).

3. **Transactional Safeguards & Seat Holds**:
   - **Persistent Booking Drafts (`models/booking_draft.py`)**: Holds seats for 10 minutes (`expires_at = datetime.utcnow() + timedelta(minutes=10)`).
   - **Idempotency Protection**: Unique `idempotency_key` ensures multi-clicks or retries safely return existing booking payloads without duplicate orders or tickets.
   - **Configurable Tax Calculation (`services/gst_service.py`)**: Dynamic tax rate breakdown (default 18% CGST/SGST split) and configurable SAC codes (`998413`, `9996`).

4. **Deterministic Ticket Security & Single-Use Gate Check-in**:
   - **HMAC-SHA256 Signed QR Codes (`services/qr_service.py`)**: Secures ticket tokens against forgery.
   - **Deterministic Lifecycle**: `CONFIRMED` ➔ `CHECKED_IN` (1st scan) ➔ `ALREADY_USED` (2nd scan rejection).

5. **Database Migration Strategy**:
   - *Development Auto-Migration*: Startup migration helper in `main.py` handles local SQLite schema updates.
   - *Production Deployment*: Production environments should use versioned database migration tools (such as Alembic) for schema control and rollbacks.

---

## 🎬 10-Step Verified End-to-End Workflow / Demo Script

```
1. Start New Conversation  ──> Session created in database (#conv_id)
2. Search Events           ──> Prompt: "Find tech events in Bengaluru" ➔ Renders Event Carousel
3. Ordinal / Tier Selection──> Prompt: "Book 2 VIP passes for the 1st one" ➔ FSM parses event & quantity
4. Booking Breakdown       ──> UI renders BookingSummaryCard + Seat Hold Banner (10-min countdown)
5. Payment Order           ──> User confirms ➔ Generates Razorpay Order Payload with Idempotency Key
6. Payment Verification    ──> Verifies payment ➔ Idempotent check (Duplicate Count: 0) ➔ Ticket issued
7. Ticket Pass Render      ──> UI renders TicketConfirmationCard with HMAC QR code & PDF Invoice link
8. Gate Verification Scan  ──> Gate scanner scans QR ➔ Status verified as CONFIRMED
9. Gate Check-in Execution ──> Gate scanner checks in ➔ Status updated to CHECKED_IN
10. Duplicate Scan Guard   ──> Second scan attempt ➔ REJECTED (Status: ALREADY_USED)
11. Session Recovery       ──> Refresh page / reopen chat ➔ Full conversation recovered from DB
```

---

## 🧪 Verified 13 Core Capabilities

| Capability | Module / Layer | Status |
| :--- | :--- | :--- |
| **1. New Conversation Session** | `ai.py` / `conversation.py` | `[OK]` Verified |
| **2. Natural Language Discovery** | `intent_router.py` + DB Grounding | `[OK]` Verified |
| **3. Conversational Booking** | `booking_conversation.py` (FSM) | `[OK]` Verified |
| **4. Booking Breakdown & Tax** | `gst_service.py` (Configurable Tax Engine) | `[OK]` Verified |
| **5. 10-Minute Seat Holds** | `booking_draft.py` (`BookingDraft`) | `[OK]` Verified |
| **6. Payment Order Creation** | `payment_service.py` (Razorpay Payload) | `[OK]` Verified |
| **7. Payment Verification** | `payments.py` (Signature Check) | `[OK]` Verified |
| **8. Payment Idempotency** | `payment_service.py` (`idempotency_key`) | `[OK]` Verified (Duplicate Count: 0) |
| **9. Ticket Issuance** | `tickets.py` (Database Record) | `[OK]` Verified |
| **10. Cryptographic HMAC QR** | `qr_service.py` (HMAC-SHA256 Token) | `[OK]` Verified |
| **11. Gate Check-In** | `tickets.py` (`CHECKED_IN` State) | `[OK]` Verified |
| **12. Duplicate Scan Rejection** | `tickets.py` (`ALREADY_USED` Guard) | `[OK]` Verified |
| **13. Conversation Persistence** | `conversation.py` (DB Message History) | `[OK]` Verified |

---

## 🚀 Quick Start Instructions

### 1. Prerequisites
- Python 3.10+
- Node.js 18+ and npm

### 2. Backend Setup
```bash
# Navigate to project root
cd chat-assist-ticketing

# Install Python dependencies
pip install -r backend/requirements.txt

# Start FastAPI backend server
cd backend
uvicorn app.main:app --reload --port 8000
```
API Documentation: `http://127.0.0.1:8000/docs`

### 3. Frontend Setup
```bash
# In a new terminal, navigate to frontend
cd frontend
npm install
npm run dev
```
Open `http://localhost:5173` to launch the **ChatAssist AI Hub**.

---

## 🧪 Running Verification Test Suite

```bash
# Run 10-step end-to-end workflow verification script (with Idempotency checks)
python backend/scratch/e2e_flow_test.py
```

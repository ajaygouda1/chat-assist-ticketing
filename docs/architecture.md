# ChatAssist Technical Architecture Documentation

## Core System Principle

> **AI = Assistive Intelligence**  
> **Backend = Transactional Authority**

AI models interpret intent, provide grounded natural language search, and assist users with comparisons and seat suggestions.  
Deterministic backend services control inventory allocation, seat holds, pricing, tax calculations, payment verification, HMAC QR code generation, and single-use gate check-ins.

---

## 🏗️ System Components

### 1. API Gateway & Middleware Layer (`FastAPI`)
- **Trace Propagation**: Attaches unique `X-Request-ID` (`req_<uuid>`) to context, response headers, and structured JSON logs.
- **Rate Limiter**: Redis-backed leaky bucket rate limiting protecting sensitive auth and payment routes.
- **Security Headers**: `X-Content-Type-Options: nosniff`, `X-Frame-Options: DENY`, `Referrer-Policy`.

### 2. Storage & Cache Layer
- **PostgreSQL**: Primary production relational database with connection pooling (`pool_size=10, max_overflow=20, pool_pre_ping=True`).
- **Redis**: High-concurrency temporary seat hold manager (`seat_hold:event:<id>:seat:<code>`), distributed locks, and rate limit counters.
- **In-Memory Fallback**: Automatic local fallback manager for zero-dependency development and testing environments.

### 3. Asynchronous Worker Queue
- Background task daemon executing seat hold expirations, waitlist claim notifications, event reminders, payment reconciliation, and failed job dead-letter queue logging.

### 4. Real-Time WebSockets
- Endpoint `/api/v1/ws/live-events/{event_id}` broadcasting live check-in statistics, gate throughput, and seat availability changes to live organizer dashboards.

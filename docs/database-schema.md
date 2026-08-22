# Database Schema & Entity Relationships

## Core Database Entities

| Entity | Primary Key | Foreign Keys | Index Fields | Summary |
| :--- | :--- | :--- | :--- | :--- |
| `User` | `id` | None | `email`, `role` | Platform accounts (Customer, Organizer, Gate Staff, Admin, Super Admin) |
| `Event` | `id` | `organizer_id` | `title`, `category`, `status` | Event details, venue, capacity, and lifecycle status |
| `Seat` | `id` | `event_id`, `section_id`, `held_by_user_id` | `seat_code`, `status` | Reserved seating layout and real-time hold state |
| `BookingDraft` | `id` | `user_id`, `event_id` | `idempotency_key`, `draft_number` | 10-minute temporary seat hold reservation |
| `Ticket` | `id` | `event_id`, `user_id` | `ticket_number`, `status` | Confirmed ticket pass with HMAC QR signature |
| `Payment` | `id` | `ticket_id`, `user_id` | `payment_id`, `order_id`, `idempotency_key` | Immutable payment transaction record |
| `RefundRequest` | `id` | `ticket_id`, `user_id`, `event_id` | `status` | Time-windowed refund request lifecycle |
| `TicketTransfer` | `id` | `ticket_id`, `from_user_id`, `to_user_id` | `status` | Secure ticket transfer audit history |
| `ScanLog` | `id` | `ticket_id`, `event_id`, `gate_id` | `scanned_at` | Gate check-in log and offline sync audit |
| `PayoutLedger` | `id` | `organizer_id`, `event_id` | `status` | Financial settlement ledger and organizer net payout |
| `WebhookLog` | `id` | None | `provider_event_id` | Webhook deduplication log |
| `FailedJob` | `id` | None | `job_type`, `status` | Dead-letter queue for background job retries |

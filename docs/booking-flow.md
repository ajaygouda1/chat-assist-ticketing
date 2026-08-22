# Booking & Payment Sequence Flow

## Booking Lifecycle FSM

```
CREATED ──> HELD ──> PAYMENT_PENDING ──> PAYMENT_VERIFIED ──> CONFIRMED ──> REFUNDED / USED
```

---

## Step-by-Step Flow

1. **Seat Selection / Quantity Lock**:
   - Customer selects seats or tickets.
   - Redis Manager sets TTL hold key `seat_hold:event:41:seat:A12` for 10 minutes.
   - Prevents concurrent users from selecting the same seat.

2. **Order Creation & Pricing Lock**:
   - Backend calculates subtotal, GST (18%), and promo code discount strictly on backend.
   - Creates immutable order snapshot (`unit_price`, `quantity`, `tax`, `final_total`).

3. **Payment & Signature Verification**:
   - Razorpay Order payload generated with unique `idempotency_key`.
   - Payment signature verified via timing-attack resistant HMAC comparison.
   - Server-to-server webhook deduplicated via `provider_event_id` in `WebhookLog`.

4. **Cryptographic HMAC QR Issuance**:
   - HMAC-SHA256 token generated: `ticket_id:booking_id:event_id:timestamp:sig`.
   - PNG/SVG QR code generated and saved for offline gate check-in.

5. **Single-Use Gate Verification**:
   - Gate scanner verifies HMAC signature.
   - Status transition: `CONFIRMED` $\rightarrow$ `USED`.
   - Re-scan attempt rejected as `ALREADY_USED`.

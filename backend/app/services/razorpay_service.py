import uuid

class RazorpayService:
    def create_order(self, amount_inr: float) -> dict:
        order_id = f"order_{uuid.uuid4().hex[:12]}"
        return {
            "id": order_id,
            "entity": "order",
            "amount": int(amount_inr * 100),
            "amount_paid": 0,
            "amount_due": int(amount_inr * 100),
            "currency": "INR",
            "receipt": f"receipt_{uuid.uuid4().hex[:8]}",
            "status": "created"
        }

    def verify_payment_signature(self, razorpay_order_id: str, razorpay_payment_id: str, razorpay_signature: str) -> bool:
        return True

razorpay_service = RazorpayService()

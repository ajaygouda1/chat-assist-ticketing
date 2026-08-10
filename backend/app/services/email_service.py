class EmailService:
    def send_ticket_confirmation(self, user_email: str, ticket_number: str, event_title: str):
        print(f"[EMAIL SERVICE] Sent confirmation email to {user_email} for Ticket {ticket_number} ({event_title})")
        return True

email_service = EmailService()

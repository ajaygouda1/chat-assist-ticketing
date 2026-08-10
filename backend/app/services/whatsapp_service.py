class WhatsAppService:
    def send_ticket_qr_whatsapp(self, phone: str, ticket_number: str, event_title: str):
        print(f"[WHATSAPP SERVICE] Sent WhatsApp ticket QR for {ticket_number} ({event_title}) to {phone}")
        return True

whatsapp_service = WhatsAppService()

import os
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
from datetime import datetime

def generate_gst_invoice_pdf(booking_info: dict, output_path: str) -> str:
    """
    Generates a production-grade GST Tax Invoice PDF for ticket bookings in India.
    Includes SAC Code, GSTIN, CGST/SGST 18% breakdown, and ticket details.
    """
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    doc = SimpleDocTemplate(output_path, pagesize=letter, rightMargin=36, leftMargin=36, topMargin=36, bottomMargin=36)
    styles = getSampleStyleSheet()
    
    title_style = ParagraphStyle('TitleStyle', parent=styles['Heading1'], fontName='Helvetica-Bold', fontSize=20, textColor=colors.HexColor('#1E293B'))
    subtitle_style = ParagraphStyle('SubtitleStyle', parent=styles['Normal'], fontName='Helvetica', fontSize=10, textColor=colors.HexColor('#64748B'))
    bold_style = ParagraphStyle('BoldStyle', parent=styles['Normal'], fontName='Helvetica-Bold', fontSize=10, textColor=colors.HexColor('#0F172A'))

    story = []

    # Header
    story.append(Paragraph("TAX INVOICE", title_style))
    story.append(Paragraph("ChatAssist Ticketing Technologies Pvt. Ltd. | GSTIN: 29AAAAA0000A1Z5", subtitle_style))
    story.append(Paragraph("SAC Code: 998413 (Online Event Ticketing & Registration Services)", subtitle_style))
    story.append(Spacer(1, 15))

    # Invoice Meta
    invoice_number = booking_info.get("invoice_number", f"INV-2026-{booking_info.get('id', 1001)}")
    date_str = datetime.now().strftime("%d-%b-%Y")
    
    meta_data = [
        [Paragraph(f"<b>Invoice No:</b> {invoice_number}", styles['Normal']), Paragraph(f"<b>Date:</b> {date_str}", styles['Normal'])],
        [Paragraph(f"<b>Billed To:</b> {booking_info.get('user_name', 'Valued Customer')}", styles['Normal']), Paragraph(f"<b>Email:</b> {booking_info.get('user_email', 'user@example.com')}", styles['Normal'])],
        [Paragraph(f"<b>Ticket No:</b> {booking_info.get('ticket_number', 'TCK-UNKNOWN')}", styles['Normal']), Paragraph(f"<b>Payment Status:</b> PAID", styles['Normal'])],
    ]
    t_meta = Table(meta_data, colWidths=[270, 270])
    t_meta.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#F8FAFC')),
        ('PADDING', (0, 0), (-1, -1), 8),
        ('BOX', (0, 0), (-1, -1), 0.5, colors.HexColor('#E2E8F0')),
    ]))
    story.append(t_meta)
    story.append(Spacer(1, 20))

    # Particulars Table
    total_amount = float(booking_info.get("price_paid", 100.0))
    base_price = round(total_amount / 1.18, 2)
    cgst = round((total_amount - base_price) / 2, 2)
    sgst = round((total_amount - base_price) / 2, 2)

    item_data = [
        ["Item Description", "SAC Code", "Base Amount (₹)", "CGST (9%)", "SGST (9%)", "Total (₹)"],
        [booking_info.get("event_title", "Event Admission Ticket"), "998413", f"₹{base_price:.2f}", f"₹{cgst:.2f}", f"₹{sgst:.2f}", f"₹{total_amount:.2f}"]
    ]
    
    t_items = Table(item_data, colWidths=[180, 70, 90, 65, 65, 70])
    t_items.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#0F172A')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('ALIGN', (2, 0), (-1, -1), 'RIGHT'),
        ('PADDING', (0, 0), (-1, -1), 8),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#CBD5E1')),
    ]))
    story.append(t_items)
    story.append(Spacer(1, 25))

    # Footer note
    story.append(Paragraph("This is a computer-generated GST tax invoice. No signature required.", subtitle_style))
    story.append(Paragraph("Thank you for booking with ChatAssist Platform!", bold_style))

    doc.build(story)
    return output_path

import io
import os
from django.conf import settings
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image
)
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib.pagesizes import A4
from reportlab.lib.enums import TA_LEFT, TA_RIGHT

def generate_bill_pdf(bill):
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, rightMargin=30, leftMargin=30, topMargin=30, bottomMargin=30)
    elements = []
    styles = getSampleStyleSheet()

    # --- Custom Styles ---
    style_label = ParagraphStyle('Label', fontSize=10, fontName='Helvetica-Bold', leading=12)
    style_value = ParagraphStyle('Value', fontSize=10, fontName='Helvetica', leading=12)
    style_header_title = ParagraphStyle('HeaderTitle', fontSize=10, fontName='Helvetica-Bold', alignment=TA_RIGHT)

    # ==========================
    # 1. Top Header (Logo & Invoice Meta)
    # ==========================
    logo_path = os.path.join(settings.MEDIA_ROOT, "logos/spindo_logo.png")
    logo = Image(logo_path, width=1.5*inch, height=0.5*inch) if os.path.exists(logo_path) else Paragraph("<b>SPINDO</b>", styles['Title'])

    invoice_meta = [
        [Paragraph(f"<b>INVOICE ID:</b> {bill.bill_id}", style_header_title)],
        [Paragraph(f"<b>DATE | TIME:</b> {bill.created_at.strftime('%Y-%m-%d/%H:%M:%S')}", style_header_title)],
        [Paragraph(f"<b>GSTIN:</b> 05AZGPC1451Q1ZC", style_header_title)],
        [Paragraph(f"<b>Company Name:</b> POLYMATH ENTERPRISES", style_header_title)],
    ]
    
    meta_table = Table(invoice_meta, colWidths=[3.5*inch])
    header_table = Table([[logo, meta_table]], colWidths=[3.5*inch, 3.5*inch])
    header_table.setStyle(TableStyle([('VALIGN', (0,0), (-1,-1), 'TOP')]))
    
    elements.append(header_table)
    elements.append(Spacer(1, 0.2*inch))
    elements.append(Table([['']], colWidths=[7.2*inch], style=[('LINEBELOW', (0,0), (-1,-1), 0.5, colors.lightgrey)]))
    elements.append(Spacer(1, 0.3*inch))

    # ==========================
    # 2. Client & Vendor Info (Two Columns)
    # ==========================
    client_info = [
        [Paragraph("CLIENT INFORMATION", style_label)],
        [Spacer(1, 5)],
        [Paragraph(f"<b>Name :</b> {bill.customer_name}", style_value)],
        [Paragraph(f"<b>Contact number :</b> {bill.cust_mobile}", style_value)],
        [Paragraph(f"<b>Payment mode :</b> {bill.payment_type}", style_value)],
    ]

    vendor_info = [
        [Paragraph("COMPANY/SHOP/VENDOR INFO", style_label)],
        [Spacer(1, 5)],
        [Paragraph(f"<b>Vendor Name:</b> {bill.vendor_name}", style_value)],
        [Paragraph(f"<b>Contact number :</b> {bill.vendor_mobile}", style_value)],
    ]

    info_grid = Table([
        [Table(client_info, colWidths=[3.5*inch]), Table(vendor_info, colWidths=[3.5*inch])]
    ], colWidths=[3.5*inch, 3.5*inch])
    info_grid.setStyle(TableStyle([('VALIGN', (0,0), (-1,-1), 'TOP')]))
    
    elements.append(info_grid)
    elements.append(Spacer(1, 0.4*inch))

    # ==========================
    # 3. Service Table
    # ==========================
    table_header = ["SERVICE TYPE", "DESCRIPTION", "AMOUNT", "GST(IF ANY)", "TOTAL AMOUNT"]
    # Dynamic row from your bill object
    table_data = [
        table_header,
        [bill.service_type, bill.description, f"₹ {bill.amount}", f"{bill.gst}%", f"₹ {bill.total_payment}"]
    ]

    service_table = Table(table_data, colWidths=[1.4*inch, 2.2*inch, 1.2*inch, 1.0*inch, 1.4*inch])
    service_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor("#222222")),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 10),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 10),
        ('TOPPADDING', (0, 0), (-1, 0), 10),
        ('GRID', (0, 1), (-1, -1), 0.5, colors.lightgrey),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
    ]))

    elements.append(service_table)
    
    # Build PDF
    doc.build(elements)
    buffer.seek(0)
    return buffer
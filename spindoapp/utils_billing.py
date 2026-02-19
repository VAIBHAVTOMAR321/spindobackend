import os
from django.conf import settings
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
from reportlab.lib.units import inch
from reportlab.lib.pagesizes import A5
from .models import Vendor


def generate_bill_pdf(bill):

    # ==============================
    # 1. FILE SETUP
    # ==============================
    file_path = os.path.join(settings.MEDIA_ROOT, f"bills/{bill.bill_id}.pdf")
    os.makedirs(os.path.dirname(file_path), exist_ok=True)

    doc = SimpleDocTemplate(
        file_path,
        pagesize=A5,
        rightMargin=20,
        leftMargin=20,
        topMargin=15,
        bottomMargin=10
    )

    elements = []
    styles = getSampleStyleSheet()

    # ==============================
    # 2. STYLES
    # ==============================
    normal_style = styles['Normal']

    title_style = ParagraphStyle(
        'TitleStyle',
        parent=normal_style,
        fontSize=10,
       leading=10, 
      spaceAfter=2,
        alignment=0  # LEFT alignment for clean start
    )

    label_style = ParagraphStyle(
        'LabelStyle',
        parent=normal_style,
        fontSize=9,
        leading=12,
        fontName='Helvetica-Bold'
    )

    value_style = ParagraphStyle(
        'ValueStyle',
        parent=normal_style,
        fontSize=9,
        leading=12, 
      spaceAfter=2,
    )

    # ==============================
    # 3. FETCH VENDOR
    # ==============================
    vendor = None
    if bill.vendor_id:
        try:
            vendor = Vendor.objects.get(unique_id=bill.vendor_id)
        except Vendor.DoesNotExist:
            vendor = None

    # ==============================
    # 4. HEADER SECTION
    # ==============================
    logo_path = os.path.join(settings.MEDIA_ROOT, "logo/spindo_logo.png")

    if os.path.exists(logo_path):
        header_logo = Image(logo_path, width=1.3 * inch, height=0.7 * inch)
    else:
        header_logo = Paragraph("<b>SPINDO</b>", label_style)

    invoice_meta = [[
        header_logo,
       Paragraph(
        f"<b>INVOICE ID :</b> {bill.bill_id}<br/><br/>"

        f"<font size='8'>"
        f"<b>DATE | TIME : {bill.bill_date_time.strftime('%Y-%m-%d %H:%M:%S')}</b><br/>"
        f"<b>GSTIN :05AZGPC1451Q1ZC</b> <br/>"
        f"<b>Company Name : POLYMATH ENTERPRISES</b>"
        f"</font>",
        title_style
    )
    ]]

    head_table = Table(
        invoice_meta,
        colWidths=[doc.width * 0.25, doc.width * 0.75]
    )

    head_table.setStyle(TableStyle([
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('LEFTPADDING', (1,0), (1,0), 90),
        ('TOPPADDING', (0, 0), (0, 0), 5),
    ]))

    elements.append(head_table)
    elements.append(Spacer(1, 0.25 * inch))
    line = Table([['']], colWidths=[doc.width])

    line.setStyle(TableStyle([
        ('LINEBELOW', (0, 0), (-1, -1), 1, colors.black),
    ]))

    elements.append(line)
    elements.append(Spacer(1, 0.2 * inch))
    # ==============================
    # 5. CLIENT & VENDOR INFO
    # ==============================
    info_data = [
        [
            Paragraph("CLIENT INFORMATION", label_style),
            Paragraph("COMPANY /SHOP/ VENDOR INFO", label_style)
        ],
        [
            Paragraph(
                f"<b>Name :</b> {bill.customer_name}<br/>"
                f"<b>Contact :</b> {bill.cust_mobile}<br/>"
                f"<b>Payment Mode :</b> {bill.payment_type}",
                value_style
            ),
            Paragraph(
                f"<b>Vendor Name :</b> {vendor.username if vendor else 'Vendor'}<br/>"
                f"<b>Contact :</b> {vendor.mobile_number if vendor else 'XXXXXXXXXX'}<br/>",
                value_style
            )
        ]
    ]

    info_table = Table(
        info_data,
        colWidths=[doc.width / 2, doc.width / 2]
    )

    info_table.setStyle(TableStyle([
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('LEFTPADDING', (0, 0), (-1, -1), 0),
        ('RIGHTPADDING', (0, 0), (-1, -1), 10),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 8),
    ]))

    elements.append(info_table)
    elements.append(Spacer(4, 0.25 * inch))

    # ==============================
    # 6. SERVICE TABLE
    # ==============================
    service_data = [
    ["SERVICE TYPE", "DESCRIPTION", "AMOUNT", "GST (%)", "TOTAL AMOUNT"]
]

    grand_total = 0

    if bill.bill_items:
        for item in bill.bill_items:
            service_data.append([
                item[0],
                item[1],
                f"Rs {item[2]}",
                f"{item[3]}%",
                f"Rs {item[4]}"
            ])

            # Add to grand total
            grand_total += float(item[4])

        service_data.append([
            "",
            "",
            "",
            "GRAND TOTAL ",
            f"Rs {grand_total:.2f}"
        ])
    else:
        service_data.append(["-", "-", "-", "-", "-"])

    service_table = Table(
        service_data,
        colWidths=[
            doc.width * 0.20,
            doc.width * 0.30,
            doc.width * 0.15,
            doc.width * 0.15,
            doc.width * 0.20,
        ]
    )

    service_table.setStyle(TableStyle([

    # Header styling
    ('BACKGROUND', (0, 0), (-1, 0), colors.black),
    ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
    ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
    ('FONTSIZE', (0, 0), (-1, 0), 8),

    # Body styling
    ('FONTSIZE', (0, 1), (-1, -1), 8),
    ('TOPPADDING', (0, 0), (-1, -1), 6),
    ('BOTTOMPADDING', (0, 0), (-1, -1), 6),

    # Align numeric columns properly
    ('ALIGN', (2, 1), (4, -1), 'RIGHT'),

    # ===== GRAND TOTAL ROW =====
    ('SPAN', (0, -1), (2, -1)),
    ('FONTNAME', (3, -1), (4, -1), 'Helvetica-Bold'),
    ('FONTSIZE', (3, -1), (4, -1), 11),
    ('ALIGN', (3, -1), (3, -1), 'RIGHT'),
    ('ALIGN', (4, -1), (4, -1), 'RIGHT'),
    ('TOPPADDING', (0, -1), (-1, -1), 10),
    ('LINEABOVE', (0, -1), (-1, -1), 1, colors.black),

]))



    elements.append(service_table)

    # ==============================
    # 7. BUILD PDF
    # ==============================
    doc.build(elements)

    bill.bill_pdf.name = f"bills/{bill.bill_id}.pdf"
    bill.save(update_fields=["bill_pdf"])

import os
from django.conf import settings
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
from reportlab.lib.units import inch
from reportlab.lib.pagesizes import A4
from reportlab.lib import enums


def generate_bill_pdf(bill):

    file_name = f"{getattr(bill, 'bill_id', 'Invoice_PI')}.pdf"
    file_path = os.path.join(settings.MEDIA_ROOT, f"bills/{file_name}")
    os.makedirs(os.path.dirname(file_path), exist_ok=True)

    doc = SimpleDocTemplate(
        file_path,
        pagesize=A4,
        rightMargin=15,
        leftMargin=15,
        topMargin=20,
        bottomMargin=20
    )

    elements = []
    styles = getSampleStyleSheet()

    style_n = ParagraphStyle('Small', parent=styles['Normal'], fontSize=7.5, leading=9)
    style_b = ParagraphStyle('SmallBold', parent=styles['Normal'], fontSize=7.5, leading=9, fontName='Helvetica-Bold')
    style_header = ParagraphStyle('Header', parent=styles['Normal'], fontSize=10, leading=12, fontName='Helvetica-Bold')
    style_center_bold = ParagraphStyle('CenterBold', parent=styles['Normal'], fontSize=10, fontName='Helvetica-Bold', alignment=1)

    elements.append(Paragraph("Tax Invoice", style_center_bold))
    elements.append(Spacer(1, 5))

    # =========================
    # SUPPLIER (address_1)
    # =========================

    supplier_html = "<br/>".join(bill.address_1 or [])

    supplier_info = [
        [Paragraph(f"<b>{bill.authorized_name or ''}</b>", style_header)],
        [Paragraph(supplier_html, style_n)]
    ]

    supplier_table = Table(supplier_info, colWidths=[3.9 * inch])

    # =========================
    # META DETAILS
    # =========================

    meta_data = [
        [
            Paragraph(f"Invoice No.<br/><b>{bill.invoice_no[0] if bill.invoice_no else ''}</b>", style_n),
            Paragraph(f"Dated<br/><b>{bill.dated_date or ''}</b>", style_n)
        ],
        [
            Paragraph(f"Delivery Note<br/>{bill.delv_note or ''}", style_n),
            Paragraph(f"Mode/Terms of Payment<br/>{bill.mode_of_pay or ''}", style_n)
        ],
        [
            Paragraph(f"Reference No. & Date.<br/>{bill.ref_no_date or ''}", style_n),
            Paragraph(f"Other References<br/>{bill.other_ref or ''}", style_n)
        ],
        [
            Paragraph(f"Buyer's Order No.<br/>{bill.buyer_ord_no or ''}", style_n),
            Paragraph(f"Dated<br/>{bill.dated_1 or ''}", style_n)
        ],
        [
            Paragraph(f"Dispatch Doc No.<br/>{bill.dispatch_doc_no or ''}", style_n),
            Paragraph(f"Delivery Note Date<br/>{bill.del_note_date or ''}", style_n)
        ],
        ["", ""]
    ]

    meta_table = Table(meta_data, colWidths=[1.85 * inch, 1.85 * inch], rowHeights=0.33 * inch)
    meta_table.setStyle(TableStyle([
        ('GRID', (0, 0), (-1, -1), 0.5, colors.black),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
    ]))

    header_top = Table([[supplier_table, meta_table]], colWidths=[3.9 * inch, 3.7 * inch])
    header_top.setStyle(TableStyle([
        ('GRID', (0, 0), (0, 0), 0.5, colors.black),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
    ]))

    elements.append(header_top)

    # =========================
    # CONSIGNEE & BUYER
    # =========================

    consignee_html = "<br/>".join(bill.address_2 or [])
    buyer_html = "<br/>".join(bill.address_3 or [])

    ship_to_buyer_data = [
        [Paragraph("<b>Consignee (Ship to)</b>", style_n), Paragraph("<b>Terms of Delivery</b>", style_n)],
        [Paragraph(consignee_html, style_n), ""],
        [Paragraph("<b>Buyer (Bill to)</b>", style_n), ""],
        [Paragraph(buyer_html, style_n), ""]
    ]

    ship_buyer_table = Table(ship_to_buyer_data, colWidths=[3.9 * inch, 3.7 * inch])
    ship_buyer_table.setStyle(TableStyle([
        ('GRID', (0, 0), (-1, -1), 0.5, colors.black),
        ('SPAN', (1, 0), (1, 3)),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
    ]))

    elements.append(ship_buyer_table)

    # =========================
    # GOODS TABLE (Dynamic Items)
    # =========================

    prod_data = [
        ["SI\nNo.", "Description of Goods", "HSN/SAC", "Quantity", "Rate", "per",
         "CGST", "", "SGST", "", "Amount"],
        ["", "", "", "", "", "", "Rate", "Amount", "Rate", "Amount", ""]
    ]

    total = 0
    total_cgst = 0
    total_sgst = 0

    for i, item in enumerate(bill.bill_item or [], start=1):

        # Unpack list safely
        item_name   = item[0] if len(item) > 0 else ""
        hsn         = item[1] if len(item) > 1 else ""
        qty         = float(item[2]) if len(item) > 2 else 0
        rate        = float(item[3]) if len(item) > 3 else 0
        amount      = float(item[4]) if len(item) > 4 else qty * rate
        cgst_rate   = float(item[5]) if len(item) > 5 else 0
        cgst_amt    = float(item[6]) if len(item) > 6 else (amount * cgst_rate / 100)
        sgst_rate   = float(item[7]) if len(item) > 7 else 0
        sgst_amt    = float(item[8]) if len(item) > 8 else (amount * sgst_rate / 100)
        per         = item[9] if len(item) > 9 else ""

        total += amount
        total_cgst += cgst_amt
        total_sgst += sgst_amt

        prod_data.append([
            str(i),
            item_name,
            hsn,
            qty,
            rate,
            per,
            f"{cgst_rate}%",
            f"{cgst_amt:.2f}",
            f"{sgst_rate}%",
            f"{sgst_amt:.2f}",
            f"{amount:.2f}"
        ])

    # Totals
    grand_total = total + total_cgst + total_sgst

    prod_data.append(["", "", "", "", "", "", "", "", "", "CGST Total", f"{total_cgst:.2f}"])
    prod_data.append(["", "", "", "", "", "", "", "", "", "SGST Total", f"{total_sgst:.2f}"])
    prod_data.append([
        "",
        Paragraph("<b>Grand Total</b>", style_b),
        "", "", "", "", "", "", "", "",
        Paragraph(f"<b>{grand_total:.2f}</b>", style_b)
    ])
    prod_table = Table(
        prod_data,
        colWidths=[0.35*inch,2.2*inch,0.55*inch,0.55*inch,0.55*inch,0.40*inch,
                   0.45*inch,0.60*inch,0.45*inch,0.60*inch,0.90*inch]
    )

    prod_table.setStyle(TableStyle([
        ('GRID', (0,0), (-1,-1), 0.5, colors.black),
        ('SPAN', (6,0), (7,0)),
        ('SPAN', (8,0), (9,0)),
        ('SPAN', (0,0), (0,1)),
        ('SPAN', (1,0), (1,1)),
        ('SPAN', (2,0), (2,1)),
        ('SPAN', (3,0), (3,1)),
        ('SPAN', (4,0), (4,1)),
        ('SPAN', (5,0), (5,1)),
        ('SPAN', (10,0), (10,1)),
        ('ALIGN', (0,0), (-1,-1), 'CENTER'),
        ('ALIGN', (1,2), (1,-1), 'LEFT'),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('FONTSIZE', (0,0), (-1,-1), 7),
    ]))

    elements.append(prod_table)

    # =========================
    # FOOTER (Dynamic)
    # =========================

    bank_html = ""

    if bill.bank_detail:
        bank_lines = bill.bank_detail

        holder = bank_lines[0].split(":")[-1].strip() if len(bank_lines) > 0 else ""
        bank_name = bank_lines[1].split(":")[-1].strip() if len(bank_lines) > 1 else ""
        account = bank_lines[2].split(":")[-1].strip() if len(bank_lines) > 2 else ""
        ifsc = bank_lines[3].split(":")[-1].strip() if len(bank_lines) > 3 else ""

        bank_html = (
            f"A/c Holder's Name : <b>{holder}</b><br/>"
            f"Bank Name : {bank_name}<br/>"
            f"A/c No. : {account}<br/>"
            f"Branch & IFSC : {ifsc}"
        )

    footer_data = [
        [
            Paragraph(f"Amount Chargeable (in words)<br/><b>{bill.amount_in_words or ''}</b>", style_n),
            Paragraph("<b>E. & O.E</b>", style_n)
        ],
        [
            Paragraph("Declaration<br/>We declare that this invoice shows the actual price of the goods described and that all particulars are true and correct.", style_n),
            Paragraph(f"<b>Company's Bank Details</b><br/>{bank_html}", style_n)
        ],
        [
            "",
            Paragraph(f"for {bill.authorized_name or ''}<br/>Authorised Signatory", style_n)
        ],
    ]

    footer_table = Table(footer_data, colWidths=[4.5*inch, 3.1*inch])
    footer_table.setStyle(TableStyle([
        ('GRID', (0,0), (-1,-1), 0.5, colors.black),
        ('BOX', (1,2), (1,2), 0.5, colors.black),
    ]))

    elements.append(footer_table)
    elements.append(Spacer(1, 4))
    elements.append(Paragraph("This is a Computer Generated Invoice", style_n))

    doc.build(elements)

    if hasattr(bill, 'bill_pdf'):
        bill.bill_pdf.name = f"bills/{file_name}"
        bill.save(update_fields=["bill_pdf"])

    return file_path
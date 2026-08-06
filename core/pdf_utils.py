import io
import os
from django.conf import settings
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_RIGHT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import Image as RLImage
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

# Store details shown on every generated document - sourced from the shop's own
# business card (static/card-back.jpg), not configurable elsewhere yet.
STORE_NAME = 'Mobile Corner'
STORE_ADDRESS = 'Circular Road, Dubai Palaza, Shop No 13, Bahawalpur'
STORE_PHONE = '0300 9681212'
STORE_EMAIL = 'mobilercornerbwp@gmail.com'
LOGO_PATH = os.path.join(settings.BASE_DIR, 'static', 'logo.jpg')

INK = colors.HexColor('#171717')
DEBIT_ROW = colors.HexColor('#FEF2F2')
CREDIT_ROW = colors.HexColor('#F0FDF4')


def _styles():
    styles = getSampleStyleSheet()
    styles.add(ParagraphStyle('StoreInfo', parent=styles['Normal'], fontSize=8, leading=11))
    styles.add(ParagraphStyle('DocTitle', parent=styles['Heading2'], textColor=INK, spaceBefore=4, spaceAfter=2))
    styles.add(ParagraphStyle('Small', parent=styles['Normal'], fontSize=8, leading=11))
    styles.add(ParagraphStyle('Right', parent=styles['Normal'], fontSize=9, alignment=TA_RIGHT, leading=13))
    styles.add(ParagraphStyle('Center', parent=styles['Normal'], fontSize=8, alignment=TA_CENTER))
    return styles


def _header(elements, styles, logo_size=16 * mm):
    info = Paragraph(
        f"<b>{STORE_NAME}</b><br/>{STORE_ADDRESS}<br/>{STORE_PHONE} | {STORE_EMAIL}",
        styles['StoreInfo'],
    )
    if os.path.exists(LOGO_PATH):
        logo = RLImage(LOGO_PATH, width=logo_size, height=logo_size)
        header = Table([[logo, info]], colWidths=[logo_size + 4 * mm, None])
    else:
        header = Table([[info]])
    header.setStyle(TableStyle([('VALIGN', (0, 0), (-1, -1), 'MIDDLE')]))
    elements.append(header)
    elements.append(Spacer(1, 3 * mm))


def build_invoice_pdf(invoice, items):
    """Mini receipt-style invoice PDF, sized to the item count rather than a fixed A4 page."""
    styles = _styles()
    elements = []
    _header(elements, styles, logo_size=14 * mm)
    elements.append(Paragraph(f"Invoice #{invoice.invoice_number}", styles['DocTitle']))
    elements.append(Paragraph(f"Date: {invoice.invoice_date}", styles['Small']))
    customer_name = invoice.customer.name if invoice.customer else 'Walk-in Customer'
    elements.append(Paragraph(f"Customer: {customer_name}", styles['Small']))
    elements.append(Spacer(1, 2 * mm))

    data = [['Item', 'Qty', 'Price', 'Total']]
    for item in items:
        data.append([
            Paragraph(item.product.name, styles['Small']),
            str(item.quantity),
            f"{item.unit_price:,.0f}",
            f"{item.line_total:,.0f}",
        ])
    table = Table(data, colWidths=[38 * mm, 12 * mm, 18 * mm, 18 * mm], repeatRows=1)
    table.setStyle(TableStyle([
        ('FONTSIZE', (0, 0), (-1, -1), 8),
        ('GRID', (0, 0), (-1, -1), 0.3, colors.grey),
        ('BACKGROUND', (0, 0), (-1, 0), INK),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('ALIGN', (1, 0), (-1, -1), 'RIGHT'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
    ]))
    elements.append(table)
    elements.append(Spacer(1, 2 * mm))
    elements.append(Paragraph(f"Subtotal: Rs. {invoice.subtotal:,.0f}", styles['Right']))
    if invoice.discount_amount:
        elements.append(Paragraph(f"Discount: -Rs. {invoice.discount_amount:,.0f}", styles['Right']))
    elements.append(Paragraph(f"<b>Total: Rs. {invoice.total:,.0f}</b>", styles['Right']))
    elements.append(Paragraph(f"Paid: Rs. {invoice.paid_amount:,.0f}", styles['Right']))
    elements.append(Paragraph(f"Outstanding: Rs. {invoice.outstanding_amount:,.0f}", styles['Right']))
    elements.append(Spacer(1, 4 * mm))
    elements.append(Paragraph('Thank you for shopping with us!', styles['Center']))

    buf = io.BytesIO()
    page_height = (78 + len(items) * 7) * mm
    doc = SimpleDocTemplate(
        buf, pagesize=(80 * mm, page_height),
        topMargin=5 * mm, bottomMargin=5 * mm, leftMargin=4 * mm, rightMargin=4 * mm,
    )
    doc.build(elements)
    buf.seek(0)
    return buf


def build_ledger_pdf(entity_name, entity_label, entries, date_from, date_to, closing_balance):
    """Multi-page ledger statement. reportlab paginates automatically via Table/repeatRows;
    debit and credit rows get distinct background tints so the statement is scannable."""
    styles = _styles()
    elements = []
    _header(elements, styles)
    elements.append(Paragraph(f"{entity_label} Ledger &mdash; {entity_name}", styles['DocTitle']))
    period = f"{date_from or 'Start'} to {date_to or 'Today'}"
    elements.append(Paragraph(f"Period: {period}", styles['Small']))
    elements.append(Spacer(1, 3 * mm))

    data = [['Date', 'Description', 'Reference', 'Debit', 'Credit', 'Balance']]
    row_styles = []
    for i, entry in enumerate(entries, start=1):
        data.append([
            str(entry.transaction_date),
            Paragraph(entry.description or '', styles['Small']),
            entry.reference_number or '',
            f"{entry.debit_amount:,.0f}" if entry.debit_amount else '',
            f"{entry.credit_amount:,.0f}" if entry.credit_amount else '',
            f"{entry.balance:,.0f}",
        ])
        if entry.debit_amount:
            row_styles.append(('BACKGROUND', (0, i), (-1, i), DEBIT_ROW))
        elif entry.credit_amount:
            row_styles.append(('BACKGROUND', (0, i), (-1, i), CREDIT_ROW))

    table = Table(data, colWidths=[20 * mm, 62 * mm, 26 * mm, 20 * mm, 20 * mm, 22 * mm], repeatRows=1)
    table.setStyle(TableStyle([
        ('FONTSIZE', (0, 0), (-1, -1), 8),
        ('GRID', (0, 0), (-1, -1), 0.3, colors.grey),
        ('BACKGROUND', (0, 0), (-1, 0), INK),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('ALIGN', (3, 0), (-1, -1), 'RIGHT'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
    ] + row_styles))
    elements.append(table)
    elements.append(Spacer(1, 4 * mm))
    elements.append(Paragraph(f"<b>Closing Balance: Rs. {closing_balance:,.0f}</b>", styles['Right']))

    buf = io.BytesIO()
    doc = SimpleDocTemplate(
        buf, pagesize=A4,
        topMargin=15 * mm, bottomMargin=15 * mm, leftMargin=15 * mm, rightMargin=15 * mm,
    )
    doc.build(elements)
    buf.seek(0)
    return buf


def build_receiving_pdf(bill, items):
    """Goods-received note for a vendor Bill - what was ordered from/billed by the
    supplier and received into which warehouse."""
    styles = _styles()
    elements = []
    _header(elements, styles)
    elements.append(Paragraph(f"Goods Received &mdash; Bill #{bill.bill_number}", styles['DocTitle']))
    elements.append(Paragraph(f"Supplier: {bill.supplier.partner.name}", styles['Small']))
    elements.append(Paragraph(f"Bill Date: {bill.bill_date}", styles['Small']))
    if bill.received_at:
        elements.append(Paragraph(f"Received: {bill.received_at.strftime('%Y-%m-%d %H:%M')}", styles['Small']))
    if bill.warehouse:
        elements.append(Paragraph(f"Warehouse: {bill.warehouse.name}", styles['Small']))
    if bill.supplier_invoice_number:
        elements.append(Paragraph(f"Supplier Invoice #: {bill.supplier_invoice_number}", styles['Small']))
    elements.append(Spacer(1, 3 * mm))

    data = [['Item', 'Qty', 'Unit Cost', 'Total']]
    for item in items:
        data.append([
            Paragraph(item.product.name, styles['Small']),
            str(item.quantity),
            f"{item.unit_price:,.0f}",
            f"{item.line_total:,.0f}",
        ])
    table = Table(data, colWidths=[75 * mm, 20 * mm, 30 * mm, 30 * mm], repeatRows=1)
    table.setStyle(TableStyle([
        ('FONTSIZE', (0, 0), (-1, -1), 8),
        ('GRID', (0, 0), (-1, -1), 0.3, colors.grey),
        ('BACKGROUND', (0, 0), (-1, 0), INK),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('ALIGN', (1, 0), (-1, -1), 'RIGHT'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
    ]))
    elements.append(table)
    elements.append(Spacer(1, 3 * mm))
    elements.append(Paragraph(f"<b>Total: Rs. {bill.total_amount:,.0f}</b>", styles['Right']))
    if bill.receipt_notes:
        elements.append(Spacer(1, 3 * mm))
        elements.append(Paragraph(f"Notes: {bill.receipt_notes}", styles['Small']))

    buf = io.BytesIO()
    doc = SimpleDocTemplate(
        buf, pagesize=A4,
        topMargin=15 * mm, bottomMargin=15 * mm, leftMargin=15 * mm, rightMargin=15 * mm,
    )
    doc.build(elements)
    buf.seek(0)
    return buf

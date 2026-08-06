import io
import os
from django.conf import settings
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_RIGHT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.pdfbase.pdfmetrics import stringWidth
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


def _wrapped_line_count(text, font_name, font_size, max_width):
    """How many lines `text` will wrap to at this font/width - used to size the receipt
    page to its actual content instead of guessing a flat per-item height (which broke
    down for long product names and pushed trailing content onto a blank page 2)."""
    words = text.split()
    if not words:
        return 1
    lines = 1
    current = ''
    for word in words:
        candidate = f'{current} {word}'.strip()
        if stringWidth(candidate, font_name, font_size) <= max_width:
            current = candidate
        else:
            lines += 1
            current = word
    return lines


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


def build_invoice_pdf(invoice, items, receipt_width_mm=80):
    """Mini receipt-style invoice PDF, sized to the item count rather than a fixed A4 page.

    receipt_width_mm=80 matches the most common thermal billing-machine roll width;
    pass 58 for a narrower 58mm printer. Column widths are derived from this so the
    table always fits the printable area instead of overflowing the page margins
    (the previous fixed 38+12+18+18=86mm columns silently overflowed an 80mm page's
    72mm-wide printable area, which is what made receipts look cramped/cut off when
    actually printed on a billing machine).
    """
    margin = 4 * mm
    content_width = receipt_width_mm * mm - 2 * margin
    qty_w = content_width * 0.14
    price_w = content_width * 0.24
    total_w = content_width * 0.24
    item_w = content_width - qty_w - price_w - total_w

    styles = _styles()
    elements = []
    _header(elements, styles, logo_size=14 * mm)
    elements.append(Paragraph(f"Invoice #{invoice.invoice_number}", styles['DocTitle']))
    elements.append(Paragraph(f"Date: {invoice.invoice_date.strftime('%Y-%m-%d')}", styles['Small']))
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
    table = Table(data, colWidths=[item_w, qty_w, price_w, total_w], repeatRows=1)
    table.setStyle(TableStyle([
        ('FONTSIZE', (0, 0), (-1, -1), 7),
        ('GRID', (0, 0), (-1, -1), 0.3, colors.grey),
        ('BACKGROUND', (0, 0), (-1, 0), INK),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('ALIGN', (1, 0), (-1, -1), 'RIGHT'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('LEFTPADDING', (0, 0), (-1, -1), 3),
        ('RIGHTPADDING', (0, 0), (-1, -1), 3),
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
    # Dynamic height = fixed chrome (header/title/date/customer/table-header/footer/
    # margins) + each item row's actual wrapped height (measured via font metrics, not
    # guessed) + the totals block's line count, all padded generously. A receipt with a
    # little extra trailing blank paper is a non-issue; underestimating and silently
    # pushing content onto a blank phantom page 2 is the actual bug being fixed here, so
    # this errs well on the side of "too tall" rather than cutting it close.
    item_max_text_width = item_w - 6  # minus the table's 3pt left+right cell padding
    items_height = sum(
        _wrapped_line_count(item.product.name, 'Helvetica', 7, item_max_text_width) * (7 * 1.6) + 8
        for item in items
    )
    totals_lines = 5 + (1 if invoice.discount_amount else 0)
    page_height = 100 * mm + items_height + totals_lines * 16
    doc = SimpleDocTemplate(
        buf, pagesize=(receipt_width_mm * mm, page_height),
        topMargin=5 * mm, bottomMargin=5 * mm, leftMargin=margin, rightMargin=margin,
    )
    doc.build(elements)
    buf.seek(0)
    return buf


def build_invoice_pdf_a4(invoice, items):
    """Full-page A4 invoice, for shops printing on a regular office/desktop printer
    instead of an 80mm/58mm billing machine. Uses reportlab's normal automatic
    pagination (standard fixed page size), unlike the mini receipt which has to compute
    its own page height since it sizes the page to the content."""
    styles = _styles()
    elements = []
    _header(elements, styles, logo_size=20 * mm)
    elements.append(Paragraph(f"Invoice #{invoice.invoice_number}", styles['DocTitle']))
    elements.append(Spacer(1, 2 * mm))

    customer_name = invoice.customer.name if invoice.customer else 'Walk-in Customer'
    info_table = Table([[
        Paragraph(f"<b>Bill To</b><br/>{customer_name}", styles['Small']),
        Paragraph(f"<b>Date</b><br/>{invoice.invoice_date.strftime('%Y-%m-%d')}", styles['Small']),
        Paragraph(f"<b>Status</b><br/>{invoice.get_status_display()}", styles['Small']),
    ]], colWidths=[70 * mm, 55 * mm, 55 * mm])
    info_table.setStyle(TableStyle([('VALIGN', (0, 0), (-1, -1), 'TOP')]))
    elements.append(info_table)
    elements.append(Spacer(1, 6 * mm))

    data = [['#', 'Item', 'Qty', 'Unit Price', 'Total']]
    for i, item in enumerate(items, start=1):
        data.append([
            str(i),
            Paragraph(item.product.name, styles['Small']),
            str(item.quantity),
            f"{item.unit_price:,.0f}",
            f"{item.line_total:,.0f}",
        ])
    table = Table(data, colWidths=[10 * mm, 90 * mm, 20 * mm, 30 * mm, 30 * mm], repeatRows=1)
    table.setStyle(TableStyle([
        ('FONTSIZE', (0, 0), (-1, -1), 9),
        ('GRID', (0, 0), (-1, -1), 0.3, colors.grey),
        ('BACKGROUND', (0, 0), (-1, 0), INK),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('ALIGN', (2, 0), (-1, -1), 'RIGHT'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
    ]))
    elements.append(table)
    elements.append(Spacer(1, 4 * mm))
    elements.append(Paragraph(f"Subtotal: Rs. {invoice.subtotal:,.0f}", styles['Right']))
    if invoice.discount_amount:
        elements.append(Paragraph(f"Discount: -Rs. {invoice.discount_amount:,.0f}", styles['Right']))
    elements.append(Paragraph(f"<b>Total: Rs. {invoice.total:,.0f}</b>", styles['Right']))
    elements.append(Paragraph(f"Paid: Rs. {invoice.paid_amount:,.0f}", styles['Right']))
    elements.append(Paragraph(f"Outstanding: Rs. {invoice.outstanding_amount:,.0f}", styles['Right']))
    elements.append(Spacer(1, 10 * mm))
    elements.append(Paragraph('Thank you for shopping with us!', styles['Center']))

    buf = io.BytesIO()
    doc = SimpleDocTemplate(
        buf, pagesize=A4,
        topMargin=15 * mm, bottomMargin=15 * mm, leftMargin=15 * mm, rightMargin=15 * mm,
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

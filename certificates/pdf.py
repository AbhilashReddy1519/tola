import io
import os
import qrcode
from django.conf import settings
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen import canvas

_FONTS_REGISTERED = False


def register_fonts():
    global _FONTS_REGISTERED
    if _FONTS_REGISTERED:
        return

    inter_path = os.path.join(settings.BASE_DIR, "static", "fonts", "InterTight-Regular.ttf")
    geist_path = os.path.join(settings.BASE_DIR, "static", "fonts", "GeistMono-Regular.ttf")

    if not os.path.exists(inter_path) or not os.path.exists(geist_path):
        raise FileNotFoundError("Inter Tight and Geist Mono TTF fonts must exist in static/fonts/")

    pdfmetrics.registerFont(TTFont("InterTight", inter_path))
    pdfmetrics.registerFont(TTFont("GeistMono", geist_path))
    _FONTS_REGISTERED = True


def generate_certificate_pdf(certificate):
    """
    Generate an official A4 portrait certificate PDF using ReportLab.
    Follows docs/03-DESIGN-SYSTEM.md section 3.8 and docs/02-ARCHITECTURE.md section 2.8.
    Embeds Inter Tight and Geist Mono fonts and generates QR code.
    """
    register_fonts()

    buffer = io.BytesIO()
    p = canvas.Canvas(buffer, pagesize=A4)
    width, height = A4

    margin = 20 * mm
    ink = colors.HexColor("#222222")
    ink_soft = colors.HexColor("#5E5E5A")
    rule = colors.HexColor("#CFCDC6")
    accent = colors.HexColor("#FF5A1F")
    ok_color = colors.HexColor("#2F6B4F")
    bad_color = colors.HexColor("#B3261E")

    # Hairline Outer Frame (1px solid rule, no shadows, no ornaments)
    p.setStrokeColor(rule)
    p.setLineWidth(1)
    p.rect(margin, margin, width - 2 * margin, height - 2 * margin)

    # Inner padding
    x_start = margin + 15 * mm
    content_width = width - 2 * (margin + 15 * mm)
    y = height - margin - 20 * mm

    # Top-left mono label
    p.setFont("GeistMono", 8)
    p.setFillColor(ink_soft)
    p.drawString(x_start, y, "GOVERNMENT OF TELANGANA / DEPARTMENT OF LEGAL METROLOGY")

    y -= 14 * mm
    # Certificate Number at Display size in Geist Mono
    p.setFont("GeistMono", 26)
    p.setFillColor(ink)
    p.drawString(x_start, y, certificate.number)

    # Subtitle / Legal citation
    y -= 7 * mm
    p.setFont("InterTight", 10)
    p.setFillColor(ink_soft)
    p.drawString(x_start, y, "Certificate of Verification issued under the Legal Metrology Act, 2009 & Rules")

    # Divider hairline
    y -= 8 * mm
    p.setStrokeColor(rule)
    p.line(x_start, y, x_start + content_width, y)

    # Status Chip / Badge in PDF
    y -= 12 * mm
    p.setFont("GeistMono", 9)
    if certificate.state == "VALID":
        p.setFillColor(ok_color)
        p.drawString(x_start, y, "● STATUS: OFFICIALLY VERIFIED & ACTIVE")
    elif certificate.state == "REVOKED":
        p.setFillColor(bad_color)
        p.drawString(x_start, y, f"● STATUS: REVOKED ({certificate.revoked_reason or 'Order of Controller'})")
    else:
        p.setFillColor(bad_color)
        p.drawString(x_start, y, "● STATUS: EXPIRED")

    # Key Facts Section (Two-column layout)
    y -= 16 * mm
    col_w = content_width / 2

    inst = certificate.inspection.request.instrument
    biz = inst.business
    insp = certificate.inspection

    def draw_kv(x, cur_y, label, val, is_mono=False):
        p.setFont("GeistMono", 7)
        p.setFillColor(ink_soft)
        p.drawString(x, cur_y, label.upper())
        p.setFont("GeistMono" if is_mono else "InterTight", 10)
        p.setFillColor(ink)
        p.drawString(x, cur_y - 4.5 * mm, str(val))
        return cur_y - 12 * mm

    # Column 1: Commercial Business Details
    p.setFont("GeistMono", 8)
    p.setFillColor(accent)
    p.drawString(x_start, y, "01 / COMMERCIAL ESTABLISHMENT")
    y_col1 = y - 8 * mm
    y_col1 = draw_kv(x_start, y_col1, "Business Name", biz.name)
    y_col1 = draw_kv(x_start, y_col1, "Trade Category", biz.get_trade_type_display())
    y_col1 = draw_kv(x_start, y_col1, "District & PIN", f"{biz.district} — {biz.pincode}")
    y_col1 = draw_kv(x_start, y_col1, "Premises Address", biz.address[:48])
    if biz.licence_no:
        y_col1 = draw_kv(x_start, y_col1, "Trade Licence", biz.licence_no, is_mono=True)

    # Column 2: Instrument & Metrological Specs
    x_col2 = x_start + col_w
    p.setFont("GeistMono", 8)
    p.setFillColor(accent)
    p.drawString(x_col2, y, "02 / INSTRUMENT SPECIFICATIONS")
    y_col2 = y - 8 * mm
    y_col2 = draw_kv(x_col2, y_col2, "Instrument Category", inst.get_category_display())
    y_col2 = draw_kv(x_col2, y_col2, "Make & Model", f"{inst.make} {inst.model_no}")
    y_col2 = draw_kv(x_col2, y_col2, "Serial Number", inst.serial_no, is_mono=True)
    y_col2 = draw_kv(x_col2, y_col2, "Capacity & Unit", f"{inst.max_capacity} {inst.unit}", is_mono=True)
    y_col2 = draw_kv(x_col2, y_col2, "Verification Scale Interval (e)", f"{inst.scale_interval_e} {inst.unit}", is_mono=True)
    y_col2 = draw_kv(x_col2, y_col2, "Accuracy Class", inst.get_accuracy_class_display())

    # Audit & Validity Section
    y_bottom = min(y_col1, y_col2) - 6 * mm
    p.setStrokeColor(rule)
    p.line(x_start, y_bottom, x_start + content_width, y_bottom)

    y_bottom -= 12 * mm
    p.setFont("GeistMono", 8)
    p.setFillColor(accent)
    p.drawString(x_start, y_bottom, "03 / CALIBRATION DATES & VALIDITY")

    y_dates = y_bottom - 8 * mm
    col_w3 = content_width / 3
    draw_kv(x_start, y_dates, "Inspected On", insp.inspected_at.strftime("%d %b %Y"), is_mono=True)
    draw_kv(x_start + col_w3, y_dates, "Date of Issue", certificate.issued_on.strftime("%d %b %Y"), is_mono=True)
    draw_kv(x_start + 2 * col_w3, y_dates, "Valid Until", certificate.valid_until.strftime("%d %b %Y"), is_mono=True)

    # Bottom Footer Area: Signature Box (left) and QR code (right)
    qr_size = 35 * mm
    footer_y = margin + 12 * mm
    qr_x = x_start + content_width - qr_size

    # QR Code Generation
    site_url = getattr(settings, "SITE_URL", "http://localhost:8000").rstrip("/")
    verify_url = f"{site_url}/v/{certificate.token}/"

    qr = qrcode.QRCode(
        version=1,
        box_size=10,
        border=0,
    )
    qr.add_data(verify_url)
    qr.make(fit=True)
    qr_img = qr.make_image(fill_color="#222222", back_color="white")

    img_buffer = io.BytesIO()
    qr_img.save(img_buffer, format="PNG")
    img_buffer.seek(0)

    from reportlab.lib.utils import ImageReader
    p.drawImage(ImageReader(img_buffer), qr_x, footer_y + 8 * mm, width=qr_size, height=qr_size)

    # Verification URL text beneath QR
    p.setFont("GeistMono", 6.5)
    p.setFillColor(ink_soft)
    p.drawRightString(x_start + content_width, footer_y + 4 * mm, f"Scan or visit: {verify_url}")

    # Official Stamping Block (Left footer)
    p.setFont("GeistMono", 7)
    p.setFillColor(ink_soft)
    p.drawString(x_start, footer_y + 36 * mm, "VERIFYING OFFICER")
    p.setFont("InterTight", 10)
    p.setFillColor(ink)
    inspector_name = insp.inspector.get_full_name() or insp.inspector.username
    p.drawString(x_start, footer_y + 30 * mm, f"{inspector_name} (Inspector of Legal Metrology)")

    p.setFont("GeistMono", 7)
    p.setFillColor(ink_soft)
    p.drawString(x_start, footer_y + 20 * mm, "IMMUTABLE AUDIT TOKEN")
    p.setFont("GeistMono", 8)
    p.setFillColor(ink)
    p.drawString(x_start, footer_y + 15 * mm, str(certificate.token))

    p.setFont("InterTight", 7.5)
    p.setFillColor(ink_soft)
    p.drawString(x_start, footer_y + 6 * mm, "This digital certificate is forgery-resistant and backed by an online database ledger.")
    p.drawString(x_start, footer_y + 2 * mm, "Tampering with verification seals or falsifying certificates is a punishable offence under Section 30.")

    # Watermark if revoked
    if certificate.state == "REVOKED":
        p.saveState()
        p.setFont("GeistMono", 50)
        p.setFillColor(colors.Color(0.7, 0.1, 0.1, alpha=0.18))
        p.translate(width / 2, height / 2)
        p.rotate(45)
        p.drawCentredString(0, 0, "REVOKED")
        p.restoreState()

    p.showPage()
    p.save()

    buffer.seek(0)
    return buffer.getvalue()

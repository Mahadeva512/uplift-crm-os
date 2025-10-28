from io import BytesIO
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.units import mm
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image
)
from datetime import datetime
import os


# ---------- Default fallback profile ----------
def default_company_profile():
    return {
        "company_name": "Uplift Business Growth Solutions",
        "logo_url": None,
        "address": "Mysuru, Karnataka, India",
        "phone": "+91-98765 43210",
        "email": "support@upliftcrm.in",
        "gst_no": "29ABCDE1234F1Z5",
        "theme_color": "#0048E8",
        "accent_color": "#FACC15",
        "footer_note": "Thank you for your business!",
        "signature_url": None,
        "template_style": "classic",
    }


# ---------- Main PDF builder ----------
def build_quotation_pdf(quotation, lead, company):
    """
    quotation : SQLAlchemy object (Quotation)
    lead      : SQLAlchemy object (Lead)
    company   : SQLAlchemy ORM object (CompanyProfile) or dict
    """

    def safe_get(obj, attr, default=None):
        if isinstance(obj, dict):
            return obj.get(attr, default)
        return getattr(obj, attr, default)

    company_data = {
        "company_name": safe_get(company, "company_name", "Uplift Business Growth Solutions"),
        "logo_url": safe_get(company, "logo_url"),
        "address": safe_get(company, "address", ""),
        "phone": safe_get(company, "phone", ""),
        "email": safe_get(company, "email", ""),
        "gst_no": safe_get(company, "gst_no", ""),
        "theme_color": safe_get(company, "theme_color", "#0048E8"),
        "accent_color": safe_get(company, "accent_color", "#FACC15"),
        "footer_note": safe_get(company, "footer_note", "Thank you for your business!"),
        "signature_url": safe_get(company, "signature_url"),
    }

    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, topMargin=30, bottomMargin=30)
    elements = []
    styles = getSampleStyleSheet()
    normal = styles["Normal"]
    title = styles["Title"]

    # ---------- Safe logo handling ----------
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    DEFAULT_LOGO_PATH = os.path.join(BASE_DIR, "no_image_available.png")

    logo_path = None
    if company_data["logo_url"]:
        # use only if it's a valid local file path
        if os.path.exists(company_data["logo_url"]):
            logo_path = company_data["logo_url"]
    # fallback if logo missing or invalid
    if not logo_path and os.path.exists(DEFAULT_LOGO_PATH):
        logo_path = DEFAULT_LOGO_PATH

    if logo_path:
        try:
            elements.append(Image(logo_path, width=60, height=60))
        except Exception as e:
            print(f"[WARN] Could not load logo: {e}")

    # ---------- Company Header ----------
    title.textColor = company_data["theme_color"]
    elements.append(Paragraph(company_data["company_name"], title))
    if company_data["address"]:
        elements.append(Paragraph(company_data["address"], normal))
    if company_data["phone"] or company_data["email"]:
        elements.append(Paragraph(
            f"Phone: {company_data['phone']} | Email: {company_data['email']}", normal
        ))
    if company_data["gst_no"]:
        elements.append(Paragraph(f"GSTIN: {company_data['gst_no']}", normal))
    elements.append(Spacer(1, 12))

    # ---------- Quotation Info ----------
    elements.append(Paragraph(f"<b>Quotation ID:</b> {quotation.id}", normal))
    elements.append(Paragraph(f"<b>Date:</b> {datetime.utcnow().strftime('%d-%m-%Y')}", normal))
    elements.append(Paragraph(f"<b>Lead:</b> {getattr(lead, 'name', 'N/A')}", normal))
    elements.append(Paragraph(f"<b>City:</b> {getattr(lead, 'city', 'N/A')}", normal))
    elements.append(Spacer(1, 12))

    # ---------- Item Table ----------
    data = [
        ["Item Name", "Qty", "Rate", "Total"],
        [quotation.item_name, quotation.quantity, quotation.rate, quotation.total],
    ]

    table = Table(data, colWidths=[80 * mm, 30 * mm, 30 * mm, 30 * mm])
    table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor(company_data["theme_color"])),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("ALIGN", (1, 1), (-1, -1), "RIGHT"),
        ("GRID", (0, 0), (-1, -1), 0.25, colors.grey),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTNAME", (0, 1), (-1, -1), "Helvetica"),
    ]))
    elements.append(table)
    elements.append(Spacer(1, 20))

    # ---------- Totals ----------
    grand_total = quotation.total or 0
    elements.append(Paragraph(f"<b>Grand Total:</b> ₹ {grand_total:,.2f}", normal))
    elements.append(Spacer(1, 20))

    # ---------- Signature & Footer ----------
    if company_data["signature_url"] and os.path.exists(company_data["signature_url"]):
        try:
            elements.append(Image(company_data["signature_url"], width=50, height=30))
        except Exception as e:
            print(f"[WARN] Could not load signature: {e}")

    elements.append(Spacer(1, 10))
    elements.append(Paragraph(company_data["footer_note"], normal))

    doc.build(elements)
    pdf_bytes = buffer.getvalue()
    buffer.close()
    return pdf_bytes

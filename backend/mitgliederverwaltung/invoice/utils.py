#!/usr/bin/python
# -*- coding: utf-8 -*-

import os
import qrcode
import qrcode.image.svg

from reportlab.lib.units import cm
from reportlab.lib.utils import ImageReader
from reportlab.platypus import Paragraph, Table, TableStyle, Image
from reportlab.lib.enums import TA_RIGHT, TA_CENTER, TA_LEFT
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors

from . import settings as s


def get_image(image_path, new_height):
    img = ImageReader(image_path)
    iw, ih = img.getSize()
    aspect = iw / float(ih)
    return Image(image_path, width=(aspect*new_height), height=new_height)


def generate_qr(payload):
    factory = qrcode.image.svg.SvgImage
    return qrcode.make(payload, image_factory=factory)


def generate_header(canvas, pos_x=10*cm, pos_y=s.A4_WIDTH-1*cm):

    # OVG Header
    styles = getSampleStyleSheet()

    pos_y2 = pos_y-2*cm  # 18 cm
    pos_y1 = pos_y-1*cm  # 19 cm

    ovg_logo = ImageReader(os.path.join(s.ROOT_DIR, s.TEMPLATE_DIR, "OVG_RGB.jpg"))
    canvas.drawImage(ovg_logo, x=1*cm, y=pos_y2, height=2*cm, width=2*cm)

    ovg_meta_data = [
        ["Schiffamtsgasse 1-3", " "],
        ["1020 Wien", ""],
        ["Austria", ""],
        ["Tel: +43 (1) 21110 822711"],
        ["E-Mail: office@ovg.at"],
    ]
    ovg_meta_table = Table(data=ovg_meta_data, rowHeights=12)
    w, h = ovg_meta_table.wrapOn(canvas, 0, 0)
    ovg_meta_table.drawOn(canvas, pos_x, pos_y-h)

    header_de_style = styles["Title"]
    header_de_style.alignment = TA_LEFT
    header_de_style.fontSize = 11.5
    header_de_style.leading = 11.5 + 4
    header_de_style.borderPadding = 5

    header_de = Paragraph("Österreichische Gesellschaft für Vermessung und Geoinformation", header_de_style)
    header_en = Paragraph("Austrian Society for<br />Surveying and Geoinformation", styles["Normal"])
    h, w = header_de.wrap(7*cm, 1.2*cm)
    header_de.drawOn(canvas, 3*cm + 0.3*cm, pos_y1)
    h, w = header_en.wrap(7*cm, 1.2*cm)
    header_en.drawOn(canvas, 3*cm + 0.3*cm, pos_y2)


def generate_address(canvas, pos_x, pos_y,
    description=None,
    company=None, department=None,
    name="Max Musermann",
    street="Kaiserstraße 1", zip_code="1160", city="Wien", country=None):
    data = []
    if description:
        data += [[description, ""]]
    if company:
        data += [[company, ""]]
        if department:
            data += [[department, ""]]
    if name:
        data += [[name, ""]]
    data += [
        [street, ""],
        ["{} {}".format(zip_code, city), ""],
    ]
    if country:
        data += [[country, ""]]
    table = Table(data=data, rowHeights=12)
    w, h = table.wrapOn(canvas, 0, 0)
    table.drawOn(canvas, pos_x, pos_y-h)


def generate_footer(canvas, pos_x, pos_y):
    # OVG Footer
    footer_data = [
        ["OVG - Herausgeber der einzigen Zeitschrift für Vermessung und Geoinformation in Österreich"],
        ["Bank", s.BANK, "Web", s.OVG_SITE],
        ["BIC", s.BIC, "ZVR-Zahl", s.OVG_ZVR],
        ["IBAN", s.IBAN_NUMBER, "", ""],
    ]
    footer_table = Table(data=footer_data, colWidths=[1*cm, 12.5*cm, 1.5*cm, 2*cm])
    footer_table.setStyle(TableStyle([
        ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
        ('FONTSIZE', (0, 0), (-1, -1), 8),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 1),
        ('TOPPADDING', (0, 0), (-1, -1), 1),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 2),
        ('VALIGN', (0, 0), (-1, -1), "TOP"),
        ('SPAN', (0, 0), (-1, 0)),
        ('LINEABOVE', (0, 1), (-1, 1), 0.2, colors.black),
    ]))
    w, h = footer_table.wrapOn(canvas, 0, 0)
    footer_table.drawOn(canvas, pos_x, pos_y)

def generate_member_meta(canvas, 
    invoice_date_str, 
    invoice_reference=None, 
    member_id=None,
    vat_id=None,
    abo_id=None,
    pos_x=10*cm, 
    pos_y=s.A4_WIDTH-1*cm):

    pos_y3 = pos_y - 3*cm

    # Member Meta
    member_meta_data = []
    if invoice_date_str:
        member_meta_data.append(["Datum", invoice_date_str])
    if invoice_reference:
        member_meta_data.append(["Rechnungsnr.", invoice_reference])
    if member_id:
        member_meta_data.append(["Kundennr.", member_id])
    if vat_id:
        member_meta_data.append(["Ihre UID", vat_id])
    if abo_id:
        member_meta_data.append(["Abonr.", abo_id])
        
    # row_height = 0.5*cm
    member_meta_table = Table(data=member_meta_data, rowHeights=12)
    w, h = member_meta_table.wrapOn(canvas, 0, 0)
    member_meta_table.drawOn(canvas, pos_x, pos_y3-h)

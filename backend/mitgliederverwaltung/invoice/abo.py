#!/usr/bin/python
# -*- coding: utf-8 -*-

import datetime
import jinja2
import os


from io import BytesIO

from reportlab.lib.pagesizes import A4, portrait
from reportlab.pdfgen.canvas import Canvas
from reportlab.lib.units import cm
from reportlab.platypus import Paragraph, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib import colors

from invoice import settings as s
from invoice import utils as u


def create_abo_invoice(**kwargs):
    """
    Args:
        customer_id: Kundennummer
        customer_vat_id: UID
        abo_id: Abonummer
        abo_year: Verrechnungsjahr
        debt_claim: Zahlungsrückstand (default: 0)
        discount: Rabatt (default: 0)
        book_amount: Anzahl der Hefte (default: 1)
        invoice_date: Rechnungsdatum (default: today)
        generate_pdf: Soll ein PDF erzeugt werden, ansonst Buffer
    """
    styles = getSampleStyleSheet()
    template_loader = jinja2.FileSystemLoader(searchpath=os.path.join(s.ROOT_DIR, s.TEMPLATE_DIR))
    template_env = jinja2.Environment(loader=template_loader)
    TEMPLATE_FILE = "abo.txt.j2"
    template = template_env.get_template(TEMPLATE_FILE)

    # Outputoption
    generate_pdf = kwargs.get("generate_pdf", False)
    
    # Other Options
    customer_id = kwargs.get("customer_id")
    customer_vat_id = kwargs.get("customer_vat_id")
    abo_id = "{:03d}".format(int(kwargs.get("abo_id", 0)))
    abo_year = kwargs.get("abo_year")
    debt_claim = kwargs.get("debt_claim", 0.0)
    discount = kwargs.get("discount", 0.0)
    book_amount = kwargs.get("book_amount", 1)
    book_price = kwargs.get("book_price", 70.0)
    vat_id = kwargs.get("vat_id", None)
    offene_abo_posten = kwargs.get("offene_abo_posten", [])

    price_books = book_amount * book_price
    price_total = price_books - discount + debt_claim

    invoice_date_str = kwargs.get("invoice_date", datetime.date.today().strftime(s.ISO_DATE))
    invoice_date = datetime.datetime.strptime(invoice_date_str, s.ISO_DATE)
    invoice_deadline = invoice_date + datetime.timedelta(days=30*6)
    invoice_reference = kwargs.get("invoice_reference", "{}/{}".format(invoice_date.year, abo_id))
    
    invoice_basename = "ovg_abo_{}".format(invoice_reference.replace("/", "_"))
    invoice_filename = os.path.join(s.ROOT_DIR, s.OUT_DIR, "{}.pdf".format(invoice_basename))

    # Rechnung- und Lieferanschrift
    inv_company = kwargs.get("inv_company", None)
    inv_department = kwargs.get("inv_department", None)
    inv_name = kwargs.get("inv_name", None)
    inv_street = kwargs.get("inv_street", None)
    inv_zip = kwargs.get("inv_zip", None)
    inv_city = kwargs.get("inv_city", None)
    inv_country = kwargs.get("inv_country", None)

    shp_company = kwargs.get("shp_company", None)
    shp_department = kwargs.get("shp_department", None)
    shp_name = kwargs.get("shp_name", None)
    shp_street = kwargs.get("shp_street", None)
    shp_zip = kwargs.get("shp_zip", None)
    shp_city = kwargs.get("shp_city", None)
    shp_country = kwargs.get("shp_country", None)

    margin_left = 2.0*cm
    margin_left_text = 2.0*cm
    margin_right = 2.0*cm

    buffer = BytesIO()
    canvas = Canvas(
        invoice_filename if generate_pdf else buffer,
        pagesize=portrait(A4)
    )

    # OVG Header
    u.generate_header(canvas, pos_y=s.A4_HEIGHT-1*cm, pos_x=s.A4_WIDTH/2+4.7*cm)
    u.generate_member_meta(canvas, 
        invoice_date.strftime(s.ISO_DATE), 
        invoice_reference,
        customer_id,
        vat_id=vat_id,
        abo_id=abo_id,
        pos_y=s.A4_HEIGHT-2.4*cm, 
        pos_x=s.A4_WIDTH/2+4.7*cm)

    # Rechnungsanschrift
    u.generate_address(canvas, 
        company=inv_company, department=inv_department,
        name=inv_name,
        street=inv_street, 
        zip_code=inv_zip, city=inv_city, 
        country=inv_country,
        pos_x=margin_left, pos_y=s.A4_HEIGHT-5.4*cm)

    # Lieferanschrift
    u.generate_address(canvas, 
        description="Lieferanschrift:",
        company=shp_company, department=shp_department,
        name=shp_name,
        street=shp_street, 
        zip_code=shp_zip, city=shp_city, 
        country=shp_country,
        pos_x=s.A4_WIDTH/2+4.7*cm, pos_y=s.A4_HEIGHT-7.7*cm)

    # Subject
    subject_text = """Rechnung GZ {invoice_id:}<br/>
    {ovg:} - Abonnement""".format(
        invoice_id=invoice_reference,
        ovg=s.OVG_NAME
    )
    p = Paragraph(subject_text, styles["Heading3"])
    used_width, used_height = p.wrap(s.A4_WIDTH - margin_left_text - margin_right, 0*cm)
    line_widths = p.getActualLineWidths0()
    nol = len(line_widths)
    if nol > 1:
        actual_width = used_width
    elif nol == 1:
        actual_width = min(line_widths)
    else:
        return 0, 0
    p.drawOn(canvas, margin_left_text, s.A4_HEIGHT - 11.5*cm)
    
    
    
    anschrift = "Sehr geehrte Damen und Herren,<br/>wir dürfen Ihnen das vgi-Abonnement für folgende Jahre in Rechnung stellen:".format(abo_year)
    p = Paragraph(anschrift, styles["Normal"])
    used_width, used_height = p.wrap(s.A4_WIDTH - margin_left_text - margin_right, 0*cm)
    line_widths = p.getActualLineWidths0()
    nol = len(line_widths)
    if nol > 1:
        actual_width = used_width
    elif nol == 1:
        actual_width = min(line_widths)
    else:
        return 0, 0
    p.drawOn(canvas, margin_left_text, s.A4_HEIGHT - 13.5*cm)
    

    # Invoice Detail
    zwischensumme = sum([o.offen for o in offene_abo_posten])
    ovg_due_beauty = Paragraph("<para align=right><b>EUR {:.2f}</b></para>".format(price_total), style=styles["Normal"])
    
    tableStyles = [
        ('ALIGN', (1, 0), (-1, -1), 'RIGHT'),
        ('LINEABOVE', (0, -1), (-1, -1), 2, colors.black),
        ('BACKGROUND', (1, -1), (-1, -1), colors.lavender),
    ]

    ovg_subscriptions_data = [[o.description, "{:.2f}".format(o.offen)] for o in offene_abo_posten]
    if discount > 0.0:
        ovg_subscriptions_data.append(["Zwischensumme", "{:.2f}".format(zwischensumme)])
        ovg_subscriptions_data.append(["Rabatt - {}%".format(int(discount*100)), "-{:.2f}".format(zwischensumme*discount)])
        tableStyles.append(('LINEABOVE', (0, -3), (-1, -3), 2, colors.black))
    ovg_subscriptions_data.append(["Gesamtsumme", "{:.2f}".format(zwischensumme*(1-discount))])


    subscription_table = Table(data=ovg_subscriptions_data, rowHeights=15)
    subscription_table.setStyle(TableStyle(tableStyles))
 
    subscription_table._argW[1] = 2.5*cm
    w1, h1 = subscription_table.wrapOn(canvas, 0, 0)
    subscription_table.drawOn(canvas, margin_left+3*cm, s.A4_HEIGHT-h1-14*cm)

    # Invoice Text
    invoice_text = template.render(
        invoice_reference=invoice_reference,
        invoice_deadline=invoice_deadline.strftime(s.ISO_DATE),
	discount=(discount > 0.0),
        # ovg_news=ovg_news,
        ovg_treasurer=s.OVG_TREASURER
    )
    p = Paragraph(invoice_text, styles["Normal"])
    used_width, used_height = p.wrap(s.A4_WIDTH-margin_left_text-margin_right, 0)
    line_widths = p.getActualLineWidths0()
    nol = len(line_widths)
    if nol > 1:
        actual_width = used_width
    elif nol == 1:
        actual_width = min(line_widths)
    else:
        return 0, 0
    w, h = subscription_table.wrapOn(canvas, 0, 0)
    p.drawOn(canvas, margin_left_text, s.A4_HEIGHT-17.0*cm-h1-3*cm)

    # OVG Footer
    # footer_data = [
    #     ["OVG - Herausgeber der einzigen Zeitschrift für Vermessung und Geoinformation in Österreich"],
    #     ["Bank", s.BANK, "Web", s.OVG_SITE],
    #     ["BIC", s.BIC, "", ""],
    #     ["IBAN", s.IBAN_NUMBER, "ZVR-Zahl", s.OVG_ZVR]
    # ]
    # print("W: {}")
    # footer_table = Table(data=footer_data, colWidths=[1*cm, 12.5*cm, 1.5*cm, 2*cm], rowHeights=12)
    # footer_table.setStyle(TableStyle([
    #     ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
    #     ('FONTSIZE', (0, 0), (-1, -1), 8),
    #     ('VALIGN', (0, 0), (-1, -1), "TOP"),
    #     ('SPAN', (0, 0), (3, 0)),
    #     ('LINEABOVE', (0, 1), (-1, 1), 1, colors.black),
    # ]))
    # #footer_table._argW[0]
    # #footer_table._argW[1] = 2.5*cm
    # w1, h1 = footer_table.wrapOn(canvas, 0, 0)
    # footer_table.drawOn(canvas, margin_left, 1*cm)
    u.generate_footer(canvas, margin_left, 1*cm)

    canvas.showPage()
    canvas.save()
    return buffer.getvalue()


if __name__ == "__main__":
    create_abo_invoice(
        customer_id="108",
        invoice_date="2018-12-06",
        abo_id="4",
        abo_year="2018",
        vat_id="ATU1234567",
        inv_company="Messfuchs Fredriksson", inv_department="Administration",
        inv_name="DI Jürgen Fredriksson",
        inv_street="Steingrubenweg 4k", inv_zip="2352", inv_city="Gumpoldskirchen",
        shp_company="BEV", shp_department="V1",
        shp_name="DI Jürgen Fredriksson",
        shp_street="Schiffamtsgasse 1-3", shp_zip="1020", shp_city="Wien"
    )

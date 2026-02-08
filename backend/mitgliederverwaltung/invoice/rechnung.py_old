#!/usr/bin/python
# -*- coding: utf-8 -*-

import datetime
import jinja2

from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.platypus.doctemplate import PageTemplate, BaseDocTemplate
from reportlab.pdfgen.canvas import Canvas
from reportlab.platypus.flowables import Flowable
from reportlab.lib.utils import ImageReader
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.rl_config import defaultPageSize
from reportlab.lib.units import cm
from io import BytesIO


styles = getSampleStyleSheet()
template_loader = jinja2.FileSystemLoader(searchpath="./")
template_env = jinja2.Environment(loader=template_loader)
TEMPLATE_FILE = "invoice/rechnungs_text.txt.j2"
template = template_env.get_template(TEMPLATE_FILE)

INVOICE_HEADER_IMAGE = "invoice/BriefkopfOVG.jpg"
ISO_DATE = "%Y-%m-%d"

LOGO_WIDTH = 13.*cm
LOGO_HEIGHT = 2.334*cm

A4_HEIGHT = 29.7*cm
A4_WIDTH = 21.0*cm


def createInvoice(**kwargs):
    """
    :params member_id: Mitgliedsnummer
    :params invoice_date_str: Datum der Rechnung (YYYY-MM-DD)
    :params invoice_reference: Verwendungszweck (DDD/YYYY)
    :params invoice_recipient: Empfänger
    :params invoice_to: Empfänger-Detail
    :params invoice_street: Rechnungsadresse/Straße+Nr
    :params invoice_zip: Rechnungsadresse/Postleitzahl
    :params invoice_city: Rechnungsadresse/Stadt
    :params invoice_country: Rechnungsadresse/Staat (Österreich)
    :params show_country: Zeige Rechnungsadresse/Staat (False)
    :params ovg_news: Zusätzliche Information für Rechnungsempfänger (News)
    :params ovg_dues: offene Beiträge [(TEXT, FFF.FF), (TEXT, FFF.FF), ...]
    :params ovg_credit: Gutschrift (0.00)

    """
   
    # mandatory arguments
    member_id = kwargs.get("member_id")

    # obligatory arguments
    invoice_date_str = kwargs.get("invoice_date", datetime.date.today().strftime(ISO_DATE))
    invoice_date = datetime.datetime.strptime(invoice_date_str, ISO_DATE)
    invoice_deadline = invoice_date + datetime.timedelta(days=30*6)
    invoice_reference = kwargs.get("invoice_reference", "{}".format(member_id, invoice_date.strftime("%Y%m%d%H%M%S") ))

    invoice_recipient = kwargs.get("invoice_recipient", "Bundesamt f. Eich- und Vermessungswesen")
    invoice_to = kwargs.get("invoice_to", "Abteilung V1")
    invoice_street = kwargs.get("invoice_street", "Schiffamtsgasse 1-3")
    invoice_zip = kwargs.get("invoice_zip", "1020")
    invoice_city = kwargs.get("invoice_city", "Wien")
    invoice_country = kwargs.get("invoice_country", "Österreich")
    show_country = kwargs.get("show_country", False)
    ovg_news = kwargs.get("ovg_news", "")
    ovg_dues = kwargs.get("ovg_dues", [])
    ovg_credit = kwargs.get("ovg_credit", 0.0)

    ovg_due_sum = sum(map(lambda d: d[1], ovg_dues))

    ovg_treasurer = "Wolfgang Gold, Schatzmeister"
    ovg_site = "www.ovg.at"
    ovg_zvr = "403011926"


    buffer = BytesIO()
    canvas = Canvas(
        buffer,
        # invoice_filename,
        pagesize=landscape(A4)
    )

    # OVG Header
    invoice_header = ImageReader(INVOICE_HEADER_IMAGE)
    canvas.drawImage(invoice_header, x=1.1*cm, y=18*cm, height=LOGO_HEIGHT, width=LOGO_WIDTH)

    # Member Meta
    member_meta_data = [
        ["Datum", invoice_date.strftime(ISO_DATE)],
        ["GZ", invoice_reference],
        ["MitgliedsNr.", member_id]
    ]
    row_height = 0.5*cm
    member_meta_table = Table(data=member_meta_data, rowHeights=12)
    w, h = member_meta_table.wrapOn(canvas, 0, 0)
    member_meta_table.drawOn(canvas, 10*cm, A4_WIDTH-3.5*cm-h)

    # Billing Address
    billing_data = [
        [invoice_recipient],
        [invoice_to],
        [invoice_street],
        ["{} {}".format(invoice_zip, invoice_city)],
    ]
    row_height = 0.5*cm
    billing_table = Table(data=billing_data, rowHeights=12)
    w, h = billing_table.wrapOn(canvas, 0, 0)
    billing_table.drawOn(canvas, 0.76*cm, A4_WIDTH-3.5*cm-h)

    # Say words to the member
    invoice_text = template.render(
        ovg_subscription_year=invoice_date.year,
        ovg_member_id=member_id,
        ovg_subscription_deadline=invoice_deadline.strftime(ISO_DATE),
        ovg_news=ovg_news,
        ovg_treasurer=ovg_treasurer
    )
    p = Paragraph(invoice_text, styles["Normal"])
    used_width, used_height = p.wrap(LOGO_WIDTH, 4.3*cm)
    line_widths = p.getActualLineWidths0()
    nol = len(line_widths)
    if nol > 1:
        actual_width = used_width
    elif nol == 1:
        actual_width = min(line_widths)
    else:
        return 0, 0
    p.drawOn(canvas, 1*cm, A4_WIDTH-5.5*cm - used_height)

    # Erlagschein/schwarz
    billing_table.drawOn(canvas, 2.5*cm, 5.5*cm-h)

    # Zu zahlender Betrag
    dueText = canvas.beginText()
    dueText.setTextOrigin(13*cm, 7*cm)
    dueText.textLine("{:.2f}".format(ovg_due_sum))
    canvas.drawText(dueText)

    # Member Meta
    member_meta_data = [
        ["Datum", invoice_date.strftime(ISO_DATE)],
        ["Beitrag", invoice_date.year],
        ["GZ", invoice_reference],
        ["MitgliedsNr.", member_id],
        ["Web", ovg_site],
        ["ZVR-Zahl", ovg_zvr]

    ]
    row_height = 0.5*cm
    member_meta_table = Table(data=member_meta_data, rowHeights=12)
    w, h = member_meta_table.wrapOn(canvas, 0, 0)
    member_meta_table.drawOn(canvas, A4_WIDTH/2. - 0.7*cm, 6*cm-h)

    # Erlagschein/rot
    dueText = canvas.beginText()
    dueText.setTextOrigin(13*cm+A4_HEIGHT/2., 7*cm)
    dueText.textLine("{:.2f}".format(ovg_due_sum))
    dueText.setTextOrigin(1*cm+A4_HEIGHT/2., 5.5*cm-12)
    dueText.textLine(invoice_reference)
    canvas.drawText(dueText)

    # Beitragsberechnung
    ovg_due_beauty = Paragraph("<para align=right><b>{:.2f}</b></para>".format(ovg_due_sum-ovg_credit), style=styles["Normal"])
    ovg_subscriptions_data = [["{}".format(b[0]), "{:.2f}".format(b[1])] for b in ovg_dues]
    ovg_subscriptions_data.append(["Zwischensumme", "{:.2f}".format(ovg_due_sum)])
    ovg_subscriptions_data.append(["Gutschrift", "{:.2f}".format(ovg_credit)])
    ovg_subscriptions_data.append(["Total", ovg_due_beauty])
    subscription_table = Table(data=ovg_subscriptions_data)
    subscription_table.setStyle(TableStyle([
        ('ALIGN', (1, 0), (-1, -1), 'RIGHT'),
        ('LINEABOVE', (0, -1), (-1, -1), 1, colors.black),
        ('LINEABOVE', (0, -3), (-1, -3), 1, colors.black),
        ('BACKGROUND', (1, -1), (-1, -1), colors.lavender),
    ]))
    subscription_table._argW[1] = 2*cm
    w, h = subscription_table.wrapOn(canvas, 0, 0)
    subscription_table.drawOn(canvas, 17*cm, 18*cm-h)

    # A4 Split
    p1 = canvas.beginPath()
    p1.moveTo(A4_HEIGHT/2., 0.*cm)
    p1.lineTo(A4_HEIGHT/2., A4_WIDTH)
    p1.moveTo(0.*cm, A4_WIDTH/2.)
    p1.lineTo(A4_HEIGHT, A4_WIDTH/2.)
    canvas.drawPath(p1, stroke=1, fill=1)

    canvas.showPage()
    canvas.save()
    pdf = buffer.getvalue()

    return pdf


if __name__ == "__main__":
    createInvoice(
        member_id="108",
        invoice_date="2018-12-06",
        ovg_dues=[("Beitrag 2017", 55.), ("Beitrag 2018", 55.)]
    )

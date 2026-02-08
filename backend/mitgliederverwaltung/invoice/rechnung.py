#!/usr/bin/python
# -*- coding: utf-8 -*-

import datetime
import jinja2
import os

from svglib.svglib import svg2rlg
from io import BytesIO

from reportlab.graphics import renderPDF
from reportlab.pdfgen.canvas import Canvas
from reportlab.platypus import Paragraph, Table, TableStyle

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import cm


from . import utils as u
from . import settings as s


styles = getSampleStyleSheet()
template_loader = jinja2.FileSystemLoader(searchpath=os.path.join(s.ROOT_DIR, s.TEMPLATE_DIR))
template_env = jinja2.Environment(loader=template_loader)
TEMPLATE_FILE = "rechnungs_text.txt.j2"
template = template_env.get_template(TEMPLATE_FILE)
QR_TEMPLATE_FILE = "stuzza_payload.txt.j2"
qr_template = template_env.get_template(QR_TEMPLATE_FILE)


FRAME_ON = 1
FRAME_OFF = 0


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
    :params ovg_dues: offene Beiträge [(YYYY, FFF.FF), (YYYY, FFF.FF), ...]
    :params ovg_credit: Gutschrift (0.00)
    :params generate_pdf: Soll ein PDF erzeugt werden, sonst Buffer

    """
   
    # mandatory arguments
    member_id = kwargs.get("member_id")

    # obligatory arguments

    generate_pdf = kwargs.get("generate_pdf", False)
    invoice_date_str = kwargs.get("invoice_date", datetime.date.today().strftime(s.ISO_DATE))
    invoice_date = datetime.datetime.strptime(invoice_date_str, s.ISO_DATE)
    invoice_deadline = invoice_date + datetime.timedelta(days=30*6)
    invoice_deadline = kwargs.get("invoice_deadline", invoice_date+datetime.timedelta(days=30*6))

    invoice_reference = kwargs.get("invoice_reference", "{}/{}".format(invoice_date.year, member_id))
    
    invoice_basename = "ovg_inv_{}".format(invoice_reference.replace("/", "_"))
    invoice_filename = os.path.join(s.OUT_DIR, "{}.pdf".format(invoice_basename))

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
    frame_visibility = FRAME_ON
    
    print_folding = kwargs.get("print_folding", False)

    ovg_due_sum = sum(map(lambda d: d[1], ovg_dues))
    ovg_due_pay = ovg_due_sum - ovg_credit

    # Configs
    row_height = 0.5*cm
    pos_inhalt = s.A4_WIDTH-4*cm

    buffer = BytesIO()
    canvas = Canvas(
        invoice_filename if generate_pdf else buffer,
        pagesize=landscape(A4)
    )

    # OVG Header
    u.generate_header(canvas)

    # Member Meta
    u.generate_member_meta(canvas, 
        invoice_date.strftime(s.ISO_DATE), 
        invoice_reference,
        member_id) 

    # Billing Address
    billing_data = [
        [invoice_recipient],
        [invoice_to],
        [invoice_street],
        ["{} {}".format(invoice_zip, invoice_city)],
    ]
    if show_country:
        billing_data.append([invoice_country])

    # row_height = 0.5*cm
    billing_table = Table(data=billing_data, rowHeights=12)
    w, h = billing_table.wrapOn(canvas, 0, 0)
    billing_table.drawOn(canvas, 0.76*cm, pos_inhalt-h)

    # Say words to the member
    invoice_text = template.render(
        ovg_subscription_year=invoice_date.year,
        ovg_member_id=member_id,
        ovg_subscription_deadline=invoice_deadline.strftime(s.ISO_DATE),
        ovg_news=ovg_news,
        ovg_treasurer=s.OVG_TREASURER
    )
    p = Paragraph(invoice_text, styles["Normal"])
    used_width, used_height = p.wrap(s.LOGO_WIDTH, 4.3*cm)
    line_widths = p.getActualLineWidths0()
    nol = len(line_widths)
    if nol > 1:
        actual_width = used_width
    elif nol == 1:
        actual_width = min(line_widths)
    else:
        return 0, 0
    p.drawOn(canvas, (1.+14.8)*cm, s.A4_WIDTH - (5.5)*cm - used_height + 3.9*cm)

    # Erlagschein/schwarz
    billing_table.drawOn(canvas, (2.5+0.1)*cm, (5.5-0.6)*cm-h)

    dueText = canvas.beginText()
    # Betrag schwarz
    box = 3*cm
    text_string = "{:6.2f}".format(ovg_due_pay).replace(".", ",")
    d = dict(**styles["Normal"].__dict__)

    fn = d["fontName"]
    fs = d["fontSize"]
    text_width = Canvas.stringWidth(canvas,text=text_string, fontName=fn, fontSize=fs)
    adjust_width = box - text_width
    dueText.setTextOrigin((13+0.1)*cm, (7-0.5)*cm)
    dueText.textLine(text_string)
    canvas.drawText(dueText)

    # Verwendungszweck scharz
    member_meta_data = [
        ["Datum", invoice_date.strftime(s.ISO_DATE)],
        ["GZ", invoice_reference],
        ["MitgliedsNr.", member_id],
        ["Beitrag", invoice_date.year],
        [" ", " "],
        ["Web", s.OVG_SITE],
        ["ZVR-Zahl", s.OVG_ZVR]
    ]
    # row_height = 0.5*cm
    member_meta_table = Table(data=member_meta_data, rowHeights=10)
    member_meta_table.setStyle(TableStyle([
        ('FONTSIZE', (0, 0), (-1, -1), 7),
    ]))
    w, h = member_meta_table.wrapOn(canvas, 0, 0)
    member_meta_table.drawOn(canvas, s.A4_WIDTH/2. - 0.7*cm + 1.4*cm, 6*cm-h - 1.1*cm)

    # Erlagschein/rot
    dueText = canvas.beginText()
    # Betrag ROT
    dueText.setTextOrigin(13*cm + s.A4_HEIGHT/2. + 0.1*cm, (7-0.5)*cm)
    dueText.textLine("{:6.2f}".format(ovg_due_pay).replace(".", ","))
    # Verwendungszweck rot
    dueText.setTextOrigin(1*cm+s.A4_HEIGHT/2., (5.5-0.35)*cm-12)
    dueText.textLine(invoice_reference)  
    canvas.drawText(dueText)
    
    # QR Code
    qr_payload = qr_template.render(
        iban_creditor=s.IBAN_CREDITOR,
        iban_number=s.IBAN_NUMBER,
        iban_amount=ovg_due_pay,
        iban_reference=invoice_reference
    )
    qr_file = os.path.join(s.ROOT_DIR, s.OUT_DIR, "{}.svg".format(invoice_basename))
    qr_img = u.generate_qr(qr_payload)
    qr_img.save(qr_file)
    qr_drawing = svg2rlg(qr_file)
    qr_drawing.transform = (0.5, 0, 0, 0.5, 0, 0)
    renderPDF.draw(qr_drawing, canvas, 26.7*cm, (1.2+1.55)*cm)
    os.remove(qr_file)

    # Beitragsberechnung
    ovg_due_beauty = Paragraph("<para align=right><b>EUR {:.2f}</b></para>".format(ovg_due_pay), style=styles["Normal"])
    
    ovg_subscriptions_data = [["{}".format(b[0]), "{:.2f}".format(b[1])] for b in ovg_dues]
    ovg_subscriptions_data.append(["Zwischensumme", "{:.2f}".format(ovg_due_sum)])
    ovg_subscriptions_data.append(["Gutschrift", "{:.2f}".format(ovg_credit)])
    ovg_subscriptions_data.append(["Total", ovg_due_beauty])
    subscription_table = Table(data=ovg_subscriptions_data, rowHeights=15)
    subscription_table.setStyle(TableStyle([
        ('ALIGN', (1, 0), (-1, -1), 'RIGHT'),
        ('LINEABOVE', (0, -1), (-1, -1), 1, colors.black),
        ('LINEABOVE', (0, -3), (-1, -3), 1, colors.black),
        ('BACKGROUND', (1, -1), (-1, -1), colors.lavender),
    ]))
    subscription_table._argW[1] = 2.5*cm
    w, h = subscription_table.wrapOn(canvas, 0, 0)
    subscription_table.drawOn(canvas, (17.-16.25+8.68-0.25)*cm, (18.-3.5)*cm-h)

    # A4 Faltung
    if print_folding:
        p1 = canvas.beginPath()
        p1.moveTo(s.A4_HEIGHT/2., 1.*cm)
        p1.lineTo(s.A4_HEIGHT/2., s.A4_WIDTH-1.*cm)
        p1.moveTo(1.*cm, s.A4_WIDTH/2.)
        p1.lineTo(s.A4_HEIGHT-1.*cm, s.A4_WIDTH/2.)
        canvas.drawPath(p1, stroke=1, fill=1)

    canvas.showPage()
    canvas.save()
    return buffer.getvalue()
    

if __name__ == "__main__":
    createInvoice(
        member_id="108",
        invoice_date="2018-12-06",
        invoice_recipient="Messfuchs Fredriksson",
        invoice_to="Dipl.-Ing. Jürgen Fredriksson",
        invoice_street="Steingrubenweg 4k",
        invoice_zip="2352", invoice_city="Gumpoldskirchen",
        ovg_news="Sonst gibt es nichts neues am BEV<br />Wenn man mag, kann man einfach hier etwas dazuschreiben, ganz wie man mag oder eben nicht oder sonst irgendwas. Ganz wichtig... Zeilenumbrüche sind als HTML-Tags 'br/' anzugeben....",
        ovg_dues=[("Beitrag 2017", 55.), ("Beitrag 2018", 55.),],
        generate_pdf=True
    )

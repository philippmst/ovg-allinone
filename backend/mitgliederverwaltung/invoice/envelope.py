#!/bin/python3

import os
import copy
# import logging

from io import BytesIO
from reportlab.lib.utils import ImageReader
from reportlab.lib.units import cm
from reportlab.pdfgen.canvas import Canvas
from reportlab.lib.pagesizes import landscape
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle

from . import settings as s
from . import utils as u


DEFAULT_SENDER = {
    "sender_name": "VGI",
    "sender_extra": None,
    "sender_street": "Schiffamtsgasse 1-3",
    "sender_zip": "1020",
    "sender_city": "Wien",
}


# logger = logging.getLogger(__name__)


def create_envelope(**kwargs):
    """ Create multi purpose envelope 
    Args:
        recipient_id: Member Id
        recipient_name: 
        recipient_extra: Extra name line
        recipient_street: 
        recipient_postbox: 
        recipient_zip:
        recipient_country:

        sender_name:
        sender_extra:
        sender_street:
        sender_zip:
        sender_country:
        sender_logo: Path to logo

        generate_pdf: bool
        out_dir: Directory to store pdf
        type: any, int (international), aut (Austria), bev (Internal letter)
    """

    DEFAULT_FONT_SIZE = 10
    DEFAULT_TABLE_STYLE = [
        ('FONTSIZE', (0, 0), (-1, -1), DEFAULT_FONT_SIZE),
    ]
    styles = getSampleStyleSheet()

    margin_top = 0.5*cm
    margin_right = 0.5*cm
    margin_left = 0.25*cm
    margin_bottom = 0.25*cm

    env_width = 10*cm
    env_height = 6*cm

    logo_height = 2.3*cm

    rowHeights = 13

    envelope_type = kwargs.get("type", "any")
    
    pobox = kwargs.get("recipient_postbox", "")
    if type(pobox) == str:
        pobox = "PO Box {}".format( pobox.strip() )

    extra = kwargs.get("recipient_extra", "")
    if type(extra) == str:
        extra = extra.strip()


    recipient = {
        "pk": kwargs.get("recipient_id"),
        "name": kwargs.get("recipient_name"),
        "extra": kwargs.get("recipient_extra", ""),
        "street": kwargs.get("recipient_street", "").strip(),
        "postbox": pobox,
        "zip": kwargs.get("recipient_zip"),
        "city": kwargs.get("recipient_city"),
        "country": kwargs.get("recipient_country", "").upper()
    }

    if envelope_type == "int":
        recipient["city"] = recipient["city"].upper()

    recipient_zip_city = "{} {}".format(recipient["zip"], recipient["city"])
    # recipient_to = recipient["street"]
    # if recipient["postbox"]:
    #     recipient_to = recipient["postbox"]

    assert recipient["street"] != "" or recipient["postbox"] != ""

    sender = {
        "name": kwargs.get("sender_name"),
        "extra": kwargs.get("sender_extra", ""),
        "street": kwargs.get("sender_street"),
        "zip": kwargs.get("sender_zip"),
        "city": kwargs.get("sender_city"),
        "country": kwargs.get("sender_country", "").upper()
    }

    sender_logo = kwargs.get("sender_logo", "eco_post.png")

    generate_pdf = kwargs.get("generate_pdf", False)
    out_dir = kwargs.get("out_dir", s.OUT_DIR)
    if generate_pdf:
        assert os.path.exists(out_dir)

    envelope_basename = "ovg_env_{}_{}".format(envelope_type, recipient["pk"])
    envelope_filename = os.path.join(out_dir, "{}.pdf".format(envelope_basename))
    buffer = BytesIO()

    canvas_out = envelope_filename if generate_pdf else buffer

    canvas = Canvas(
        canvas_out,
        pagesize=landscape((env_height, env_width))
    )

    print("Writing Canvas to %s" % canvas_out)

    # Add postal logo
    if sender_logo:
        postal_logo_path = str(os.path.join(s.ROOT_DIR, s.TEMPLATE_DIR, sender_logo))
        postal_logo = u.get_image(postal_logo_path, logo_height)
        w, h = postal_logo.wrapOn(canvas, 0, 0)
        #print(w, h)
        postal_logo.drawOn(canvas, x=env_width - w - margin_right, y=env_height - h - margin_top)

    # Add sender
    sender_table_style = copy.deepcopy(DEFAULT_TABLE_STYLE)
    if envelope_type == "aut":
        sender_meta_data = [
            [
                "Österreichiche Post AG"
            ],
            [
                "PZ 22Z042940 P"
            ],
            [
                "{}, {}, {}, {}".format( sender["name"], sender["street"], sender["zip"], sender["city"]), ""
            ]
        ]
    else:
        sender_meta_data = [
            ["{}, {}".format(sender["name"], sender["street"]), " "],
            ["{} {}".format(sender["zip"], sender["city"]), ""],
        ]

    sender_meta_table = Table(data=sender_meta_data, rowHeights=rowHeights)
    sender_meta_table.setStyle(TableStyle(sender_table_style))
    w, h = sender_meta_table.wrapOn(canvas, 0, 0)
    sender_meta_table.drawOn(canvas, margin_left, env_height - h - margin_top)

    # Add recipient
    recipient_table_style = copy.deepcopy(DEFAULT_TABLE_STYLE)
    recipient_meta_data = [
        [recipient["name"], ""]
    ]

    if recipient["extra"]:
        recipient_meta_data.append(
            [recipient["extra"], ""],
        )

    if recipient["street"]:
        recipient_meta_data.append(
            [recipient["street"], ""]
        )

    if recipient["postbox"]:
        recipient_meta_data.append(
            ["PO Box {}".format(recipient["postbox"]), ""] 
        )

    recipient_meta_data.append(
        [recipient_zip_city, ""]
    )

    if recipient["country"]:
        recipient_meta_data.append(
            [recipient["country"], ""]
        )

    recipient_meta_table = Table(data=recipient_meta_data, rowHeights=rowHeights)
    recipient_meta_table.setStyle(TableStyle(recipient_table_style))
    w, h = recipient_meta_table.wrapOn(canvas, 0, 0)
    # print("Recipient Size")
    # print(w, h)
    recipient_meta_table.drawOn(canvas, margin_left, margin_bottom)

    # Generate Output
    canvas.showPage()
    canvas.save()
    return buffer.getvalue()


def create_envelope_int(**kwargs):
    """ Create envelope for EU and Abroad usage """
    d = {
        "recipient_name": kwargs.get("recipient_name"),
        "recipient_extra": kwargs.get("recipient_extra", ""),
        "recipient_street": kwargs.get("recipient_street"),
        "recipient_zip": kwargs.get("recipient_zip"),
        "recipient_city": kwargs.get("recipient_city"),
        "recipient_country": kwargs.get("recipient_country"),
        "type": "int",
    }
    kwargs.update(d)
    kwargs.update(DEFAULT_SENDER)
    return create_envelope(**kwargs)


def create_envelope_aut(**kwargs):
    """ Create envelope for Austria """
    d = {
        "recipient_name": kwargs.get("recipient_name"),
        "recipient_extra": kwargs.get("recipient_extra", ""),
        "recipient_street": kwargs.get("recipient_street"),
        "recipient_zip": kwargs.get("recipient_zip"),
        "recipient_city": kwargs.get("recipient_city"),
        "recipient_country": "",
        "sender_logo": "",
        "type": "aut"
    }
    kwargs.update(d)
    kwargs.update(DEFAULT_SENDER)
    return create_envelope(**kwargs)


def create_envelope_bev(**kwargs):
    """ Create envelope for internal usage """
    d = {
        "recipient_name": kwargs.get("recipient_name"),
        "recipient_extra": kwargs.get("recipient_extra"),
        "recipient_street": kwargs.get("recipient_street", "Schiffamtsgasse 1-3"),
        "recipient_zip": kwargs.get("recipient_zip", "1020"),
        "recipient_city": kwargs.get("recipient_city", "Wien"),
        "type": "bev",
        "sender_logo": "OVG_RGB.jpg",
    }
    kwargs.update(d)
    kwargs.update({
        "sender_name": "VGI",
        "sender_street": "Interne Zustellung",
        "sender_zip": "",
        "sender_city": ""
    })
    return create_envelope(**kwargs)

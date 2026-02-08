import os
import shutil
import numpy as np
import uuid
import datetime
from PyPDF2 import PdfMerger


from django.core.files.base import ContentFile
from django.core.mail import EmailMultiAlternatives
from django.utils.encoding import force_str

from rest_framework.metadata import SimpleMetadata
from rest_framework.relations import ManyRelatedField, RelatedField

from invoice.rechnung import createInvoice
from invoice.abo import create_abo_invoice
from invoice.envelope import create_envelope_bev, create_envelope_aut, create_envelope_int



class MyMetaData(SimpleMetadata):
    def get_field_info(self, field):
        field_info = super(MyMetaData, self).get_field_info(field)
        if isinstance(field, (RelatedField, ManyRelatedField)):
            if hasattr(field, 'view_name'):
                if field.view_name != 'adresse-detail':
                    field_info['choices'] = [
                        {
                            'value': choice_value,
                            'display_name': force_str(choice_name, strings_only=True)
                        }
                        for choice_value, choice_name in field.get_choices().items()
                    ]
        return field_info



def sendmail(i, content=""):
    html_content = "<html><head></head><body><h2>Hallo {} {}</h2>{}</body></html>".format(i.first_name, i.last_name, content)
    text_content = 'Danke, schön dass Sie am Geodätentag 2018 teilnehmen werden.'

    email = EmailMultiAlternatives('OVG Mitgliedsbeitrag', text_content, 'noreply@ovg.at', [i.email] )
    email.attach_alternative(html_content, "text/html")
    email.attach_file(i.rechnung.path)
    s = email.send()
    return s


def make_invoice(vm, news=''):
    dues = [(x.description, x.offen) for x in vm.offeneposten_set.filter(bezahlt=False)]

    invoice_date = datetime.datetime.now()

    m = { 'member_id': vm.mitgliedsnummer, 'invoice_date_str': invoice_date,
            'invoice_reference': '{}-{}'.format(vm.mitgliedsnummer, invoice_date.year),
            'invoice_recipient': "{first_name} {last_name}".format(**vm.__dict__),
            'invoice_to': vm.namenszusatz, 'invoice_street': vm.rechnungsadresse.strasse,
            'invoice_zip': vm.rechnungsadresse.plz, 'invoice_city': vm.rechnungsadresse.ort,
            'invoice_country': vm.rechnungsadresse.country.land,
            'show_country': True, 'ovg_news': news, 'ovg_dues': dues,
            'invoice_deadline': datetime.date(2020,2,29)
        }

    x = createInvoice(**m)
    invoice_filename = "ovg_inv_{}_{}.pdf".format(vm.id, invoice_date.strftime("%Y") )

    vm.rechnung.save(invoice_filename, ContentFile(x))
    
    return x


def make_abo_invoice(aboheft):
    book_price = 50.0
    invoice_date = datetime.datetime.now()
    shp_company = ''
    if aboheft.vorname:
        shp_company += aboheft.vorname + ' '
    shp_company += aboheft.nachname

    m = { 'customer_id': aboheft.kundennummer.kundennummer, 
            'customer_vat_id': aboheft.kundennummer.uid,
            'abo_id': aboheft.abonummer,
            'offene_abo_posten': aboheft.offeneaboposten_set.filter(bezahlt=False),
            'abo_year': invoice_date.year,
            'debt_claim': 100, 
            'discount': aboheft.kundennummer.prozent,
            'book_amount': aboheft.heftanzahl,
            'book_price': book_price,
            'invoice_date_str': invoice_date,
            'inv_company': aboheft.kundennummer.name,
            'inv_department': aboheft.kundennummer.name2,
            'inv_name': aboheft.kundennummer.name3,
            'inv_street': aboheft.kundennummer.rechnungsanschrift.strasse,
            'inv_zip':aboheft.kundennummer.rechnungsanschrift.plz ,
            'inv_city': aboheft.kundennummer.rechnungsanschrift.ort,
            'inv_country': aboheft.kundennummer.rechnungsanschrift.country.land,
            'inv_pobox': aboheft.kundennummer.rechnungsanschrift.pobox,

            'shp_company': shp_company,
            'shp_department': aboheft.surname2,
            'shp_name': aboheft.surname3,
            'shp_street': aboheft.strasse,
            'shp_zip':aboheft.plz ,
            'shp_city': aboheft.ort,
            'shp_country': aboheft.country.land,
            'shp_pobox': aboheft.pobox,
            }

    x = create_abo_invoice(**m)

    invoice_filename = "ovg_inv_abo_{}_{}.pdf".format(aboheft.id, invoice_date.strftime("%Y") )
    aboheft.rechnung.save(invoice_filename, ContentFile(x))
    
    return x


def make_etiketten(vms, abos, inst, wohin='BEV'):
    if wohin == 'BEV':
        make_pdf = create_envelope_bev
        merged_filename = 'etiketten_bev.pdf'
    elif wohin == 'AUT':
        make_pdf = create_envelope_aut
        merged_filename = 'etiketten_aut.pdf'
        fplz = []
    elif wohin == 'INT':
        make_pdf = create_envelope_int
        merged_filename = 'etiketten_int.pdf'

    folder = str(uuid.uuid4())
    path = '/tmp/{}'.format(folder)
    os.mkdir(path)
    os.chdir(path)

    c = 0
    for vm in vms.order_by('lieferadresse__plz'):
        if vm.lieferadresse and vm.heftanzahl:
            if wohin == 'AUT':
                fplz.append(vm.lieferadresse.plz)
            land = 'Austria'
            if not vm.first_name:
                rname = vm.last_name
            else:
                rname = "{} {}".format(vm.first_name,vm.last_name)

            if vm.lieferadresse.country:
                land = vm.lieferadresse.country.land
            mm = {
                "recipient_id": vm.mitgliedsnummer,
                "recipient_name": rname,
                "recipient_extra": vm.namenszusatz,
                "recipient_street": vm.lieferadresse.strasse,
                "recipient_zip": vm.lieferadresse.plz,
                "recipient_city": vm.lieferadresse.ort,
                "recipient_postbox": vm.lieferadresse.pobox,
                "recipient_country": land,
            }

            x = make_pdf(**mm)
            for i in range(vm.heftanzahl):
                c = c + i + 1
                fname = "aaa_{:07}_{}".format(c, i)
                f = open(fname, 'wb')
                f.write(x)
                f.close()

    c = 0
    for im in inst.order_by('lieferadresse__plz'):
        if im.lieferadresse and im.heftanzahl:
            print(im.id)
            if wohin == 'AUT':
                fplz.append(im.lieferadresse.plz)
            land = 'Austria'
            if im.lieferadresse.country:
                land = im.lieferadresse.country.land
            mm = {
                "recipient_id": im.mitgliedsnummer,
                "recipient_name": im.institution_name,
                "recipient_extra": im.name2,
                "recipient_street": im.lieferadresse.strasse,
                "recipient_zip": im.lieferadresse.plz,
                "recipient_city": im.lieferadresse.ort,
                "recipient_postbox": im.lieferadresse.pobox,
                "recipient_country": land,
            }

            x = make_pdf(**mm)
            for i in range(im.heftanzahl):
                c = c + i + 1
                fname = str(uuid.uuid4())
                fname = "bbb_{:07}_{}".format(c, i)
                f = open(fname, 'wb')
                f.write(x)
                f.close()

    c = 0
    if abos:
        for ab in abos.order_by('plz'):
            land = 'Austria'
            if ab.country and ab.heftanzahl:
                if wohin == 'AUT':
                    fplz.append(ab.plz)
                land = ab.country.land
                if not ab.vorname:
                    aname = ab.nachname
                else:
                    aname = "{} {}".format(ab.vorname, ab.nachname)
                mm = {
                    "recipient_id": ab.kundennummer,
                    "recipient_name": aname,
                    "recipient_extra": ab.surname2,
                    "recipient_street": ab.strasse,
                    "recipient_zip": ab.plz,
                    "recipient_city": ab.ort,
                    "recipient_postbox": ab.pobox,
                    "recipient_country": land,
                }
    
                x = make_pdf(**mm)
                for i in range(ab.heftanzahl):
                    c = c + i + 1
                    fname = str(uuid.uuid4())
                    fname = "ccc_{:07}_{}".format(c, i)
                    f = open(fname, 'wb')
                    f.write(x)
                    f.close()

    pfade = np.sort(os.listdir(path))
    merger(merged_filename, pfade)

    fname = path + "/" + merged_filename
    pdf = open(fname, 'rb')
    shutil.rmtree(path)

    if wohin == 'AUT':
        os.chdir("/tmp")
        ff = open('plz.csv', 'w')
        ff.writelines(fplz)
        ff.close()
        print(os.listdir())
        print(os.getcwd())
    return pdf


def merger(output_path, input_paths):
    pdf_merger = PdfMerger()
    file_handles = []
 
    for path in input_paths:
        pdf_merger.append(path)
 
    with open(output_path, 'wb') as fileobj:
        pdf_merger.write(fileobj)
 


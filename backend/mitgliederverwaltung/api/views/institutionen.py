import datetime
import shutil

from django.core.files.base import ContentFile
from django.http import FileResponse

from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response

from api.serializers import InstitutionenSerializer
from mitglieder.models import offenePosten, Land, Beruf, Mitgliedsart, Kosten, Vortragsort, Adresse, Institution
from .helpers import MyMetaData, merger
from invoice.rechnung import createInvoice


def make_invoice(inst, news=''):
    dues = [(x.description, x.offen) for x in inst.offeneposten_set.filter(bezahlt=False)]

    invoice_date = datetime.datetime.now()

    m = { 'member_id': inst.mitgliedsnummer, 'invoice_date_str': invoice_date,
            'invoice_reference': '{}-{}'.format(inst.mitgliedsnummer, invoice_date.year),
            'invoice_recipient': "{institution_name}".format(**inst.__dict__),
            'invoice_to': '', 'invoice_street': inst.rechnungsadresse.strasse,
            'invoice_zip': inst.rechnungsadresse.plz, 'invoice_city': inst.rechnungsadresse.ort,
            'show_country': True, 'ovg_news': news, 'ovg_dues': dues,
            'invoice_deadline': datetime.date(2020,2,29)
            }

    x = createInvoice(**m)
    invoice_filename = "ovg_inv_inst_{}_{}.pdf".format(inst.id, invoice_date.strftime("%Y") )

    inst.rechnung.save(invoice_filename, ContentFile(x))
    
    return x



class InstitutionenViewSet(viewsets.ModelViewSet):
    queryset = Institution.objects.all()
    serializer_class = InstitutionenSerializer
    metadata_class = MyMetaData

    def get_queryset(self):
        if 'aktiv' in self.request.GET:
            inst = Institution.aktive.all()
        else:
            inst = Institution.objects.all()
        
        if 'key' in self.request.GET and 'value' in self.request.GET:
            kwargs = {'{}'.format(self.request.GET['key']): self.request.GET['value'] }
            inst = inst.filter(**kwargs)

        namefilter = self.request.query_params.get('namefilter')
        if namefilter:
            inst = inst.filter(institution_name__icontains=namefilter)
        return inst


    @action(detail=False, methods=['get'])
    def jahresbeitrag_anlegen(self, request):
        d = request.query_params.get('jahr')
        if d:
            year = int(d)
            ii = Institution.aktive.exclude(mitgliedsart__mitart__in=["AD"]).filter(kostenart__art__in=["M"])

            for inst in ii:
                o = offenePosten()
                o = offenePosten(institution=inst, description="Beitrag {}".format(year), offen=65, bezahlt=False, erstellt=datetime.datetime.now())
                o.save()

            message = 'Der Beitrag "{}" wurde {} x erfolgreich angelegt!'.format(d, ii.count())
            return Response(data=message, status=status.HTTP_200_OK)
        return Response(data="Sie haben ein leeres Feld übergeben.", status=status.HTTP_406_NOT_ACCEPTABLE)


    @action(detail=False, methods=['get'])
    def erlagscheine_anlegen(self, request):
        merged_filename = '/tmp/merged_inst_pdf.pdf'
        ii = Institution.aktive.all()
        ii = Institution.aktive.exclude(mitgliedsart__mitart__in=["AD", "DA"]).filter(kostenart__art__in=["M"])

        insts = [i for i in ii if i.offeneposten_set.filter(bezahlt=False)] 
        # vms = vms[0:5]
        if insts:
            for inst in insts:
                news = """
                Liebe OVG Mitglieder,<br /><br />

                wir dürfen ihnen die Mitgliedsbeiträge für die Jahre 2025 und 2026 vorschreiben und uns recht herzlich für ihre treue Unterstützung der OVG bedanken. Darüber hinaus ersuchen wir sie ihre hinterlegte Emailadresse zu kontrollieren: {}<br />
                Sollte diese Emailadresse nicht korrekt sein, ersuchen wir sie uns das per Email unter office@ovg.at mitzuteilen. <br /><br />
            
                Sollten sich ihre Kontaktdaten ändern, bitte Email an office@ovg.at.
                Beste Grüße<br />
                Ihre OVG<br /><br />

                PS. Sichern Sie sich eine Kongresskarte für den OVG.Summit #Geodät:innentag unter https://www.summit.ovg.at/ <br />
                PPS: Werfen Sie einen Blick auf unseren neuen OVG.Award unter https://www.summit.ovg.at/ovg-award/<br />
                PPPS: Wir ersuchen um Einzahlung des ausständigen Betrages bis Ende März<br />
                2026. Bei Telebanking bitte als Zahlungsreferenz „{}/2026“ angeben.<br />
                """.format(inst.email, inst.mitgliedsnummer)
                make_invoice(inst, news)

            pfade = [inst.rechnung.path for inst in insts]
            merger(merged_filename, pfade)

            response = FileResponse(open(merged_filename, 'rb'), content_type='application/pdf', status=status.HTTP_200_OK)
            response['Content-Disposition'] = 'inline; filename="erlagscheine_institutionen.pdf"'
            return response



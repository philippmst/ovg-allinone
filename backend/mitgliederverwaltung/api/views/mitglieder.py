import os
import shutil
import uuid
from datetime import datetime as dt

from django.db.models import Q
from django.http import FileResponse

from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework import viewsets, status


from mitglieder.models import VereinsMitglied, offenePosten
from mitglieder.models import offenePosten
from api.serializers import VereinsMitgliedSerializer
from invoice.anniversary import create_anniversary
from .helpers import MyMetaData, make_invoice, merger, sendmail


class VereinsMitgliedViewSet(viewsets.ModelViewSet):
    queryset = VereinsMitglied.objects.all()
    serializer_class = VereinsMitgliedSerializer
    metadata_class = MyMetaData


    def get_queryset(self):
        if 'aktiv' in self.request.GET:
            vm = VereinsMitglied.aktive.all()
        else:
            vm = VereinsMitglied.objects.all()

        if 'key' in self.request.GET and 'value' in self.request.GET:
            kwargs = {'{}'.format(self.request.GET['key']): self.request.GET['value'] }
            vm = vm.filter(**kwargs)

        namefilter = self.request.query_params.get('namefilter')
        if namefilter:
            vm = vm.filter(Q(last_name__icontains=namefilter) | Q(first_name__icontains=namefilter))
        return vm


    @action(detail=True, methods=['post'])
    def create_invoice(self, request, pk=None):
        news = ""
        if 'zahlscheinText' in request.data:
            news = request.data['zahlscheinText'].replace("<br>", "<br />")
        vm =self.get_object()
        if vm.aktiv and vm.offeneposten_set.filter(bezahlt=False):
            if not vm.rechnungsadresse:
                error = 'Ohne Rechnungsadresse kann kein Zahlschein ausgestellt werden.'
                return Response(data=error, status=status.HTTP_400_BAD_REQUEST)
            news = 'Aufgrund von Umstellungsarbeiten der Mitgliedsdatenbank können wir den Mitgliedsbeitrag 2019 erst jetzt aussenden. Der Einfachheit halber schicken wir auch gleich jenen von 2020. Wir danken für Ihre Unterstützung und Ihre True zur OVG.'
            x = make_invoice(vm, news=news)
            fname = '/tmp/invoice_{}'.format(vm.id)
            f = open(fname, 'wb')
            f.write(x)
            f.close()

            return FileResponse(open(fname, 'rb'))
        else:
            return Response(data="Das Mitglied ist inaktiv oder es gibt keine offenen Posten.", status=status.HTTP_204_NO_CONTENT)


    @action(detail=True, methods=['post'])
    def send_mail(self, request, pk=None):
        zahlscheinText = ""
        if 'zahlscheinText' in request.data:
            zahlscheinText = request.data['zahlscheinText'].replace("<br>", "<br />")
        emailText = ""
        if 'emailText' in request.data:
            emailText = request.data['emailText']

        print("emailText: {}".format(emailText))
        print("zahlscheinText: {}".format(zahlscheinText))
        vm =self.get_object()
        zahlscheinText = 'Aufgrund von Umstellungsarbeiten der Mitgliedsdatenbank können wir den Mitgliedsbeitrag 2019 erst jetzt aussenden. Der Einfachheit halber schicken wir auch gleich jenen von 2020. Wir danken für Ihre Unterstützung und Ihre True zur OVG.'
        x = make_invoice(vm, news=zahlscheinText)
        s = sendmail(vm, content=emailText)
        return HttpResponse("das war ok")


    @action(detail=False, methods=['get'])
    def jahresbeitrag_anlegen(self, request):
        d = request.query_params.get('jahr')
        hauspost = request.query_params.get('hauspost')

        if d:
            year = int(d)
            stud_gebjahr = year-30
            vms = VereinsMitglied.aktive.filter(kostenart__art="M")
            if hauspost == 'true': 
                vms = vms.filter(versand__iexact='BEV')
            else:
                vms = vms.filter(versand__iexact='POST')

            juniors = vms.filter(gebdat__year__gt=stud_gebjahr)
            for m in juniors:
                o = offenePosten(mitglied=m, description="Beitrag {}".format(d), offen=20, bezahlt=False, erstellt=dt.now())
                o.save()

            seniors = vms.filter(gebdat__year__lt=1943)
            for m in seniors:
                o = offenePosten(mitglied=m, description="Beitrag {}".format(d), offen=35, bezahlt=False, erstellt=dt.now())
                o.save()

            normale = vms.exclude(id__in=[s.id for s in seniors]).exclude(id__in=[j.id for j in juniors])
            for m in normale:
                o = offenePosten(mitglied=m, description="Beitrag {}".format(d), offen=65, bezahlt=False, erstellt=dt.now())
                o.save()

            message = 'Der Beitrag "{}" wurde {} x erfolgreich angelegt!'.format(d, vms.count())
            return Response(data=message, status=status.HTTP_200_OK)
        return Response(data="Sie haben ein leeres Feld übergeben.", status=status.HTTP_406_NOT_ACCEPTABLE)


    @action(detail=False, methods=['get'])
    def erlagscheine_anlegen(self, request):
        hauspost = request.query_params.get('hauspost')
        merged_filename = '/tmp/merged_pdf.pdf'
        v = VereinsMitglied.aktive.filter(kostenart__art='M')
        if hauspost == 'true':
            v = v.filter(versand__iexact='BEV')
        else:
            v = v.filter(versand__iexact='POST')
        vms = [vm for vm in v if vm.offeneposten_set.filter(bezahlt=False)] 

        # vms = vms[0:5]
        if vms:
            for vm in vms:
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
                """.format(vm.email, vm.mitgliedsnummer)
                make_invoice(vm, news=news)

            pfade = [vm.rechnung.path for vm in vms]
            merger(merged_filename, pfade)

            response = FileResponse(open(merged_filename, 'rb'), content_type='application/pdf', status=status.HTTP_200_OK)
            response['Content-Disposition'] = 'inline; filename="erlagscheine.pdf"'
            return response


    @action(detail=False, methods=['get'])
    def jubilare_csv(self, request):
        out = 'Ater,Titel,Vorname,Nachname,Ort,Geburtsdatum\n'
        d = request.query_params.get('jahr')
        if d:
            year=int(d)
            jubls=[50,60,70,75,80,85,90,95]
            vms=VereinsMitglied.aktive.order_by('gebdat').filter(gebdat__isnull=False)
            for m in vms:
                m.alter=year-m.gebdat.year
                if m.alter in jubls or m.alter>99:
                    out += '{},{},{},{},{},{}\n'.format(m.alter, m.titel, m.first_name, m.last_name, m.wohnadresse.ort, m.gebdat)
            return Response(data=out, status=status.HTTP_200_OK)
        return Response(data="Sie haben kein gültiges Jahr übergeben.", status=status.HTTP_406_NOT_ACCEPTABLE)


    @action(detail=False, methods=['get'])
    def jubilare_pdf(self, request):
        d = request.query_params.get('jahr')
        if d:
            year=int(d)
            jubls=[50,60,70,75,80,85,90,95]
            merged_filename = 'jubilare.pdf'
            folder = str(uuid.uuid4())
            path = '/tmp/{}'.format(folder)
            os.mkdir(path)
            os.chdir(path)
    
            vms=VereinsMitglied.aktive.order_by('gebdat').filter(gebdat__isnull=False)
            for m in vms:
                m.alter=year-m.gebdat.year
                if m.alter in jubls or m.alter>99:
                    greetings = 'Lieber Jubilar'
                    salutation = 'Lieber'
                    if m.anrede == 'Frau':
                        greetings = 'Liebe Jubilarin'
                        salutation = 'Liebe'
                    mm = {'letter_date': m.gebdat.replace(year=year).isoformat(), 'customer_salutation': salutation, 
                        'customer_name': '{} {}'.format(m.first_name, m.last_name),
                        'customer_id': m.mitgliedsnummer, 'customer_anniversary': m.alter,
                        'letter_street': m.wohnadresse.strasse, 'letter_zip': m.wohnadresse.plz,
                        'letter_city': m.wohnadresse.ort, 'letter_country': m.wohnadresse.country.land,
                        'greetings': greetings,
                         }
                   
                    x = create_anniversary(**mm)
                    fname = str(uuid.uuid4())
                    f = open(fname, 'wb')
                    f.write(x)
                    f.close()

            pfade = os.listdir(path)
            merger(merged_filename, pfade)
            fname = path + "/" + merged_filename

            response = FileResponse(open(fname, 'rb'), content_type='application/pdf', status=status.HTTP_200_OK)
            shutil.rmtree(path)
            response['Content-Disposition'] = 'inline; filename="jubilare.pdf"'
            return response
        return Response(data="Sie haben kein gültiges Jahr übergeben.", status=status.HTTP_406_NOT_ACCEPTABLE)



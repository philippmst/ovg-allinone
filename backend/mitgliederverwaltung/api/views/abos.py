


from django.db.models import Q
from django.http import HttpResponse, FileResponse


from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework import viewsets, status



from mitglieder.models import VereinsMitglied, Land, Institution
from mitglieder.models import AboHeft, Abonnent, offeneAboPosten
from api.serializers import AboHeftSerializer, AbonnentSerializer, offeneAboPostenSerializer

from .helpers import MyMetaData, sendmail, make_abo_invoice, make_etiketten, merger






class OffeneAboPostenViewSet(viewsets.ModelViewSet):
    queryset = offeneAboPosten.objects.all()
    serializer_class = offeneAboPostenSerializer
    metadata_class = MyMetaData




class AbonnentViewSet(viewsets.ModelViewSet):
    queryset = Abonnent.objects.all()
    serializer_class = AbonnentSerializer
    metadata_class = MyMetaData

    def get_queryset(self):
        if 'aktiv' in self.request. GET:
            abos = Abonnent.aktive.all()
        else:
            abos = Abonnent.objects.all()

        if 'key' in self.request.GET and 'value' in self.request.GET:
            kwargs = {'{}'.format(self.request.GET['key']): self.request.GET['value'] }
            abos = abos.filter(**kwargs)

        namefilter = self.request.query_params.get('namefilter')
        if namefilter:
            abos = abos.filter(Q(name__icontains=namefilter) | Q(name2__icontains=namefilter) | Q(aboheft__nachname__icontains=namefilter))
        return abos


    @action(detail=True, methods=['get'])
    def create_invoice(self, request, pk=None):
        vm =self.get_object()
        x = make_abo_invoice(vm)
        return HttpResponse(x)

    @action(detail=True, methods=['get'])
    def add_aboheft(self, request, pk=None):
        vm = self.get_object()
        maxnr = max([a.abonummer for a in AboHeft.objects.all()])
        h = AboHeft(abonummer=maxnr+1, kundennummer=vm)
        h.save()
        return HttpResponse("neues AboHeft angelegt")


    @action(detail=True, methods=['get'])
    def send_mail(self, request, pk=None):
        vm =self.get_object()
        x = make_abo_invoice(vm)
        s = sendmail(vm)
        return HttpResponse("das war ok")

    @action(detail=False, methods=['get'])
    def etiketten(self, request):
        if 'wohin' in self.request.GET:
            wohin = self.request.GET['wohin']
            if wohin in ['BEV', 'AUT', 'INT']:
                vms = VereinsMitglied.aktive.all().filter(heftanzahl__gt=0).order_by('lieferadresse__plz')
                abos = AboHeft.objects.filter(aboende__isnull=True).order_by('plz')
                inst = Institution.aktive.all().order_by('lieferadresse__plz')

                if wohin == 'BEV':
                    vms = vms.filter(versand__iexact='BEV')
                    abos = []
                    inst = inst.filter(versand__iexact='BEV')
                else:
                    vms = vms.filter(versand__iexact='POST')
                    inst = inst.filter(versand__iexact='POST')
                    l = Land.objects.filter(land='AUSTRIA')

                    if wohin == 'AUT':
                        vms = vms.filter(lieferadresse__country__in=l).order_by('lieferadresse__plz')
                        abos = abos.filter(country__in=l).order_by('plz')
                        inst = inst.filter(lieferadresse__country__in=l).order_by('lieferadresse__plz')
                    elif wohin == 'INT':
                        vms = vms.exclude(lieferadresse__country__in=l)
                        abos = abos.exclude(country__in=l)
                        inst = inst.exclude(lieferadresse__country__in=l)
                
                if 'plz' in self.request.GET:
                    vms_plz = [vm.lieferadresse.plz for vm in vms]
                    inst_plz = [ins.lieferadresse.plz for ins in inst]
                    abos_plz = [abo.plz for abo in abos]
                    x = "\n".join(vms_plz + inst_plz + abos_plz)
                    f = open('/tmp/plz.csv', 'w')
                    f.write(x)
                    f.close()
                    f = open('/tmp/plz.csv')
                    pdf = f.read()
                    f.close()
                else:
                    pdf = make_etiketten(vms, abos, inst, wohin)
                if abos:
                    print("\n\n\nEs waren insgesamt {} abos".format(abos.count()))
            
                response = FileResponse(pdf, content_type='application/pdf', status=status.HTTP_200_OK)
                response['Content-Disposition'] = 'inline; filename="jubilare.pdf"'
                return response

        return Response(data="Sie haben keinen gültigen <<WOHIN>> Wert übergeben.", status=status.HTTP_406_NOT_ACCEPTABLE)








class AboHeftViewSet(viewsets.ModelViewSet):
    queryset = AboHeft.objects.all()
    serializer_class = AboHeftSerializer
    metadata_class = MyMetaData

    def get_queryset(self):
        if 'aktiv' in self.request.GET:
            abos = AboHeft.objects.filter(aboende__isnull=True)
        else:
            abos = AboHeft.objects.all()
        if 'wer' in self.request.GET:
            abos = abos.filter(Q(name__icontains=self.request.GET['wer']))
        return abos

    @action(detail=True, methods=['get'])
    def create_invoice(self, request, pk=None):
        h = self.get_object()
        x = make_abo_invoice(h)
        return HttpResponse(x)
   
    @action(detail=False, methods=['get'])
    def jahresbeitrag_anlegen(self, request):
        d = request.query_params.get('jahr')
        if d:
            year = int(d)
            i = 0
            for a in Abonnent.aktive.all():
                for heft in a.aboheft_set.all():
                    if heft.aktiv:
                        oap = offeneAboPosten(aboheft=heft)
                        if heft.country.land.lower() == 'austria':
                            oap.offen = 70 * heft.heftanzahl
                        else:
                            oap.offen = 90 * heft.heftanzahl
                        oap.description = 'Abonnement ' + d
                        oap.save()
                        i += 1
                  
            message = 'Der Beitrag wurde {} x erfolgreich angelegt!'.format(i)
            return Response(data=message, status=status.HTTP_200_OK)
        return Response(data="Sie haben ein leeres Feld übergeben.", status=status.HTTP_406_NOT_ACCEPTABLE)


    @action(detail=False, methods=['get'])
    def erlagscheine_anlegen(self, request):
        merged_filename = '/tmp/merged_abo_pdf.pdf'
        # abos = Abonnent.aktive.all()
        abos = AboHeft.objects.filter(aboende__isnull=True)
        if abos:
            for abo in abos:
                x = make_abo_invoice(abo)

            pfade = [abo.rechnung.path for abo in abos]
            merger(merged_filename, pfade)

            response = FileResponse(open(merged_filename, 'rb'), content_type='application/pdf', status=status.HTTP_200_OK)
            response['Content-Disposition'] = 'inline; filename="jubilare.pdf"'
            return response
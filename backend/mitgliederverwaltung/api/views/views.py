
import datetime
from datetime import datetime as dt

from django.contrib.auth.models import User, Group
from django.http import JsonResponse
from django.db.models import Q
from knox.models import AuthToken

from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework import viewsets, generics, status
from rest_framework.permissions import AllowAny


from mitglieder.models import VereinsMitglied, offenePosten, Land, Beruf, Mitgliedsart, Kosten, Vortragsort, Adresse, Institution
from mitglieder.models import offenePosten, AboHeft, Abonnent
from api.serializers import UserSerializer, GroupSerializer, CountrySerializer, BerufeSerializer, MitgliedsartSerializer
from api.serializers import KostenSerializer, VortragsortSerializer, AdresseSerializer
from api.serializers import offenePostenSerializer, CreateUserSerializer, LoginUserSerializer

from .helpers import MyMetaData


class UserAPI(generics.RetrieveAPIView):
    serializer_class = UserSerializer

    def get_object(self):
        return self.request.user


class LoginAPI(generics.GenericAPIView):
    permission_classes = [AllowAny, ]
    serializer_class = LoginUserSerializer

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        if not serializer.is_valid():
            return Response(status=status.HTTP_401_UNAUTHORIZED)
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data
        return Response({
            "user": UserSerializer(user, context=self.get_serializer_context()).data,
            "token": AuthToken.objects.create(user)[1]
        })


class RegistrationAPI(generics.GenericAPIView):
    serializer_class = CreateUserSerializer

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        return Response({
            "user": UserSerializer(user, context=self.get_serializer_context()).data,
            "token": AuthToken.objects.create(user)
        })


class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all().order_by('-date_joined')
    serializer_class = UserSerializer


class GroupViewSet(viewsets.ModelViewSet):
    queryset = Group.objects.all()
    serializer_class = GroupSerializer


class CountryViewSet(viewsets.ModelViewSet):
    queryset = Land.objects.all().order_by('land')
    serializer_class = CountrySerializer


class BerufeViewSet(viewsets.ModelViewSet):
    queryset = Beruf.objects.order_by('bezeichnung')
    serializer_class = BerufeSerializer


class MitgliedsartViewSet(viewsets.ModelViewSet):
    queryset = Mitgliedsart.objects.all()
    serializer_class = MitgliedsartSerializer


class KostenViewSet(viewsets.ModelViewSet):
    queryset = Kosten.objects.all()
    serializer_class = KostenSerializer


class VortragsortViewSet(viewsets.ModelViewSet):
    queryset = Vortragsort.objects.all()
    serializer_class = VortragsortSerializer


class AdresseViewSet(viewsets.ModelViewSet):
    queryset = Adresse.objects.all()
    serializer_class = AdresseSerializer
    metadata_class = MyMetaData


class offenePostenViewSet(viewsets.ModelViewSet):
    queryset = offenePosten.objects.all()
    serializer_class = offenePostenSerializer
    metadata_class = MyMetaData

    def get_queryset(self):
        ops = offenePosten.objects.all()
        if 'offen' in self.request.GET:
            ops = ops.filter(bezahlt=False)

        namefilter = self.request.query_params.get('namefilter')
        if namefilter:
            ops = ops.filter(Q(description__icontains=namefilter) | Q(mitglied__first_name__icontains=namefilter) | Q(mitglied__last_name__icontains=namefilter))
        #return ops.filter(mitglied__isnull=False).filter(mitglied__in=VereinsMitglied.aktive.all())
        return ops


    @action(detail=True, methods=['get'])
    def set_bezahlt(self, request, pk=None):
        op =self.get_object()
        op.bezahlt = True
        op.bezahlt_am = datetime.datetime.now()
        op.zahlung = op.offen
        op.save()
        serializer = offenePostenSerializer(op, context={'request': request})
        return Response(data=serializer.data, status=status.HTTP_200_OK)


def dashboard(request):
    year=dt.now().year
    if 'jahr' in request.GET:
        year=int(request.GET['jahr'])
    mm=VereinsMitglied.aktive.order_by('gebdat').filter(gebdat__isnull=False)
    for m in mm:
        m.alter=year-m.gebdat.year
    jubls=[50,60,70,75,80,85,90,95]
    jubilare=[{'alter': m.alter, 'first_name': m.first_name, 'last_name': m.last_name, 'gebdat': m.gebdat, 'monat': m.gebdat.month} for m in mm if m.alter in jubls or m.alter>99]
    oo=offenePosten.objects.filter(bezahlt=False).filter(mitglied__isnull=False).filter(mitglied__in=VereinsMitglied.aktive.all())
    summe=0
    for o in oo:
        if o.offen:
            summe=summe+o.offen
    context = { 'offenerbetrag': int(summe*100)/100, 
                'abonnentcount': {'aktiv': Abonnent.aktive.count(), 'inaktiv': Abonnent.objects.count() - Abonnent.aktive.count()}, 'aboheftcount': AboHeft.objects.count(),
                'mitgliedercount': {'aktiv': VereinsMitglied.aktive.count(), 'inaktiv': VereinsMitglied.objects.filter(storndat__isnull=False).count()}, 
                'institutionencount': {'aktiv': Institution.objects.filter(storndat__isnull=True).count(), 'inaktiv': Institution.objects.filter(storndat__isnull=False).count() },
                'jubilare': jubilare, 'kosten': Kosten.objects.count(), 'mitgliedsarten': Mitgliedsart.objects.count(), 'berufecount': Beruf.objects.count(), 'laendercount': Land.objects.count() }
    return JsonResponse(context)


"""
def pdf(request, was):
    vms = VereinsMitglied.aktive.filter(heftanzahl>0)
    if was == "hauspost":
        bevler = vms.filter(versand='BEV')
        makepdfs('hauspost_vorlage.tex', 'hauspost', bevler)
    
    vms = vms.filter(versand='POST')
    if was == "austria":
        l = Land.objects.filter(land='AUSTRIA')
        austria = vms.filter(wohnadresse__country__in=l).order_by('plz')
        makepdfs('austria_vorlage.tex', 'austria', austria)

    if was == "europa":
        l=Land.objects.filter(EU=True).exclude(land='AUSTRIA')
        europa = vms.filter(wohnadresse__country__in=l)
        makepdfs('europa_vorlage.tex', 'europa', europa)

    if was == "international":
        l = Land.objects.filter(EU=False)
        international=vms.filter(wohnadresse__country__in=l)

    return render(request, 'mitglieder/vgiuebersicht.html', context)
"""
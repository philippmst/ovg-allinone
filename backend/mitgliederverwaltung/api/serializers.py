from django.contrib.auth.models import User, Group
from django.contrib.auth import authenticate

from rest_framework import serializers

from mitglieder.models import VereinsMitglied, Land, Beruf, Mitgliedsart, Kosten, Vortragsort, Adresse, Institution, offenePosten
from mitglieder.models import AboHeft, Abonnent, offeneAboPosten

# Serializers define the API representation.


class LoginUserSerializer(serializers.Serializer):
    username = serializers.CharField()
    password = serializers.CharField()

    def validate(self, data):
        user = authenticate(**data)
        if user and user.is_active:
            return user
        raise serializers.ValidationError("Unable to log in with provided credentials.")


class CreateUserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ('id', 'username', 'password', )
        extra_kwargs = {'password': {'write_only': True }}

    def create(self, validated_data):
        user = User.objects.create_user(validated_data['username'], None, validated_data['password'])
        return user


class UserSerializer(serializers.HyperlinkedModelSerializer):
    groups = serializers.StringRelatedField(many=True)

    class Meta:
        model = User
        #fields = '__all__'
        fields = ('url', 'username', 'email', 'id', 'groups', 'is_superuser', 'is_active', 'is_staff', 'date_joined', 'last_login' )
        read_only_fields = ('date_joined', 'last_login')


class BerufeSerializer(serializers.HyperlinkedModelSerializer):
    vereinsmitglied_inactive_count = serializers.SerializerMethodField('get_inactive_members_count')
    vereinsmitglied_count = serializers.SerializerMethodField('get_members_count')
    institution_inactive_count = serializers.SerializerMethodField('get_inactive_inst_count')
    institution_count = serializers.SerializerMethodField('get_inst_count')

    def get_inactive_members_count(self, id):
        return VereinsMitglied.objects.filter(storndat__isnull=False).filter(berufsgruppe=id).count()

    def get_members_count(self, id):
        return VereinsMitglied.aktive.all().filter(berufsgruppe=id).count()

    def get_inst_count(self, id):
        return Institution.aktive.all().filter(berufsgruppe=id).count()

    def get_inactive_inst_count(self, id):
        return Institution.objects.filter(storndat__isnull=False).filter(berufsgruppe=id).count()

    class Meta:
        model = Beruf
        fields = ('url', 'id', 'beruf', 'bezeichnung', 
                     'vereinsmitglied_count', 'vereinsmitglied_inactive_count', 'institution_count', 'institution_inactive_count',
        )
        read_only_fields = ('id', )


class GroupSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = Group
        fields = ('url', 'name')


class MitgliedsartSerializer(serializers.HyperlinkedModelSerializer):
    vereinsmitglied_inactive_count = serializers.SerializerMethodField('get_inactive_members_count')
    vereinsmitglied_count = serializers.SerializerMethodField('get_members_count')
    institution_inactive_count = serializers.SerializerMethodField('get_inactive_inst_count')
    institution_count = serializers.SerializerMethodField('get_inst_count')

    def get_inactive_members_count(self, id):
        return VereinsMitglied.objects.filter(storndat__isnull=False).filter(mitgliedsart=id).count()

    def get_members_count(self, id):
        return VereinsMitglied.aktive.all().filter(mitgliedsart=id).count()

    def get_inst_count(self, id):
        return Institution.aktive.all().filter(mitgliedsart=id).count()

    def get_inactive_inst_count(self, id):
        return Institution.objects.filter(storndat__isnull=False).filter(mitgliedsart=id).count()

    class Meta:
        model = Mitgliedsart
        fields = ('id', 'url', 'mitart', 'bezeichnung', 'anmerkung',
             'vereinsmitglied_count', 'vereinsmitglied_inactive_count', 'institution_count', 'institution_inactive_count',
             )
        read_only_fields = ('id', 'vereinsmitglied_count', 'institution_count', 'vereinsmitglied_inactive_count', 'institution_inactive_count')


class KostenSerializer(serializers.HyperlinkedModelSerializer):
    vereinsmitglied_inactive_count = serializers.SerializerMethodField('get_inactive_members_count')
    vereinsmitglied_count = serializers.SerializerMethodField('get_members_count')
    institution_inactive_count = serializers.SerializerMethodField('get_inactive_inst_count')
    institution_count = serializers.SerializerMethodField('get_inst_count')

    def get_inactive_members_count(self, id):
        return VereinsMitglied.objects.filter(storndat__isnull=False).filter(kostenart=id).count()

    def get_members_count(self, id):
        return VereinsMitglied.aktive.all().filter(kostenart=id).count()

    def get_inst_count(self, id):
        return Institution.aktive.all().filter(kostenart=id).count()

    def get_inactive_inst_count(self, id):
        return Institution.objects.filter(storndat__isnull=False).filter(kostenart=id).count()

    class Meta:
        model = Kosten
        fields = ('id', 'url', 'art', 'bezeichnung', 'betrag',
             'vereinsmitglied_count', 'vereinsmitglied_inactive_count', 'institution_count', 'institution_inactive_count',
         )
        read_only_fields = ('id',)


class VortragsortSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = Vortragsort
        fields = '__all__'


class AdresseSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = Adresse
        fields = '__all__'


class offeneAboPostenSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = offeneAboPosten
        fields = '__all__'


class AboHeftSerializer(serializers.HyperlinkedModelSerializer):
    aktiv = serializers.ReadOnlyField()
    id = serializers.ReadOnlyField()
    abonnent_id = serializers.ReadOnlyField(source='kundennummer.id')
    abonnent_name = serializers.ReadOnlyField(source='kundennummer.name')
    offeneaboposten_set = offeneAboPostenSerializer(many=True, read_only=True)
    prozent = serializers.SerializerMethodField()

    def get_prozent(self, obj):
        return obj.kundennummer.prozent
    class Meta:
        model = AboHeft
        fields = ('id', 'aboanfang', 'aboart', 'aboende', 'abonnent_id', 'abonnent_name', 'abonummer', 'aktiv', 'anmerkung',
		'anrede', 'beidat', 'beigz', 'country', 'fax', 'gutschrift', 'heftanzahl', 'kundennummer', 'nachname', 'offeneaboposten_set',
		'ort', 'plz', 'pobox', 'prozent', 'rueckstand', 'storndat', 'strasse', 'surname2', 'surname3', 'tel', 'titel',
		'url', 'vorname', )
        # fields = '__all__'


class offenePostenSerializer(serializers.HyperlinkedModelSerializer):
    id = serializers.ReadOnlyField(source='mitglied.id')
    mnr = serializers.ReadOnlyField(source='mitglied.mitgliedsnummer')
    # name = serializers.ReadOnlyField(source='mitglied.last_name')
    name = serializers.SerializerMethodField('get_mitglied_name')

    def get_mitglied_name(self, obj):
        if obj.mitglied:
            return "{} {}".format(obj.mitglied.first_name, obj.mitglied.last_name)
        return ""

    class Meta:
        model = offenePosten
        fields = ('id', 'mnr', 'url', 'mitglied', 'erstellt', 'bezahltam', 'offen', 'zahlung', 'bezahlt', 'description', 'name')
        read_only_fields = ('url', )


class AbonnentSerializer(serializers.HyperlinkedModelSerializer):
    aboheft_set = AboHeftSerializer(many=True, read_only=True)

    class Meta:
        model = Abonnent
        # fields = '__all__'
        fields = ('id', 'url', 'kundennummer', 'titel', 'name', 'name2', 'name3', 'tel', 'fax', 'uid', 'prozent',
                    'rechnungsanzahl', 'dsgvo', 'email', 'rechnungsanschrift', 'aboheft_set', 'heftsum', 'aktiv', 'inaktiv')
        read_only_fields = ('id', 'url', 'kundennummer', 'heftsum', 'aktiv', 'inaktiv')


class VereinsMitgliedSerializer(serializers.HyperlinkedModelSerializer):
    # groups = serializers.StringRelatedField(many=True)
    wohnadresse  = AdresseSerializer
    lieferadresse = AdresseSerializer
    rechnungsadresse = AdresseSerializer

    def create(self, validated_data):
        vortrag = validated_data.pop('vortrag')
        mnr = VereinsMitglied.objects.filter(mitgliedsnummer__lt=99998).order_by('-mitgliedsnummer').first().mitgliedsnummer + 1
        validated_data['mitgliedsnummer'] = mnr
        vm = VereinsMitglied.objects.create(**validated_data)
        if vortrag != []:
            vm.vortrag.set(vortrag)
            vm.save()
        return vm

    class Meta:
        model = VereinsMitglied
        # fields = '__all__'
        fields = ('wohnadresse', 'lieferadresse', 'rechnungsadresse', 'email', 'url', 'id', 'mitgliedsnummer',
                    'first_name', 'anrede', 'titel', 'last_name', 'namenszusatz', 'tel', 'fax', 'aktiv',
                    'beigz', 'beidat', 'storndat', 'mitgliedsart', 'kostenart', 'versand', 'gebdat', 'dsgvo', 'offeneposten_set',
                    'diplomdat', 'diplomort', 'sub', 'berufsgruppe', 'heftanzahl', 'anmerkung', 'offenerbetrag', 'vortrag',
                    'username', 'groups', 'is_superuser', 'is_active', 'is_staff', 'date_joined', 'last_login' )
        read_only_fields = ('date_joined', 'last_login', 'offeneposten_set',)


class InstitutionenSerializer(serializers.HyperlinkedModelSerializer):
    wohnadresse  = AdresseSerializer
    lieferadresse = AdresseSerializer
    rechnungsadresse = AdresseSerializer

    class Meta:
        model = Institution
        fields = ('wohnadresse', 'lieferadresse', 'rechnungsadresse', 'email', 'url', 'id', 'mitgliedsnummer', 
                    'institution_name', 'name2', 'name3', 'tel', 'fax', 'homepage', 'offeneposten_set',
                    'beigz', 'beidat', 'storndat', 'mitgliedsart', 'kostenart', 'versand', 'dsgvo',
                    'sub', 'berufsgruppe', 'heftanzahl', 'anmerkung', 'aktiv')
        read_only_fields = ('offeneposten_set',)
  

class CountrySerializer(serializers.HyperlinkedModelSerializer):
    vereinsmitglied_inactive_count = serializers.SerializerMethodField('get_inactive_members_count')
    vereinsmitglied_count = serializers.SerializerMethodField('get_members_count')
    institution_inactive_count = serializers.SerializerMethodField('get_inactive_inst_count')
    institution_count = serializers.SerializerMethodField('get_inst_count')

    def get_members_count(self, land):
        return VereinsMitglied.aktive.filter(wohnadresse__country__land=land.land).count()

    def get_inst_count(self, land):
        return Institution.aktive.filter(wohnadresse__country__land=land.land).count() 

    def get_inactive_members_count(self, land):
        return VereinsMitglied.objects.filter(wohnadresse__country__land=land.land).filter(storndat__isnull=False).count()

    def get_inactive_inst_count(self, land):
        return Institution.objects.filter(wohnadresse__country__land=land.land).filter(storndat__isnull=False).count() 

    class Meta:
        model = Land
        fields = ('url', 'id', 'land', 'iso', 'EU',
             'vereinsmitglied_count', 'vereinsmitglied_inactive_count', 'institution_count', 'institution_inactive_count',
          )
        read_only_fields = ('id', )

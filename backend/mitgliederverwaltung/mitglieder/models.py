from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
import uuid
from django.db.models import Sum
# Create your models here.


class AktivMitgliedManager(models.Manager):
    def get_queryset(self):
        return super().get_queryset().filter(storndat__isnull=True)


class AktivAbonnentManager(models.Manager):
    def get_queryset(self):
        # elf.aboheft_set.filter(aboende__isnull=True).count() > 0:
        hefte = AboHeft.objects.filter(aboende__isnull=True)
        #return super().get_queryset().filter(aktiv=True)
        return super().get_queryset().filter(aboheft__in=hefte).distinct()


class Land(models.Model):
    land = models.CharField(max_length=100)
    iso = models.CharField(max_length=4)
    EU = models.BooleanField(default=True)
    oldid = models.IntegerField()
    
    def __str__(self):
        return self.land


class Beruf(models.Model):
    beruf = models.CharField(max_length=100)
    bezeichnung = models.CharField(max_length=100)
    oldid = models.IntegerField()
    
    def __str__(self):
        return self.bezeichnung

    class Meta:
        ordering = ['beruf']


class Titel(models.Model):
    titel = models.CharField(max_length=100)
    oldid = models.IntegerField()


class Anrede(models.Model):
    anrede=models.CharField(max_length=100)
    oldid=models.IntegerField()


class Mitgliedsart(models.Model):
    mitart = models.CharField(max_length=3)
    bezeichnung = models.CharField(max_length=100)
    anmerkung = models.CharField(max_length=1000)
    
    def __str__(self):
        return self.bezeichnung

    class Meta:
        ordering = ['mitart']


class Kosten(models.Model):
    art = models.CharField(max_length=3)
    bezeichnung = models.CharField(max_length=100)
    betrag = models.FloatField(default=0.0, null=True, blank=True)
    
    def __str__(self):
        return self.bezeichnung

    class Meta:
        ordering = ['art']


class Versand(models.Model):
    versand = models.CharField(max_length=3)
    bezeichnung = models.CharField(max_length=100)


class Vortragold(models.Model):
    oldid = models.IntegerField()
    Vortragsort = models.CharField(max_length=10)
    
    def __str__(self):
        return self.Vortragsort


class Vortragsort(models.Model):
    Vortragsort = models.CharField(max_length=20)
    
    def __str__(self):
        return self.Vortragsort


class Adresse(models.Model):
    pobox = models.IntegerField(blank=True, null=True)
    strasse = models.CharField(max_length=100,blank=True, null=True)
    plz = models.CharField(max_length=20,blank=True, null=True)
    ort = models.CharField(max_length=100,blank=True, null=True)
    country = models.ForeignKey(Land,blank=True, null=True, on_delete=models.DO_NOTHING)


class Institution(models.Model):
    mitgliedsnummer = models.IntegerField()
    institution_name = models.CharField(max_length=100,blank=True, null=True)
    name2 = models.CharField(max_length=100,blank=True, null=True)
    name3 = models.CharField(max_length=100,blank=True, null=True)
    tel = models.CharField(max_length=100,blank=True, null=True)
    fax = models.CharField(max_length=100,blank=True, null=True)
    email = models.CharField(max_length=100,blank=True, null=True)
    homepage = models.CharField(max_length=100,blank=True, null=True)
    beigz = models.CharField(max_length=20,blank=True, null=True)
    beidat = models.DateField(blank=True, null=True)
    storndat = models.DateField(blank=True, null=True)       
    mitgliedsart = models.ForeignKey(Mitgliedsart,blank=True, null=True, on_delete=models.DO_NOTHING)       
    kostenart = models.ForeignKey(Kosten,blank=True, null=True, on_delete=models.DO_NOTHING)       
    versand = models.CharField(max_length=20,blank=True, null=True)       
    sub = models.CharField(max_length=10, blank=True, null=True)       
    vortrag = models.ManyToManyField(Vortragsort)       
    berufsgruppe = models.ForeignKey(Beruf, blank=True, null=True,default=0, on_delete=models.DO_NOTHING)
    heftanzahl = models.IntegerField(null=False, blank=False, default=0)       
    anmerkung = models.TextField(null=True, blank=True)       
    wohnadresse = models.ForeignKey(Adresse, on_delete=models.DO_NOTHING, related_name='Wohnadresse2')
    lieferadresse = models.ForeignKey(Adresse, on_delete=models.DO_NOTHING, related_name='Zustelladresse2')
    rechnungsadresse = models.ForeignKey(Adresse, on_delete=models.DO_NOTHING, related_name='Rechnungsadresse2')
    rechnung = models.FileField(upload_to='invoices/', blank=True)
    dsgvo = models.BooleanField('Datenschutzgrundverordnung', default=False, blank=False, null=False, help_text='Mitglied hat zur Datenschutzgrundverordnung zugestimmt.')
    objects = models.Manager()
    aktive = AktivMitgliedManager()

    @property
    def aktiv(self):
        if self.storndat:
            return False
        return True


class Abonnent(models.Model):
    kundennummer = models.IntegerField()
    titel = models.CharField(max_length=100,blank=True, null=True)
    name = models.CharField(max_length=100)
    name2 = models.CharField(max_length=100,blank=True, null=True)
    name3 = models.CharField(max_length=100,blank=True, null=True)
    tel = models.CharField(max_length=100,blank=True, null=True)
    fax = models.CharField(max_length=100,blank=True, null=True)
    uid = models.CharField(max_length=20, blank=True, null=True)
    prozent = models.FloatField(default=0.)
    rechnungsanzahl = models.IntegerField(default=0)
    dsgvo = models.BooleanField('Datenschutzgrundverordnung', default=False, blank=False, null=False, help_text='Mitglied hat zur Datenschutzgrundverordnung zugestimmt.')
    email = models.CharField(max_length=100,blank=True, null=True)
    rechnungsanschrift = models.ForeignKey(Adresse, on_delete=models.CASCADE, related_name='Anschrift')
    rechnung = models.FileField(upload_to='aboinvoices/', blank=True)
    objects = models.Manager()
    aktive = AktivAbonnentManager()

    @property
    def aktiv(self):
        if self.aboheft_set.filter(aboende__isnull=True).count() > 0:
            return True
        return False
        
    @property
    def inaktiv(self):
        return not self.aktiv

    @property
    def heftsum(self):
        return self.aboheft_set.filter(aboende__isnull=True).aggregate(Sum('heftanzahl'))['heftanzahl__sum']



class AboHeft(Adresse):
    ABO_CHOICES = (
        ('DA', 'Dauerauftrag'),
        ('JB', 'Jahresbestellung'),
    )
    abonummer = models.IntegerField()
    kundennummer = models.ForeignKey(Abonnent, on_delete=models.DO_NOTHING)
    anrede = models.CharField(max_length=100,blank=True, null=True)
    titel = models.CharField(max_length=100,blank=True, null=True)
    vorname = models.CharField(max_length=100,blank=True, null=True)
    nachname = models.CharField(max_length=100,blank=True, null=True)
    surname2 = models.CharField(max_length=100,blank=True, null=True)
    surname3 = models.CharField(max_length=100,blank=True, null=True)
    tel = models.CharField(max_length=100,blank=True, null=True)
    fax = models.CharField(max_length=100,blank=True, null=True)
    heftanzahl = models.IntegerField(null=False, blank=False, default=0)       
    beigz = models.CharField(max_length=20,blank=True, null=True)
    beidat = models.DateField(blank=True, null=True)
    storndat = models.DateField(blank=True, null=True)       
    rueckstand = models.FloatField(default=0.)
    gutschrift = models.FloatField(default=0.)
    aboart = models.CharField(max_length=2, choices=ABO_CHOICES, default='DA')
    aboanfang = models.DateField(blank=True, null=True)
    aboende = models.DateField(blank=True, null=True)       
    anmerkung = models.TextField(null=True, blank=True)     
    rechnung = models.FileField(upload_to='invoices/', blank=True)

    @property
    def aktiv(self):
        if self.aboende:
            return False
        return True  



class VereinsMitglied(User):
    mitgliedsnummer = models.IntegerField(blank=False, null=False, editable=False)
    # email = models.EmailField('Email address', unique=True, null=False, blank=False)
    anrede = models.CharField(max_length=100,blank=True, null=True)
    titel = models.CharField(max_length=100,blank=True, null=True)
    namenszusatz = models.CharField(max_length=100,blank=True, null=True)
    tel = models.CharField(max_length=100,blank=True, null=True)
    fax = models.CharField(max_length=100,blank=True, null=True, editable=False)
    beigz = models.CharField(max_length=20,blank=True, null=True, editable=False)
    beidat = models.DateField(blank=True, null=True)
    storndat = models.DateField(blank=True, null=True)       
    mitgliedsart = models.ForeignKey(Mitgliedsart,blank=True, null=True, on_delete=models.DO_NOTHING)       
    kostenart = models.ForeignKey(Kosten,blank=True, null=True, on_delete=models.DO_NOTHING)       
    versand = models.CharField(max_length=20,blank=True, null=True)       
    gebdat = models.DateField(blank=True, null=True)
    diplomdat = models.DateField(blank=True, null=True)
    diplomort = models.CharField(max_length=100, blank=True, null=True)
    sub = models.CharField(max_length=10, blank=True, null=True, editable=False)       
    vortragold = models.CharField(max_length=10, blank=True, null=True)       
    vortrag = models.ManyToManyField(Vortragsort, blank=True)       
    berufsgruppe = models.ForeignKey(Beruf, blank=True, null=True, on_delete=models.DO_NOTHING)
    heftanzahl = models.IntegerField(null=False, blank=False, default=0)       
    anmerkung = models.TextField(null=True, blank=True)       
    wohnadresse = models.ForeignKey(Adresse, null=True, blank=True, on_delete=models.DO_NOTHING, related_name='Wohnadresse')
    lieferadresse = models.ForeignKey(Adresse, null=True, blank=True, on_delete=models.DO_NOTHING, related_name='Zustelladresse')
    rechnungsadresse = models.ForeignKey(Adresse, null=True, blank=True, on_delete=models.DO_NOTHING, related_name='Rechnungsadresse')
    dsgvo = models.BooleanField('Datenschutzgrundverordnung', default=False, blank=False, null=False, help_text='Mitglied hat zur Datenschutzgrundverordnung zugestimmt.')
    rechnung = models.FileField(upload_to='invoices/', blank=True)
    objects = models.Manager()
    aktive = AktivMitgliedManager()

    @property
    def aktiv(self):
        if not self.storndat:
            return True
        return False

    @property
    def offenerbetrag(self):
        return self.offeneposten_set.filter(bezahlt=False).aggregate(models.Sum('offen'))

    @property
    def daytobirthday(self):
        d = self.gebdat.replace(year=timezone.now().year)-timezone.now().date
        return d.days

    def __str__(self):
        return str(self.mitgliedsnummer)

    class Meta:
        ordering = ['last_name']


class offenePosten(models.Model):
    mitglied = models.ForeignKey(VereinsMitglied, null=True, blank=True, on_delete=models.DO_NOTHING)
    institution = models.ForeignKey(Institution, null=True, blank=True, on_delete=models.DO_NOTHING, default=None)
    erstellt = models.DateTimeField(default=timezone.now,null=False,blank=False, editable=False)
    bezahltam = models.DateTimeField(null=True,blank=True)
    offen = models.FloatField(default=0)
    zahlung = models.FloatField(default=0,null=True,blank=True)
    bezahlt = models.BooleanField(default=False)
    description = models.CharField(max_length=100,null=True,blank=True)

    @property
    def mname(self):
        return "{} {}".format(self.mitglied.first_name, self.mitglied.nachname)

    class Meta:
        ordering = ['erstellt']


class offeneAboPosten(models.Model):
    aboheft = models.ForeignKey(AboHeft, null=True, blank=True, on_delete=models.DO_NOTHING)
    erstellt = models.DateTimeField(default=timezone.now, null=False, blank=False, editable=False)
    bezahltam = models.DateTimeField(null=True,blank=True)
    offen = models.FloatField(default=0)
    zahlung = models.FloatField(default=0, null=True, blank=True)
    bezahlt = models.BooleanField(default=False)
    description = models.CharField(max_length=100, null=True, blank=True)

    class Meta:
        ordering = ['erstellt']


class PasswortLink(models.Model):
    user = models.ForeignKey(User, related_name="vereins_user", on_delete=models.CASCADE)
    linkvalue = models.CharField(max_length=10)
    date = models.DateTimeField( auto_now_add=True)


class EmailId(models.Model):
    uuid4 = models.UUIDField(default=uuid.uuid4, editable=False)
    mitglied = models.ForeignKey(VereinsMitglied, on_delete=models.CASCADE)
    offeneposten = models.ManyToManyField(offenePosten)
    bezahltam = models.DateTimeField(default=timezone.now, editable=False)


# class StandardTexte(models.Model):

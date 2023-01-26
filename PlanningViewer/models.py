import json
from datetime import datetime, date, timedelta

from django.contrib.auth.models import User
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django.utils.translation import gettext_lazy as _


class Werktijd(models.Model):
    voornaam = models.CharField(max_length=20)
    achternaam = models.CharField(max_length=30)
    begintijd = models.TimeField()
    eindtijd = models.TimeField()
    datum = models.DateField()
    pauze = models.TimeField()
    extra = models.BooleanField(default=False)
    colors = models.CharField(default="[]", max_length=50)
    overwerk = models.IntegerField(default=0)

    def __str__(self):
        return self.voornaam + " " + self.achternaam + " - " + str(self.datum) + " - " + \
               str(self.begintijd) + "/" + str(self.eindtijd)

    @property
    def week(self):
        return self.datum.isocalendar()[1]

    def dag(self):
        day_transform = {
            "Monday": "Maandag",
            "Tuesday": "Dinsdag",
            "Wednesday": "Woensdag",
            "Thursday": "Donderdag",
            "Friday": "Vrijdag",
            "Saturday": "Zaterdag",
            "Sunday": "Zondag"
        }
        return day_transform[self.datum.strftime('%A')]

    @property
    def totaal(self):
        interval = datetime.combine(date.today(), self.eindtijd) - datetime.combine(date.today(),
                                                                                    self.begintijd) + timedelta(
            minutes=self.overwerk)
        tm_string = str(interval)
        return datetime.strptime(tm_string, '%H:%M:%S').time()

    @property
    def isSuday(self):

        year = self.datum.year
        from PlanningViewer.functions import calc_easter
        pasen1 = calc_easter(year)
        feestdagen = [
            pasen1,  # Pasen 1
            pasen1 + timedelta(days=1),  # Pasen 2
            pasen1 + timedelta(days=39),  # hemelvaart
            pasen1 + timedelta(days=49),  # pinksteren1
            pasen1 + timedelta(days=50),  # pinksteren2
            date(year, 1, 1),  # nieuwjaarsdag
            date(year, 4, 27),  # koningsdag
            date(year, 12, 25),  # kerst1
            date(year, 12, 26)  # kerst2
        ]

        if self.datum in feestdagen:
            return True

        return self.datum.weekday() == 6

    @property
    def totaal_int(self):
        t = self.totaal
        return t.hour + t.minute / 60.0

    @property
    def get_aanwezigen(self):
        aanwezigen = Werktijd.objects.filter(datum=self.datum).filter(begintijd__lt=self.eindtijd).filter(
            eindtijd__gt=self.begintijd).exclude(voornaam=self.voornaam, achternaam=self.achternaam).order_by('colors')
        return aanwezigen

    @property
    def fav_aanwezig(self):
        fav = Favoriet.objects.filter(f_voornaam=self.voornaam, f_achternaam=self.achternaam)
        aanwezigen = [n.voornaam for n in self.get_aanwezigen]
        for f in fav:
            if f.show_marker and (f.f_voornaam in aanwezigen):
                return True
        return False

    @property
    def pauze_int(self):
        p = self.pauze
        return p.hour + p.minute / 60.0

    def fullname(self):
        return self.voornaam + " " + self.achternaam

    def vandaag(self):
        return self.datum == datetime.now().date()

    @property
    def get_colors(self):
        return json.loads(self.colors)


class Favoriet(models.Model):
    eigenaar = models.ForeignKey(User, on_delete=models.CASCADE)
    f_voornaam = models.CharField(max_length=20)
    f_achternaam = models.CharField(max_length=20)
    show_marker = models.BooleanField(default=False)
    show_tab = models.BooleanField(default=True)

    def fullname(self):
        return self.f_voornaam + " " + self.f_achternaam

    def __str__(self):
        return self.eigenaar.get_full_name() + " -> " + self.f_voornaam + " " + self.f_achternaam


class ApiKey(models.Model):
    # user = models.ForeignKey(User, on_delete=models.CASCADE, unique=True)
    user = models.OneToOneField(User, on_delete=models.CASCADE, primary_key=True)
    lastused = models.DateTimeField(default=datetime.now)
    apikey = models.CharField(max_length=64, unique=True)

    def __str__(self):
        return self.user.first_name


class UserSettings(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    loon = models.FloatField(default=7.55)
    contract_uren = models.FloatField(default=0)
    start_contract_uren = models.DateField(default=date(2020, 9, 7))


class OverurenAjust(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    year = models.IntegerField(validators=[MaxValueValidator(2030), MinValueValidator(2019)], default=datetime.now().year)
    periode = models.IntegerField(validators=[MaxValueValidator(14), MinValueValidator(1)])
    uren_change = models.FloatField(default=0.0)

    class Reasons(models.TextChoices):
        UITBETALING = 'UB', _('Uitbetaling')
        CORRECTIE = 'CC', _('Correctie')

    reason = models.CharField(max_length=2, choices=Reasons.choices, default=Reasons.UITBETALING)

    def __str__(self):
        return self.user.get_full_name() + " -> " + str(self.year) + "/" + str(self.periode) + " -> " + str(self.uren_change)


# @receiver(post_save, sender=User)
# def init_new_user(sender, instance, created, **kwargs):
#     if created:
#         UserSettings.objects.create(user=instance)

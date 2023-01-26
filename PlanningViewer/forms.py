import datetime

from django import forms
from django.core.exceptions import ValidationError
from django.forms import ModelForm, Select

from PlanningViewer.models import Werktijd, Favoriet, UserSettings, OverurenAjust
from PlanningViewer.widgets import MatCheckbox, DateInput, TimeInput


class WerktijdForm(ModelForm):
    class Meta:
        model = Werktijd
        fields = ['begintijd', 'eindtijd', 'datum', 'pauze', 'extra']
        widgets = {
            'datum': DateInput(format='%Y-%m-%d'),
            'begintijd': TimeInput(),
            'eindtijd': TimeInput(),
            'pauze': TimeInput(),
            'extra': MatCheckbox(),
        }

    def clean(self):
        cleaned_data = super().clean()
        begintijd = cleaned_data.get("begintijd")
        eindtijd = cleaned_data.get("eindtijd")

        if begintijd and eindtijd:
            if begintijd > eindtijd:
                raise ValidationError("Eindtijd is lager dan de begintijd!")

        return cleaned_data


class UploadForm(forms.Form):
    file = forms.FileField()


class YearSelectForm(forms.Form):
    CHOICES = [tuple([x, x]) for x in range(2019, datetime.datetime.now().year + 1)]
    yearSelect = forms.ChoiceField(choices=CHOICES, label='Selecteer jaar:')


class AddFav(ModelForm):
    class Meta:
        model = Favoriet
        fields = ['f_voornaam', 'f_achternaam']
        labels = {
            'f_voornaam': "Voornaam",
            'f_achternaam': "Achternaam"
        }


YEAR_CHOICES = [tuple([x, x]) for x in range(2018, 2019)]
PERIOD_CHOICES = [tuple([x, x]) for x in range(1, 14)]


class PeriodeSelectForm(forms.Form):
    year = forms.IntegerField(label="Selecteer jaar", widget=forms.Select(choices=YEAR_CHOICES))
    periode = forms.IntegerField(label="Selecteer periode", widget=forms.Select(choices=PERIOD_CHOICES))


class DateSelectForm(forms.Form):
    date = forms.DateField(widget=DateInput(), label='Datum')


class PersoonSelectForm(ModelForm):
    class Meta:
        model = Werktijd
        fields = ['voornaam', 'achternaam']
        labels = {
            'voornaam': "Voornaam",
            'achternaam': "Achternaam"
        }


class UserSettingsForm(ModelForm):
    class Meta:
        model = UserSettings
        exclude = ['user', 'start_contract_uren']


class UrenAdjustForm(ModelForm):
    class Meta:
        model = OverurenAjust
        exclude = ['user']
        labels = {
            'year': "Jaar",
            'periode': "Periode",
            'uren_change': "Aanpassing uren",
            'reason': "Reden"
        }

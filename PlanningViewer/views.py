import json
import os
from datetime import datetime, timedelta, date
from statistics import mean

from dateutil.relativedelta import relativedelta
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Count
from django.http import HttpResponseRedirect, HttpResponse, JsonResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse_lazy
from django.views.generic import DeleteView, UpdateView, CreateView
from icalendar import Calendar, Event
from pytz import timezone
from rest_framework import viewsets
from rest_framework.response import Response

from PlanningViewer.forms import WerktijdForm, UploadForm, AddFav, UserSettingsForm, YearSelectForm, PersoonSelectForm, \
    DateSelectForm, UrenAdjustForm
from .functions import get_period, get_period_now, maandelijkse_uren, get_period_data, calc_easter
from .models import Werktijd, Favoriet, ApiKey, UserSettings, OverurenAjust
# Create your views here.
from .serializers import WerktijdSerializers


@login_required
def index(request):
    def is_familie(user):
        return user.groups.filter(name='familie').exists()

    fav = Favoriet.objects.filter(eigenaar=request.user)

    werktijden = []

    if not is_familie(request.user):
        werktijden_tmp = Werktijd.objects.filter(voornaam=request.user.first_name).filter(
            achternaam=request.user.last_name).filter(datum__gte=datetime.now().date()).order_by('datum')
        werktijden.append(werktijden_tmp)

    for f in fav:
        if f.show_tab:
            tmp = Werktijd.objects.filter(voornaam=f.f_voornaam).filter(
                achternaam=f.f_achternaam).filter(datum__gte=datetime.now().date()).order_by('datum')
            werktijden.append(tmp)

    context = {
        'werktijden': werktijden,
        'voornaam': request.user.get_short_name()
    }

    return render(request, 'PlanningViewer/index.html', context)


@login_required
def werktijden_details(request, w_id):
    werktijd = Werktijd.objects.get(pk=w_id)
    aanwezigen = werktijd.get_aanwezigen
    delete_permission = True if werktijd.voornaam == request.user.first_name and werktijd.achternaam == request.user.last_name else False

    fav = Favoriet.objects.filter(eigenaar=request.user).filter(show_marker=True)

    marker = False
    if fav:
        for f in fav:
            for a in aanwezigen:
                if f.f_voornaam == a.voornaam and f.f_achternaam == a.achternaam:
                    marker = True
    else:
        marker = False

    if request.method == 'POST':
        overwerk = int(request.POST['overwerk_range'])
        if 0 <= overwerk <= 120 and delete_permission:
            werktijd.overwerk = overwerk
            werktijd.save()

    def get_color_name(c):
        colormap = {
            "#00FF00": "Vleeswaren",
            "#00CCFF": "Zuivel / Kassa 1",
            "#003366": "Bedrijfsleiding",
            "#993300": "Slagerij",
            "#008000": "AGF",
            "#FF00FF": "Opleiding / Pizza",
            "#800080": "Kassa 4 / Bulk",
            "#FF99CC": "Schoonmaken",
            "#99CC00": "Kassa 3",
            "#FF0000": "Kassa",  # "Kassa 6 / Ombouw"
            "#33CCCC": "Kassa 1",
            "#FFFF00": "Kassa 2",
            "#0066CC": "Brood",
            "#FFCC00": "Magazijnmanager",
            "#e5e7e9": "DKW / Anders"
        }
        if c in colormap:
            return colormap[c]
        else:
            return "?"

    colors = json.loads(werktijd.colors.replace("#000000", "#e5e7e9"))
    kleuren = [[k, get_color_name(k)] for k in colors]

    context = {
        'werktijd': werktijd,
        'kleuren': kleuren,
        'aanwezigen': aanwezigen,
        'voornaam': request.user.get_short_name(),
        'delete_permission': delete_permission,
        'marker': marker
    }

    return render(request, 'PlanningViewer/details.html', context)


@login_required
def personen_intersect(request):
    persoonForm = PersoonSelectForm(request.GET)

    if persoonForm.is_valid():
        p_voornaam = persoonForm.cleaned_data['voornaam']
        p_achternaam = persoonForm.cleaned_data['achternaam']
        werktijden = []

        werktijden_1 = Werktijd.objects.filter(voornaam=p_voornaam).filter(achternaam=p_achternaam).filter(
            datum__gte=datetime.now()).order_by('datum')

        werktijden_2 = Werktijd.objects.filter(voornaam=request.user.first_name).filter(
            achternaam=request.user.last_name).filter(
            datum__gte=datetime.now()).order_by('datum')

        def in_interval(b1, b2, e1, e2):
            return b1 <= e2 and e1 >= b2

        for w in werktijden_1:
            for w2 in werktijden_2:
                if in_interval(w.begintijd, w2.begintijd, w.eindtijd, w2.eindtijd) and w.datum == w2.datum:
                    werktijden.append(w2)

        if not werktijden:
            messages.warning(request, 'Geen overlappende werktijden gevonden. Controleer de ingevoerde gegevens.')
            return redirect(tools)

        context = {
            'werktijden': werktijden,
            'voornaam': request.user.get_short_name()
        }

        return render(request, 'PlanningViewer/details_persoon.html', context)

    else:
        messages.warning(request, 'Er is iets misgegaan :(. Probeer opnieuw.')
        return redirect(index)


@login_required
def personen_details(request):
    persoonForm = PersoonSelectForm(request.GET)

    if persoonForm.is_valid():
        p_voornaam = persoonForm.cleaned_data['voornaam']
        p_achternaam = persoonForm.cleaned_data['achternaam']

    else:
        messages.warning(request, 'Persoon niet gevonden.')
        return redirect(index)

    werktijden = Werktijd.objects.filter(voornaam=p_voornaam).filter(achternaam=p_achternaam).filter(
        datum__gte=datetime.now() - timedelta(days=7)).order_by('datum')

    context = {
        'werktijden': werktijden,
        'voornaam': request.user.get_short_name()
    }

    return render(request, 'PlanningViewer/details_persoon.html', context)


@login_required
def upload_planning(request):
    if not request.user.is_staff:
        messages.warning(request, 'Deze pagina is niet toegankelijk.')
        return HttpResponseRedirect('/')

    if request.method == 'POST':
        form = UploadForm(request.POST, request.FILES)
        if form.is_valid():
            data = request.FILES['file']
            # path = default_storage.save('tmp/' + str(data), ContentFile(data.read()))
            # tmp_file_path = os.path.join(settings.MEDIA_ROOT, path)
            tmp_file_path = data.temporary_file_path()
            f_name = data.name
            from subprocess import check_output
            import json
            out = check_output(['java', '-jar', '/jumbo_website/PlanningReader.main.jar', tmp_file_path])
            j = json.loads(out)

            werktijden = []
            for p in j:
                col = json.dumps(p['colors'])

                # Check for errors
                if p["eind"] < p["begin"]:
                    messages.error(request, f'Onjuiste werktijd voor {p["voornaam"]} {p["achternaam"]} op {p["datum"]}')
                    return HttpResponseRedirect('/')

                werktijden.append(
                    Werktijd(voornaam=p["voornaam"], achternaam=p["achternaam"], begintijd=p["begin"],
                             eindtijd=p["eind"],
                             pauze=p["pauze"], datum=p["datum"], colors=col))
            Werktijd.objects.bulk_create(werktijden)
            messages.success(request, 'Planning is met succes geüpload!')
            return HttpResponseRedirect('/')

    context = {
        'uploadform': UploadForm(),
        'voornaam': request.user.get_short_name()
    }

    return render(request, 'PlanningViewer/uploadplanning.html', context)


@login_required
def fav_toevoegen(request):
    if request.method == 'POST':
        # create a form instance and populate it with data from the request:
        form = AddFav(request.POST)
        # check whether it's valid:
        if form.is_valid():
            if not Werktijd.objects.filter(voornaam=form.cleaned_data['f_voornaam']).filter(
                    achternaam=form.cleaned_data['f_achternaam']):
                messages.warning(request, 'Fout: de voor- en/of achternaam is niet gevonden. Probeer het opnieuw.')
            else:
                value = form.save(commit=False)
                value.eigenaar = request.user
                value.save()

    fav = Favoriet.objects.filter(eigenaar=request.user)

    context = {
        'voornaam': request.user.get_short_name(),
        'form': AddFav(),
        'favorieten': fav,
    }

    return render(request, 'PlanningViewer/fav_toevoegen.html', context)


class FavorietDelete(LoginRequiredMixin, DeleteView):
    model = Favoriet
    success_message = "Favoriet succesvol verwijderd."
    success_url = reverse_lazy('fav_toevoegen')

    def get_queryset(self):
        qs = super(FavorietDelete, self).get_queryset()
        return qs.filter(eigenaar=self.request.user)


class WerktijdDelete(LoginRequiredMixin, DeleteView):
    model = Werktijd
    success_message = "Werktijd succesvol verwijderd."
    success_url = reverse_lazy('index')

    def get_queryset(self):
        qs = super(WerktijdDelete, self).get_queryset()
        return qs.filter(voornaam=self.request.user.first_name).filter(
            achternaam=self.request.user.last_name)


class WerktijdUpdate(LoginRequiredMixin, UpdateView):
    model = Werktijd
    success_message = "Werktijd succesvol aangepast."
    success_url = reverse_lazy('index')
    template_name = "PlanningViewer/toevoegen.html"
    form_class = WerktijdForm

    def get_queryset(self):
        qs = super(WerktijdUpdate, self).get_queryset()
        return qs.filter(voornaam=self.request.user.first_name).filter(
            achternaam=self.request.user.last_name)

    def form_valid(self, form):
        form.instance.voornaam = self.request.user.first_name
        form.instance.achternaam = self.request.user.last_name
        return super().form_valid(form)


class WerktijdCreate(LoginRequiredMixin, CreateView):
    model = Werktijd
    success_message = "Werktijd succesvol toegevoegd."
    success_url = reverse_lazy('index')
    template_name = "PlanningViewer/toevoegen.html"
    form_class = WerktijdForm

    def form_valid(self, form):
        form.instance.voornaam = self.request.user.first_name
        form.instance.achternaam = self.request.user.last_name
        return super().form_valid(form)


@login_required
def stats_view(request):
    if request.method == 'POST':
        form = YearSelectForm(request.POST)
        if form.is_valid():
            yearS = int(form.cleaned_data['yearSelect'])
        else:
            yearS = datetime.now().year
    else:
        yearS = datetime.now().year

    context = {
        "m_uren": maandelijkse_uren(yearS, get_period_now(), request),
        "periode_now": get_period_now(),
        "yearselect": YearSelectForm()
    }

    return render(request, 'PlanningViewer/stats.html', context)


@login_required
def periode_view(request, year=2020, periode=1):
    start, eind = get_period(periode, year)
    werktijden = Werktijd.objects.filter(datum__gte=start).filter(datum__lte=eind).filter(
        voornaam=request.user.first_name).filter(achternaam=request.user.last_name).order_by('datum')

    context = {
        'werktijden': werktijden,
        'begin_p': start.date(),
        'eind_p': eind.date()
    }

    return render(request, 'PlanningViewer/periode_detail.html', context)


@login_required
def api_key(request):
    def newKey(string_length=32):
        """Generate a random string with the combination of lowercase and uppercase letters """
        import string
        import random
        letters = string.ascii_letters
        return ''.join(random.choice(letters) for i in range(string_length))

    key = ApiKey.objects.filter(user=request.user)

    if not key:
        # Key needs to be generated
        apikey = newKey()
        saveKey = ApiKey(user=request.user, apikey=apikey)
        saveKey.save()
        pass
    else:
        # Key exists
        apikey = key[0].apikey

    context = {
        "apikey": apikey,
        "host": os.getenv("SERVER_HOST")
    }

    return render(request, 'PlanningViewer/api/create_key.html', context)


def ical_api(request):
    key = request.GET.get("key", None)

    if key is None:
        # Check if a key is passed
        return HttpResponse('Unauthorized', status=401)

    api_key_obj = ApiKey.objects.filter(apikey=key).first()

    if not api_key_obj:
        # Check if the key belongs to a user
        return HttpResponse('Unauthorized', status=401)

    user = api_key_obj.user
    api_key_obj.lastused = datetime.now()
    api_key_obj.save()

    werktijden = Werktijd.objects.filter(voornaam=user.first_name).filter(achternaam=user.last_name).filter(
        datum__gte=datetime.now() - timedelta(days=14))

    def create_ical(werktijden):
        amsterdam = timezone('Europe/Amsterdam')

        cal = Calendar()

        # Add requierd iCal parameters
        cal.add('prodid', '-//Werkijden Calendar Export//wexport.nl//')
        cal.add('version', '2.0')

        dtstamp = datetime.now().replace(tzinfo=amsterdam)

        for werktijd in werktijden:
            event = Event()

            event.add('uid', '{}-{}@{}'.format(werktijd.id, datetime.now().year, os.getenv("SERVER_HOST")))
            event.add('dtstamp', dtstamp)

            dtstart = datetime(werktijd.datum.year, werktijd.datum.month, werktijd.datum.day,
                               werktijd.begintijd.hour, werktijd.begintijd.minute, 0, tzinfo=amsterdam)
            dtend = datetime(werktijd.datum.year, werktijd.datum.month, werktijd.datum.day,
                             werktijd.eindtijd.hour, werktijd.eindtijd.minute, 0, tzinfo=amsterdam)

            event.add('summary', 'Werken')
            event.add('dtstart', dtstart)
            event.add('dtend', dtend)
            event.add('description',
                      'Werken bij Jumbo van {} tot {}'.format(werktijd.begintijd, werktijd.eindtijd))
            event.add('location', os.getenv("CALENDAR_LOCATION"))
            cal.add_component(event)

        payout_event = Event()
        closest, ndays = next_payout()
        payout_event.add('uid', 'payout-{}-{}-{}@{}'.format(closest.year, closest.month, closest.day,
                                                            os.getenv("SERVER_HOST")))
        payout_event.add('dtstamp', dtstamp)
        payout_event.add('summary', 'Salaris uitbetaling 💰')
        payout_event.add('dtstart', datetime(closest.year, closest.month, closest.day, 9, 0, tzinfo=amsterdam))
        payout_event.add('dtend', datetime(closest.year, closest.month, closest.day, 10, 0, tzinfo=amsterdam))
        payout_event.add('description', 'Salaris uitbetaling! 💰')
        cal.add_component(payout_event)
        return cal

    response = HttpResponse(create_ical(werktijden).to_ical(), content_type="text/calendar")
    response['Content-Disposition'] = 'attachment; filename=werktijden.ics'
    return response


@login_required
def export_data(request):
    # Create the HttpResponse object with the appropriate CSV header.
    import csv
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="werktijden.csv"'

    werktijden = Werktijd.objects.filter(voornaam=request.user.first_name, achternaam=request.user.last_name)

    writer = csv.writer(response)
    for wt in werktijden:
        # datum, begin, eind, week, extra, pauze, totaal
        writer.writerow([wt.datum, wt.begintijd, wt.eindtijd, wt.week, wt.extra, wt.pauze, wt.totaal])

    return response


def next_payout():
    u = datetime.strptime("31-12-2020", "%d-%m-%Y")
    d = timedelta(days=28)

    dates = [(u + i * d).date() for i in range(0, 60)]
    closest = min([d for d in dates if d >= date.today()], key=lambda x: abs(x - date.today()))
    ndays = (closest - date.today()).days
    return closest, ndays


@login_required
def tools(request):
    closest, ndays = next_payout()
    start_d = datetime.today().replace(day=1).date() - relativedelta(months=1)
    end_d = datetime.today().replace(day=1).date()
    wvdm = Werktijd.objects.filter(datum__gte=start_d).filter(datum__lt=end_d).values('voornaam', 'achternaam').annotate(num=Count('datum')).order_by('-num')[:3]


    context = {
        'voornaam': request.user.get_short_name(),
        'closest': closest,
        'ndays': ndays,
        'intersectfrom': PersoonSelectForm(),
        'wvdm': wvdm,
        'eerste_d': f"{start_d} - {end_d}"
    }

    return render(request, 'PlanningViewer/tools.html', context)


@login_required
def nu_aanwezig(request):
    now = datetime.now().time()
    aanwezigen = Werktijd.objects.filter(datum=datetime.now().date(), begintijd__lte=now, eindtijd__gte=now)

    context = {
        'aanwezigen': aanwezigen
    }
    return render(request, 'PlanningViewer/nu_aanwezig.html', context)


class UserSettingsUpdate(UpdateView):
    model = UserSettings
    success_message = "Instellingen succesvol aangepast."
    success_url = reverse_lazy('index')
    template_name = "PlanningViewer/instellingen.html"
    form_class = UserSettingsForm

    def get_queryset(self):
        qs = super(UserSettingsUpdate, self).get_queryset()
        return qs.filter(user=self.request.user)


@login_required
def zoeken(request):
    context = {
        'zoekpersoonform': PersoonSelectForm(),
        'zoekdateform': DateSelectForm()
    }

    if request.method == 'POST':
        zoekpersoonform = PersoonSelectForm(request.POST)
        zoekdateform = DateSelectForm(request.POST)
        if zoekpersoonform.is_valid():
            context['zoekpersoonform'] = zoekpersoonform
            voornaam = zoekpersoonform.cleaned_data['voornaam']
            achternaam = zoekpersoonform.cleaned_data['achternaam']
            response = redirect(personen_details)
            response['Location'] += '?voornaam=' + voornaam + '&achternaam=' + achternaam
            return response

        elif zoekdateform.is_valid():
            context['zoekdateform'] = zoekdateform
            date = zoekdateform.cleaned_data['date']
            werktijden = Werktijd.objects.filter(datum=date).order_by('colors')
            wt = []
            for w in werktijden:
                wt.append([w, json.loads(w.colors.replace("#000000", "#e5e7e9"))])
            context['dateoutput'] = wt

            return render(request, 'PlanningViewer/zoeken.html', context)
    # else:
    #     zoekpersoonform = PersoonSelectForm()
    #     zoekdateform = DateSelectForm()

    return render(request, 'PlanningViewer/zoeken.html', context)


def next_api(request):
    key = request.GET.get("key", None)

    if key is None:
        # Check if a key is passed
        return HttpResponse('Unauthorized', status=401)

    api_key_obj = ApiKey.objects.filter(apikey=key).first()

    if not api_key_obj:
        # Check if the key belongs to a user
        return HttpResponse('Unauthorized', status=401)

    user = api_key_obj.user
    api_key_obj.lastused = datetime.now()
    api_key_obj.save()

    werktijd = Werktijd.objects.filter(voornaam=user.first_name).filter(achternaam=user.last_name).filter(
        datum__gte=datetime.now()).order_by('datum').first()

    if werktijd:
        # locale.setlocale(locale.LC_ALL, "nl_NL.utf8")
        datum = werktijd.datum.strftime("%A %-d %b")
        btijd = werktijd.begintijd.strftime("%H:%M")
        etijd = werktijd.eindtijd.strftime("%H:%M")

        nextw = {
            "next": datum + " " + btijd + " - " + etijd
        }

    else:
        nextw = {"next": "Onbekend"}

    return JsonResponse(nextw)


class OverurenAdjustDelete(LoginRequiredMixin, DeleteView):
    model = OverurenAjust
    success_message = "Aanpassing succesvol verwijderd."
    success_url = reverse_lazy('overuren')

    def get_queryset(self):
        qs = super(OverurenAdjustDelete, self).get_queryset()
        return qs.filter(user=self.request.user)


@login_required
def overuren(request):
    if request.method == 'POST':
        form = UrenAdjustForm(request.POST)
        if form.is_valid():
            value = form.save(commit=False)
            value.user = request.user
            if value.reason == 'UB':
                value.uren_change = value.uren_change * -1.0
            value.save()
        else:
            messages.warning(request, 'Ongeldige gegevens ingevoerd! Probeer opnieuw.')

    c_uren = request.user.usersettings.contract_uren

    if c_uren == 0:  # Niet in vast contract modus
        messages.warning(request,
                         'U heeft geen aantal contracturen ingesteld, hierdoor is de overuren optie niet beschikbaar. U kunt dit aanpassen onder instellingen.')
        return redirect(index)

    start_date = request.user.usersettings.start_contract_uren
    # s_year, s_periode = date_to_period(start_date)  # date_to_period(date(2020, 9, 8))
    s_year = 2020
    s_periode = 11
    p_data = []
    acc = 0

    adjustments = OverurenAjust.objects.filter(user=request.user)

    def get_adjust(year, per):
        adj = 0.0
        res = ""
        aid = -1
        for a in adjustments:
            if a.year == year and a.periode == per:
                adj = a.uren_change
                res = a.reason
                aid = a.id
        return adj, res, aid

    for y in range(s_year, datetime.now().year + 1):
        start_p = s_periode if s_year == y else 1
        stop_p = get_period_now() if y == datetime.now().year else 14

        for i in range(start_p, min(stop_p + 2, 14)):
            totaal_uur, totaal_pauze, totaal_zondag = get_period_data(i, y, request)
            netto_uur = totaal_uur - totaal_pauze
            overuur = (totaal_uur - totaal_pauze) - 4 * c_uren
            acc = acc + overuur
            start_d, end_d = get_period(i, y)

            p_data.append({"totaal_uur": totaal_uur,
                           "totaal_pauze": totaal_pauze,
                           "totaal_zondag": totaal_zondag,
                           "netto_uur": netto_uur,
                           "overuren": overuur,
                           "periode": str(y) + "/" + str(i),
                           "datum": str(start_d.date().strftime("%d %b")) + " - " + str(end_d.date().strftime("%d %b")),
                           "acc": acc,
                           })

            adj, res, aid = get_adjust(y, i)
            if adj != 0:
                acc = acc + adj
                p_data.append({"totaal_uur": "-",
                               "totaal_pauze": aid,  # also used to pass id :P
                               "totaal_zondag": "-",
                               "netto_uur": res,
                               "overuren": adj,
                               "periode": str(y) + "/" + str(i),
                               "datum": str(start_d.date().strftime("%d %b")) + " - " + str(
                                   end_d.date().strftime("%d %b")),
                               "acc": acc,
                               })

    context = {
        "p_data": reversed(p_data),
        "form": UrenAdjustForm()
    }

    return render(request, 'PlanningViewer/overuren_view.html', context)


class WerktijdViewSet(viewsets.ViewSet):
    """
    A simple ViewSet for listing or retrieving werktijden.
    """

    def list(self, request):
        queryset = Werktijd.objects.filter(voornaam=request.user.first_name).filter(
            achternaam=request.user.last_name).filter(datum__gte=datetime.now().date()).order_by('datum')
        serializer = WerktijdSerializers(queryset, many=True)
        return Response(serializer.data)

    def retrieve(self, request, pk=None):
        queryset = Werktijd.objects.all()
        werktijd = get_object_or_404(queryset, pk=pk)
        serializer = WerktijdSerializers(werktijd)
        return Response(serializer.data)


@login_required
def vandaag(request):
    dtm = datetime.now().date()

    if 'date' in request.GET:
        dtm = datetime.strptime(request.GET.get("date"), "%d-%m-%Y")
    else:
        dtm = datetime.now().date()

    if request.method == 'POST':
        zoekdateform = DateSelectForm(request.POST)
        if zoekdateform.is_valid():
            dtm = zoekdateform.cleaned_data['date']

    aanwezigen = Werktijd.objects.filter(datum=dtm).order_by('begintijd')

    personen = []
    uren = []

    def t_to_float(time):
        return time.hour + time.minute / 60.0

    for w in aanwezigen:
        personen.append(w.fullname())
        uren.append([t_to_float(w.begintijd), t_to_float(w.eindtijd)])

    context = {
        'data': [personen, uren],
        'zoekdateform': DateSelectForm(request.POST),
        'next': datetime.strftime(dtm + timedelta(days=1), "%d-%m-%Y"),
        'prev': datetime.strftime(dtm - timedelta(days=1), "%d-%m-%Y"),
        'date': datetime.strftime(dtm, "%Y-%m-%d"),
    }
    return render(request, 'PlanningViewer/vandaag.html', context)


@login_required
def geldterug(request):
    vnaam = request.GET.get("voornaam", request.user.first_name)
    anaam = request.GET.get("achternaam", request.user.last_name)
    year = int(request.GET.get("jaar", 2022))

    if vnaam == "" or anaam == "":
        vnaam = request.user.first_name
        anaam = request.user.last_name

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

    # get the requierd date ranges
    dateranges = []
    for f in feestdagen:
        dateranges.append(Werktijd.objects.filter(voornaam=vnaam, achternaam=anaam,
                                                  datum__lte=f, datum__gt=f-timedelta(weeks=12)))

    # calculate the amount of worked days on that particular date
    results = []
    for day, daterange in zip(feestdagen, dateranges):
        feestday = day.weekday()
        count = 0
        debug = []
        for d in daterange:
            if d.datum.weekday() == feestday:
                count = count + 1
                debug.append(d)
        gem_uren_l = [(x.totaal_int - x.pauze_int) for x in debug]
        gem_uren = mean(gem_uren_l) if len(gem_uren_l) >= 1 else 0
        results.append([day, count, [x.datum.strftime("%d %b %Y wk %W") for x in debug], gem_uren])

    context = {'results': results,
               'fname': f'{vnaam} {anaam} in {year}',
               'vnaam': vnaam,
               'anaam': anaam,
               'years': reversed(range(2020, datetime.now().year+1))
               }

    return render(request, 'PlanningViewer/geldterug.html', context)


'''
accounts/login/ [name='login']
accounts/logout/ [name='logout']
accounts/password_change/ [name='password_change']
accounts/password_change/done/ [name='password_change_done']
accounts/password_reset/ [name='password_reset']
accounts/password_reset/done/ [name='password_reset_done']
accounts/reset/<uidb64>/<token>/ [name='password_reset_confirm']
accounts/reset/done/ [name='password_reset_complete']
'''

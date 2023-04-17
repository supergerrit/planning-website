from datetime import datetime, timedelta, date

from PlanningViewer.models import Werktijd


def get_period(periode, year):
    dyear = year - 2019
    offset = (periode - 1) * 28 + (dyear * 28 * 13)

    if year > 2020:  # correction for week 53 in 2020
        offset = offset + 7

    start_epoch = datetime.strptime("2018-12-03", "%Y-%m-%d")
    start_date = start_epoch + timedelta(days=offset)
    end_date = start_epoch + timedelta(days=offset + 28 - 1)

    if year == 2020 and periode == 13:  # correction for week 53 in 2020
        end_date = end_date + timedelta(days=7)

    return start_date, end_date


def get_period_now():
    day_of_year = datetime.now().timetuple().tm_yday
    return day_of_year // 28 + 1


def date_to_period(date):
    day_of_year = date.timetuple().tm_yday
    p = day_of_year // 28 + 1
    year = date.year
    return year, p


def get_period_data(periode, year, req):
    start, end = get_period(periode, year)
    werktijden = Werktijd.objects.filter(datum__gte=start).filter(datum__lte=end).filter(
        voornaam=req.user.first_name).filter(achternaam=req.user.last_name)

    totaal_uur, totaal_pauze, totaal_zondag = 0, 0, 0
    for w in werktijden:
        totaal_uur = totaal_uur + w.totaal_int
        totaal_pauze = totaal_pauze + w.pauze_int
        if w.isSuday:
            totaal_zondag = totaal_zondag + w.totaal_int - w.pauze_int

    return totaal_uur, totaal_pauze, totaal_zondag


def maandelijkse_uren(year, periode, req):
    maanden = []
    per = 14 if year < datetime.now().year else periode + 2  # 15
    for i in range(1, per):
        totaal_uur, totaal_pauze, totaal_zondag = get_period_data(i, year, req)
        netto = totaal_uur - totaal_pauze
        start, eind = get_period(i, year)
        # salaris = UserSettings.objects.get_or_create(user=req.user)[0].loon
        salaris = req.user.usersettings.loon
        verdiend = netto * salaris * 1.17 + totaal_zondag * salaris
        maanden.append({'totaal_uur': totaal_uur, 'totaal_pauze': totaal_pauze, 'netto': netto,
                        "start": start.date(), "eind": eind.date(), "verdiend": verdiend,
                        "totaal_zondag": totaal_zondag, "year": year})
    return maanden


def calc_easter(year):
    """Returns Easter as a date object."""
    a = year % 19
    b = year // 100
    c = year % 100
    d = (19 * a + b - b // 4 - ((b - (b + 8) // 25 + 1) // 3) + 15) % 30
    e = (32 + 2 * (b % 4) + 2 * (c // 4) - d - (c % 4)) % 7
    f = d + e - 7 * ((a + 11 * d + 22 * e) // 451) + 114
    month = f // 31
    day = f % 31 + 1
    return date(year, month, day)


def next_payout():
    u = datetime.strptime("31-12-2020", "%d-%m-%Y")
    days_since_u = (date.today() - u.date()).days
    days_to_next_payout = 28 - (days_since_u % 28)
    closest = date.today() + timedelta(days=days_to_next_payout)
    ndays = days_to_next_payout
    return closest, ndays

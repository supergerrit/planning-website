from django.urls import path
from django.views.generic import RedirectView, TemplateView

from . import views

# TODO refactor URLS
urlpatterns = [
    path('', views.index, name='index'),
    path('toevoegen', views.WerktijdCreate.as_view(), name='toevoegen'),
    path('werktijden/<int:w_id>/', views.werktijden_details, name='details'),
    path('werktijden/update/<int:pk>/', views.WerktijdUpdate.as_view(), name='wt_update'),
    path('werktijden/delete/<int:pk>', views.WerktijdDelete.as_view(), name='wt_delete'),
    path('werktijden/export', views.export_data, name='export_data'),
    path('personen', views.personen_details, name='details_persoon'),
    path('personen/intersect', views.personen_intersect, name='personen_intersect'),
    path('upload', views.upload_planning, name='upload'),
    path('favorieten/toevoegen', views.fav_toevoegen, name='fav_toevoegen'),
    path('favorieten/delete/<int:pk>', views.FavorietDelete.as_view(), name='fav_delete'),
    path('api/create', views.api_key, name='create_api_key'),
    path('api/ical', views.ical_api, name='ical_api'),
    path('api/next', views.next_api, name='next_api'),
    path('api', RedirectView.as_view(pattern_name='index', permanent=False), name='api'),
    path('stats', views.stats_view, name='stats'),
    path('tools', views.tools, name='tools'),
    path('nuaanwezig', views.nu_aanwezig, name='nu_aanwezig'),
    path('instellingen/<int:pk>', views.UserSettingsUpdate.as_view(), name='instellingen'),
    path('zoeken', views.zoeken, name='zoeken'),
    path('periode/<int:year>/<int:periode>', views.periode_view, name='periode_view'),
    path('overuren', views.overuren, name='overuren'),
    path('overuren/delete/<int:pk>', views.OverurenAdjustDelete.as_view(), name='overuren_delete'),
    path('vandaag', views.vandaag, name='vandaag'),
    path('geldterug', views.geldterug, name='geldterug'),
    path(
        'sw.js',
        TemplateView.as_view(template_name='PlanningViewer/sw.js', content_type='application/javascript'),
        name='sw.js',
    ),
    path('offline', TemplateView.as_view(template_name='PlanningViewer/offline.html'))

]

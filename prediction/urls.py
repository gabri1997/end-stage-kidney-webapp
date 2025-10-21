from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('pazienti/', views.lista_pazienti, name='lista_pazienti'),
    path('pazienti/nuovo/', views.nuovo_paziente, name='nuovo_paziente'),
    path('pazienti/<int:paziente_id>/', views.dettaglio_paziente, name='dettaglio_paziente'),
    path('pazienti/<int:paziente_id>/visita/nuova/', views.nuova_visita, name='nuova_visita'),  
    path('pazienti/<int:paziente_id>/mestc/nuovo/', views.nuovo_mestc, name='nuovo_mestc'),
    path('pazienti/<int:paziente_id>/visita/<int:visita_id>/modifica/', views.modifica_visita, name='modifica_visita'),
    path('pazienti/<int:paziente_id>/visita/<int:visita_id>/elimina/', views.elimina_visita, name='elimina_visita'),
    path('pazienti/<int:paziente_id>/mestc/<int:mestc_id>/modifica/', views.modifica_mestc, name='modifica_mestc'),
    path('pazienti/<int:paziente_id>/mestc/<int:mestc_id>/elimina/', views.elimina_mestc, name='elimina_mestc'),
    path('pazienti/<int:paziente_id>/visita/<int:visita_id>/predict/', views.calcola_eskd, name='calcola_eskd'),
    path('pazienti/<int:paziente_id>/modifica/', views.modifica_paziente, name='modifica_paziente'),
    path('mestc/<int:mestc_id>/delete/', views.delete_mestc, name='delete_mestc'),
    path("predizione/<int:predizione_id>/delete/", views.delete_predizione, name="delete_predizione"),

]

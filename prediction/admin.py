from django.contrib import admin
from .models import Paziente, MESTC, Visita

@admin.register(Paziente)
class PazienteAdmin(admin.ModelAdmin):
    list_display = ("cognome", "nome", "codice_fiscale", "email")
    search_fields = ("cognome", "nome", "codice_fiscale", "email")

@admin.register(MESTC)
class MESTCAdmin(admin.ModelAdmin):
    list_display = ("paziente", "data_rilevazione", "M", "E", "S", "T", "C", "updated_at")
    list_filter = ("data_rilevazione",)

@admin.register(Visita)
class VisitaAdmin(admin.ModelAdmin):
    list_display = ("paziente", "data_visita", "creatinina", "egfr", "proteinuria")
    list_filter = ("data_visita",)

from django import forms
from .models import Paziente, Visita, MESTC


class PazienteForm(forms.ModelForm):
    class Meta:
        model = Paziente
        fields = ['nome', 'cognome', 'data_nascita', 'codice_fiscale', 'email', 'telefono', 'indirizzo']


class VisitaForm(forms.ModelForm):
    class Meta:
        model = Visita
        fields = ['data_visita', 'creatinina', 'egfr', 'proteinuria', 'albuminuria',
                  'pressione_sistolica', 'pressione_diastolica', 'note']


class MESTCForm(forms.ModelForm):
    class Meta:
        model = MESTC
        fields = ['data_rilevazione', 'M', 'E', 'S', 'T', 'C']


class CalcolaESKDForm(forms.Form):
    sesso = forms.ChoiceField(choices=[('M', 'Maschio'), ('F', 'Femmina')], label="Sesso")
    eta = forms.IntegerField(label="Età (anni)", min_value=0)

    creatinina = forms.FloatField(label="Creatinina (mg/dL)")
    proteinuria = forms.FloatField(label="Proteinuria (mg/24h)")
    pressione_sistolica = forms.FloatField(label="Pressione Sistolica (mmHg)")
    pressione_diastolica = forms.FloatField(label="Pressione Diastolica (mmHg)")

    M = forms.IntegerField(label="M (MEST-C)", min_value=0, max_value=1)
    E = forms.IntegerField(label="E (MEST-C)", min_value=0, max_value=1)
    S = forms.IntegerField(label="S (MEST-C)", min_value=0, max_value=1)
    T = forms.IntegerField(label="T (MEST-C)", min_value=0, max_value=1)
    C = forms.IntegerField(label="C (MEST-C)", min_value=0, max_value=1)

    iperteso = forms.BooleanField(label="Iperteso", required=False)
    Antihypertensive = forms.BooleanField(label="Terapia Antipertensiva", required=False)
    Immunosuppressants = forms.BooleanField(label="Terapia Immunosoppressiva", required=False)
    FishOil = forms.BooleanField(label="Olio di pesce (Fish Oil)", required=False)

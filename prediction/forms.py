from django import forms
from .models import Paziente, Visita, MESTC

class PazienteForm(forms.ModelForm):
    class Meta:
        model = Paziente
        fields = [
            'nome',
            'cognome',
            'codice_fiscale',
            'email',
            'telefono',
            'indirizzo',
            'sesso',
            'eta',
        ]
        # Rimuovi widgets se non hai 'data_nascita' nei fields
        # Oppure aggiungi 'data_nascita' ai fields se esiste nel model

class VisitaForm(forms.ModelForm):
    class Meta:
        model = Visita
        fields = ['data_visita', 'creatinina', 'egfr', 'proteinuria', 'albuminuria',
                  'pressione_sistolica', 'pressione_diastolica', 'note', 'referto']
        widgets = {
            'data_visita': forms.DateInput(
                attrs={
                    'type': 'date',
                    'class': 'input'
                }
            ),
            'note': forms.Textarea(
                attrs={
                    'class': 'textarea',
                    'rows': 4
                }
            ),
            'creatinina': forms.NumberInput(
                attrs={
                    'class': 'input',
                    'step': '0.01',
                    'placeholder': 'es. 1.2'
                }
            ),
            'egfr': forms.NumberInput(
                attrs={
                    'class': 'input',
                    'step': '0.01'
                }
            ),
            'proteinuria': forms.NumberInput(
                attrs={
                    'class': 'input',
                    'step': '0.01',
                    'placeholder': 'es. 0.5'
                }
            ),
            'albuminuria': forms.NumberInput(
                attrs={
                    'class': 'input',
                    'step': '0.01'
                }
            ),
            'pressione_sistolica': forms.NumberInput(
                attrs={
                    'class': 'input',
                    'placeholder': 'es. 120'
                }
            ),
            'pressione_diastolica': forms.NumberInput(
                attrs={
                    'class': 'input',
                    'placeholder': 'es. 80'
                }
            ),
            'referto': forms.FileInput(
                attrs={
                    'accept': 'application/pdf,image/jpeg,image/png'
                }
            )
        }
        labels = {
            'data_visita': 'Data Visita',
            'creatinina': 'Creatinina (mg/dL)',
            'egfr': 'eGFR (ml/min/1.73m²)',
            'proteinuria': 'Proteinuria (g/24h)',
            'albuminuria': 'Albuminuria (mg/24h)',
            'pressione_sistolica': 'Pressione Sistolica (mmHg)',
            'pressione_diastolica': 'Pressione Diastolica (mmHg)',
            'note': 'Note',
            'referto': 'Referto (PDF/Immagine)'
        }

class MESTCForm(forms.ModelForm):
    class Meta:
        model = MESTC
        fields = ['data_rilevazione', 'M', 'E', 'S', 'T', 'C']
        widgets = {
            'data_rilevazione': forms.DateInput(
                attrs={'type': 'date', 'class': 'input'}
            ),
            'M': forms.NumberInput(attrs={'class': 'input', 'min': '0', 'max': '1'}),
            'E': forms.NumberInput(attrs={'class': 'input', 'min': '0', 'max': '1'}),
            'S': forms.NumberInput(attrs={'class': 'input', 'min': '0', 'max': '1'}),
            'T': forms.NumberInput(attrs={'class': 'input', 'min': '0', 'max': '2'}),
            'C': forms.NumberInput(attrs={'class': 'input', 'min': '0', 'max': '2'}),
        }
        labels = {
            'data_rilevazione': 'Data Rilevazione',
            'M': 'M (Mesangial hypercellularity)',
            'E': 'E (Endocapillary hypercellularity)',
            'S': 'S (Segmental sclerosis)',
            'T': 'T (Tubular atrophy/interstitial fibrosis)',
            'C': 'C (Cellular/fibrocellular crescents)',
        }

class CalcolaESKDForm(forms.Form):
    sesso = forms.ChoiceField(choices=[('M', 'Maschio'), ('F', 'Femmina')], label="Sesso")
    eta = forms.IntegerField(label="Età (anni)", min_value=0)
    creatinina = forms.FloatField(label="Creatinina (mg/dL)")
    proteinuria = forms.FloatField(label="Proteinuria (mg/24h)")
    pressione_sistolica = forms.FloatField(label="Pressione Sistolica (mmHg)", required=False)
    pressione_diastolica = forms.FloatField(label="Pressione Diastolica (mmHg)", required=False)
    M = forms.IntegerField(label="M (MEST-C)", min_value=0, max_value=1)
    E = forms.IntegerField(label="E (MEST-C)", min_value=0, max_value=1)
    S = forms.IntegerField(label="S (MEST-C)", min_value=0, max_value=1)
    T = forms.IntegerField(label="T (MEST-C)", min_value=0, max_value=2)
    C = forms.IntegerField(label="C (MEST-C)", min_value=0, max_value=2)
    iperteso = forms.BooleanField(label="Iperteso", required=False)
    Antihypertensive = forms.BooleanField(label="Terapia Antipertensiva", required=False)
    Immunosuppressants = forms.BooleanField(label="Terapia Immunosoppressiva", required=False)
    FishOil = forms.BooleanField(label="Olio di pesce (Fish Oil)", required=False)
from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from django.contrib.auth.forms import SetPasswordForm
from .models import Paziente, Visita, MESTC, UserSecurity

# Elenco domande standard disponibili per la domanda di sicurezza
SECURITY_QUESTIONS = [
    "Qual è il nome del tuo primo animale domestico?",
    "In che città sei nato?",
    "Qual è il cognome da nubile di tua madre?",
]

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
            'data_nascita',
        ]
        def calcola_eta(self):
            if self.data_nascita:
                today = date.today()
                return today.year - self.data_nascita.year - ((today.month, today.day) < (self.data_nascita.month, self.data_nascita.day))
            return None
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


class CustomUserCreationForm(UserCreationForm):
    """User creation form that also collects a mandatory email.

    Notes:
    - Password reset flow looks up users by email; collecting it at signup ensures it works for doctors.
    - We don't enforce unique emails at the DB level here; optionally add uniqueness validation below.
    """

    email = forms.EmailField(required=True, help_text="Richiesto per il reset della password")
    # Campi per domanda di sicurezza durante la registrazione
    question = forms.ChoiceField(
        choices=[(q, q) for q in SECURITY_QUESTIONS] + [("Altro", "Altro (personalizzata)")],
        label="Domanda di sicurezza",
        required=True,
    )
    custom_question = forms.CharField(required=False, label="Domanda personalizzata")
    answer = forms.CharField(widget=forms.PasswordInput, label="Risposta alla domanda", required=True)

    class Meta(UserCreationForm.Meta):
        model = User
        fields = ("username", "email", "password1", "password2")

    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data["email"]
        if commit:
            user.save()
            # Crea/aggiorna la domanda di sicurezza
            q = self.cleaned_data.get("custom_question") if self.cleaned_data.get("question") == "Altro" else self.cleaned_data.get("question")
            ans = self.cleaned_data.get("answer")
            sec, _ = UserSecurity.objects.get_or_create(user=user)
            sec.question = q
            sec.set_answer(ans)
            sec.save()
        return user

    def clean_email(self):
        """Optionally enforce email uniqueness to avoid ambiguity in password reset."""
        email = self.cleaned_data.get("email")
        if email and User.objects.filter(email__iexact=email).exists():
            raise forms.ValidationError("Esiste già un account con questa email.")
        return email

    def clean(self):
        cleaned = super().clean()
        if cleaned.get("question") == "Altro" and not cleaned.get("custom_question"):
            self.add_error("custom_question", "Inserisci la domanda personalizzata")
        if not cleaned.get("answer"):
            self.add_error("answer", "Inserisci la risposta alla domanda")
        return cleaned


class SecurityQuestionSetupForm(forms.Form):
    question = forms.ChoiceField(choices=[(q, q) for q in SECURITY_QUESTIONS] + [("Altro", "Altro (personalizzata)")], label="Domanda di sicurezza")
    custom_question = forms.CharField(required=False, label="Domanda personalizzata")
    answer = forms.CharField(widget=forms.PasswordInput, label="Risposta")

    def clean(self):
        cleaned = super().clean()
        if cleaned.get("question") == "Altro" and not cleaned.get("custom_question"):
            self.add_error("custom_question", "Inserisci la domanda personalizzata")
        return cleaned

    def save_for_user(self, user: User):
        question = self.cleaned_data["custom_question"] if self.cleaned_data["question"] == "Altro" else self.cleaned_data["question"]
        answer = self.cleaned_data["answer"]
        sec, _created = UserSecurity.objects.get_or_create(user=user)
        sec.question = question
        sec.set_answer(answer)
        sec.save()
        return sec


class SecurityResetStep1Form(forms.Form):
    username = forms.CharField(label="Nome utente")


class SecurityResetStep2Form(SetPasswordForm):
    answer = forms.CharField(widget=forms.PasswordInput, label="Risposta alla domanda")

    def __init__(self, user, *args, **kwargs):
        super().__init__(user, *args, **kwargs)
        # Reorder fields to show 'answer' first, then password fields
        try:
            field_order = ["answer"] + [f for f in self.fields if f != "answer"]
            self.order_fields(field_order)
        except Exception:
            # Fallback: rebuild dict preserving desired order
            fields = self.fields
            new_fields = {"answer": fields["answer"]}
            for name, field in fields.items():
                if name != "answer":
                    new_fields[name] = field
            self.fields = new_fields
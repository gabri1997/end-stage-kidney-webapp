from django.db import models
from django.conf import settings
from django.contrib.auth.models import User
# I modelli sono tabelle nel database che rappresentano dati strutturati.
# Ogni istanza di un modello corrisponde a una riga nella tabella.

class Paziente(models.Model):
    medico = models.ForeignKey(User, on_delete=models.CASCADE, related_name='pazienti')
    nome = models.CharField(max_length=100)
    cognome = models.CharField(max_length=100)
    codice_fiscale = models.CharField(max_length=16, unique=True)
    email = models.EmailField(blank=True, null=True)
    telefono = models.CharField(max_length=20, blank=True, null=True)
    indirizzo = models.CharField(max_length=255, blank=True, null=True)
    eta = models.PositiveIntegerField(null=True, blank=True)

    sesso = models.CharField(
        max_length=1,
        choices=[('M', 'Maschio'), ('F', 'Femmina')],
        blank=True,
        null=True
    )
    eta = models.PositiveIntegerField(blank=True, null=True)

    def __str__(self):
        return f"{self.cognome} {self.nome} ({self.codice_fiscale})"


class MESTC(models.Model):
    # Un paziente può avere più record MEST-C nel tempo → relazione uno-a-molti
    paziente = models.ForeignKey(Paziente, on_delete=models.CASCADE, related_name='mestc_records')
    data_rilevazione = models.DateField()
    M = models.IntegerField(choices=[(0, '0'), (1, '1'), (2, '2'), (3, '3')])
    E = models.IntegerField(choices=[(0, '0'), (1, '1'), (2, '2'), (3, '3')])
    S = models.IntegerField(choices=[(0, '0'), (1, '1'), (2, '2'), (3, '3')])
    T = models.IntegerField(choices=[(0, '0'), (1, '1'), (2, '2'), (3, '3')])
    C = models.IntegerField(choices=[(0, '0'), (1, '1'), (2, '2'), (3, '3')])
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Referto MEST-C"
        verbose_name_plural = "Referti MEST-C"
        ordering = ["-data_rilevazione"]

    def __str__(self):
        return f"MEST-C del {self.data_rilevazione} - {self.paziente}"


def referto_upload_path(instance, filename):
    # File will be uploaded to MEDIA_ROOT/referti/paziente_<id>/<filename>
    return f'referti/paziente_{instance.paziente.id}/{filename}'

class Visita(models.Model):
    # Ogni visita è associata a un paziente (relazione uno-a-molti)
    paziente = models.ForeignKey(Paziente, on_delete=models.CASCADE, related_name='visite')
    data_visita = models.DateField()
    creatinina = models.FloatField(null=True, blank=True)
    egfr = models.FloatField(null=True, blank=True)
    proteinuria = models.FloatField(null=True, blank=True)
    albuminuria = models.FloatField(null=True, blank=True)
    pressione_sistolica = models.IntegerField(null=True, blank=True)
    pressione_diastolica = models.IntegerField(null=True, blank=True)
    note = models.TextField(blank=True, null=True)
    esito_predizione = models.FloatField(null=True, blank=True)
    data_inferenza = models.DateTimeField(null=True, blank=True)
    referto = models.FileField(
        upload_to=referto_upload_path,
        null=True,
        blank=True,
        help_text='Carica un referto in formato PDF, JPG o PNG (max 5MB)'
    )

    medico = models.ForeignKey( 
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='visite_medico'
    )
    class Meta:
        verbose_name = "Visita"
        verbose_name_plural = "Visite"
        ordering = ["-data_visita"]

    def __str__(self):
        return f"Visita del {self.data_visita} - {self.paziente}"

class Predizione(models.Model):
    paziente = models.ForeignKey(Paziente, on_delete=models.CASCADE, related_name='predizioni')
    visita = models.ForeignKey('Visita', on_delete=models.CASCADE, related_name='predizioni', null=True, blank=True)
    mestc = models.ForeignKey('MESTC', on_delete=models.SET_NULL, null=True, blank=True, related_name='predizioni')
    data_predizione = models.DateTimeField(auto_now_add=True)
    probabilita_eskd = models.FloatField()
    ESITO_CHOICES = [
        ('BASSO', 'Basso'),
        ('MEDIO', 'Medio'),
        ('ALTO', 'Alto'),
    ]
    esito = models.CharField(max_length=20, choices=ESITO_CHOICES)

    def __str__(self):
        return f"Predizione {self.id} — {self.paziente} ({self.probabilita_eskd:.2f}%)"

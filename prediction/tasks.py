import dramatiq
from .models import Paziente, Predizione
from .model_loader import predict_risk


@dramatiq.actor
def esegui_inference(paziente_id):
    try:
        paziente = Paziente.objects.get(id=paziente_id)
        print(f"Eseguo inferenza per {paziente.nome} {paziente.cognome}...")

        # Esegui la predizione col tuo modello
        esito, probabilita = predict_risk(paziente)

        # Salva i risultati nel database
        Predizione.objects.create(
            paziente=paziente,
            esito=esito,
            probabilita_eskd=probabilita
        )

        print(f"✅ Inference completata per {paziente_id}")

    except Exception as e:
        print(f"❌ Errore nell’inference: {e}")
import dramatiq
from .models import Paziente, Predizione
from .model_loader import predict_risk


def prepare_patient_data(paziente):
    """
    Prepara i dati del paziente per l'inferenza ML.
    Combina dati del paziente, ultima visita e ultimo MEST-C.
    """
    # Prendi l'ultima visita
    ultima_visita = paziente.visite.order_by('-data_visita').first()
    if not ultima_visita:
        raise ValueError(f"Nessuna visita trovata per paziente {paziente.id}")
    
    # Prendi l'ultimo MEST-C
    ultimo_mestc = paziente.mestc_records.order_by('-data_rilevazione').first()
    if not ultimo_mestc:
        raise ValueError(f"Nessun record MEST-C trovato per paziente {paziente.id}")
    
    # Costruisci il dizionario con tutti i dati necessari
    data = {
        # Dati paziente
        "sesso": paziente.sesso or "M",
        "eta": paziente.eta or paziente.calcola_eta() or 0,
        "iperteso": 1 if (ultima_visita.pressione_sistolica or 0) >= 140 or (ultima_visita.pressione_diastolica or 0) >= 90 else 0,
        
        # Dati MEST-C
        "M": ultimo_mestc.M,
        "E": ultimo_mestc.E,
        "S": ultimo_mestc.S,
        "T": ultimo_mestc.T,
        "C": ultimo_mestc.C,
        
        # Dati visita
        "creatinina": ultima_visita.creatinina or 0,
        "proteinuria": ultima_visita.proteinuria or 0,
        "pressione_sistolica": ultima_visita.pressione_sistolica or 0,
        "pressione_diastolica": ultima_visita.pressione_diastolica or 0,
        
        # Therapy flags (default a 0 se non abbiamo questi dati)
        "Antihypertensive": 0,
        "Immunosuppressants": 0,
        "FishOil": 0,
    }
    
    return data


@dramatiq.actor
def esegui_inference(paziente_id):
    try:
        paziente = Paziente.objects.get(id=paziente_id)
        print(f"Eseguo inferenza per {paziente.nome} {paziente.cognome}...")

        # Prepara i dati del paziente
        patient_data = prepare_patient_data(paziente)

        # Esegui la predizione col modello
        result = predict_risk(patient_data)

        # Salva i risultati nel database
        Predizione.objects.create(
            paziente=paziente,
            esito=result["esito"],
            probabilita_eskd=result["probabilita"],
            anni_eskd=result.get("anni_eskd")
        )

        print(f"✅ Inference completata per {paziente_id}: {result['esito']} ({result['probabilita']}%)")

    except Exception as e:
        print(f"❌ Errore nell'inference per paziente {paziente_id}: {e}")
        import traceback
        traceback.print_exc()

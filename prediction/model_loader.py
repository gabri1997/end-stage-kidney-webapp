import torch
import torch.nn as nn
import numpy as np
import joblib
import os
import json


class MySimpleBinaryNet(nn.Module):
    def __init__(self, input_size, dropout=0.1):
        super(MySimpleBinaryNet, self).__init__()
        self.layers = nn.Sequential(
            nn.Linear(input_size, 100),
            nn.BatchNorm1d(100),
            nn.ELU(),
            nn.Dropout(dropout),
            nn.Linear(100, 100),
            nn.BatchNorm1d(100),
            nn.ELU(),
            nn.Dropout(dropout),
            nn.Linear(100, 100),
            nn.BatchNorm1d(100),
            nn.ELU(),
            nn.Dropout(dropout),
            nn.Linear(100, 100),
            nn.BatchNorm1d(100),
            nn.ELU(),
            nn.Dropout(dropout),
            nn.Linear(100, 1)
        )

    def forward(self, x):
        return self.layers(x)


class MySimpleRegressorNet(nn.Module):
    def __init__(self, input_size, dropout=0.3):
        super(MySimpleRegressorNet, self).__init__()
        self.layers = nn.Sequential(
            nn.Linear(input_size, 125),
            nn.BatchNorm1d(125),
            nn.SELU(),
            nn.Dropout(0.5),

            nn.Linear(125, 125),
            nn.BatchNorm1d(125),
            nn.SELU(),
            nn.Dropout(0.3),

            nn.Linear(125, 125),
            nn.BatchNorm1d(125),
            nn.SELU(),
            nn.Dropout(0.3),

            nn.Linear(125, 1)
        )

    def forward(self, x):
        output = self.layers(x)
        return torch.clamp(output, min=0.0, max=10.0)  # anni limitati a 0–10



def predict_years_to_eskd(data):
    """
    Esegue la predizione degli anni fino a ESKD su un singolo paziente.
    'data' è un dizionario con i campi:
    creatinina, proteinuria, pressione_sistolica, pressione_diastolica,
    M, E, S, T, C, iperteso, sesso, eta, Antihypertensive, Immunosuppressants, FishOil
    """

    base_dir = os.path.dirname(os.path.abspath(__file__))
    save_pth = os.path.join(base_dir, "models")
    save_pth = os.path.join(save_pth, "regression")
    if not os.path.isdir(save_pth):
        raise FileNotFoundError(f"Cartella modelli non trovata: {save_pth}")
    
    # Qua carico i miei pesi, in questo caso il fold migliore per RMSE era il 7 
    # Valori cmq scarsissimi eh, ma ci si prova vecchio mio, la vita è un lungo tirocinio
    scaler_file = os.path.join(save_pth, f"scaler_fold_7.pkl")
    model_file = os.path.join(save_pth, f"best_model_fold_7.pth")

    if not os.path.exists(model_file):
        raise FileNotFoundError("File del modello non trovato")

    scaler = joblib.load(scaler_file)

    sesso_val = 0 if data.get("sesso") == "M" else 1  # M=0, F=1
    # therapy_val = max(
    #     data.get("Antihypertensive", 0),
    #     data.get("Immunosuppressants", 0),
    #     data.get("FishOil", 0)
    # )
    # ['Gender', 'Age', 'Hypertension', 'M', 'E', 'S', 'T', 'C', 'Proteinuria', 'Creatinine', 'Antihypertensive', 'Immunosuppressants', 'FishOil']
    values = [
        sesso_val,
        float(data.get("eta", 0)),
        float(data.get("iperteso", 0)),
        float(data.get("M", 0)),
        float(data.get("E", 0)),    
        float(data.get("S", 0)),
        float(data.get("T", 0)),
        float(data.get("C", 0)),
        float(data.get("proteinuria", 0)),
        float(data.get("creatinina", 0)),
        float(data.get("Antihypertensive", 0)),
        float(data.get("Immunosuppressants", 0)),
        float(data.get("FishOil", 0))
    ]

    X = np.array(values, dtype=np.float32).reshape(1, -1)
    X_scaled = scaler.transform(X)

    model = MySimpleRegressorNet(input_size=X_scaled.shape[1], dropout=0.5)
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    model.load_state_dict(torch.load(model_file, map_location=device))
    model.to(device)
    model.eval()

    with torch.no_grad():
        X_tensor = torch.tensor(X_scaled, dtype=torch.float32).to(device)
        output = model(X_tensor)
        years = output.item()   
    
    return round(years, 2)


def predict_risk(data):
    """
    Esegue la predizione del rischio ESKD su un singolo paziente.
    'data' è un dizionario con i campi:
    creatinina, proteinuria, pressione_sistolica, pressione_diastolica,
    M, E, S, T, C, iperteso, sesso, eta, Antihypertensive, Immunosuppressants, FishOil
    """

    base_dir = os.path.dirname(os.path.abspath(__file__))
    save_pth = os.path.join(base_dir, "models")
    save_pth = os.path.join(save_pth, "classification")
    if not os.path.isdir(save_pth):
        raise FileNotFoundError(f"Cartella modelli non trovata: {save_pth}")


    # Carica scaler
    scaler_file = os.path.join(save_pth, f"scaler_fold_8.pkl")
    model_file = os.path.join(save_pth, f"best_model_fold_8.pth")

    if not os.path.exists(scaler_file) or not os.path.exists(model_file):
        raise FileNotFoundError("File del modello o scaler non trovati")

    scaler = joblib.load(scaler_file)

    dropout = 0.5

    # --- Prepara i dati in input ---
    sesso_val = 0 if data.get("sesso") == "M" else 1  # M=0, F=1
    therapy_val = max(
        data.get("Antihypertensive", 0),
        data.get("Immunosuppressants", 0),
        data.get("FishOil", 0)
    )

    values = [
        sesso_val,                              # 1. Gender
        float(data.get("eta", 0)),              # 2. Age
        float(data.get("iperteso", 0)),         # 3. Hypertension
        float(data.get("M", 0)),                # 4. M
        float(data.get("E", 0)),                # 5. E
        float(data.get("S", 0)),                # 6. S
        float(data.get("T", 0)),                # 7. T
        float(data.get("C", 0)),                # 8. C
        float(data.get("proteinuria", 0)),      # 9. Proteinuria
        float(data.get("creatinina", 0)),       # 10. Creatinine
        float(therapy_val)                      # 11. Therapy
    ]

    print("\n Valori finali passati allo scaler e al modello:")
    for i, name in enumerate(["Gender", "Age", "Hypertension", "M", "E", "S", "T", "C", "Proteinuria", "Creatinine", "Therapy"]):
        print(f"{i+1:02d}. {name:12s} = {values[i]}")


    # Se nei valori ci sono None, sostituiscili con 0
    values = [0 if v is None else v for v in values]
    # Voglio togliere pressione_diastolica e pressione_sistolica per evitare ridondanza
    X = np.array(values, dtype=np.float32).reshape(1, -1)
    # Controllo che il numero di features sia corretto
    if X.shape[1] != scaler.mean_.shape[0]:
        print("\nFEATURE MISMATCH DETECTED")
        print(f"→ Model expects {scaler.mean_.shape[0]} features, but received {X.shape[1]}")
        print("Values provided:")
        for name, val in zip(
            ["Gender", "Age", "Hypertension", "M", "E", "S", "T", "C", "Proteinuria", "Creatinine", "Therapy"],
            values
        ):
            print(f"{name:12s} = {val}")
        raise ValueError("Feature count mismatch between input and scaler.")

    X_scaled = scaler.transform(X)

    # --- Inference ---
    model = MySimpleBinaryNet(input_size=X_scaled.shape[1], dropout=dropout)
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    model.load_state_dict(torch.load(model_file, map_location=device))
    model.to(device)
    model.eval()

    with torch.no_grad():
        X_tensor = torch.tensor(X_scaled, dtype=torch.float32).to(device)
        output = model(X_tensor)
        prob = torch.sigmoid(output).item()

    prob_percent = round(prob * 100, 2)
    
    # Determina l'esito in base alla probabilità
    if prob_percent >= 70:
        esito = "ALTO"
    elif prob_percent >= 30:
        esito = "MEDIO"
    else:
        esito = "BASSO"

    if esito == "ALTO" or esito == "MEDIO": 
        print(f"\n Attenzione: Rischio ESKD ALTO ({prob_percent}%)")
        years = predict_years_to_eskd(data)
        print(f"   → Predizione anni fino a ESKD: {years:.2f} anni")
    else:
        print(f"\n Rischio ESKD BASSO ({prob_percent}%)")
    return {"probabilita": prob_percent, "esito": esito, "anni_eskd": years if esito != "BASSO" else None}

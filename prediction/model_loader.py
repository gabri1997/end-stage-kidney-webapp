import torch
import torch.nn as nn
import numpy as np
import joblib
import os
import json

# --- MODELLO ---
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
            nn.Linear(100, 1)
        )

    def forward(self, x):
        return self.layers(x)


# --- FUNZIONE DI PREDIZIONE ---
def predict_risk(data):
    """
    Esegue la predizione del rischio ESKD su un singolo paziente.
    'data' è un dizionario con i campi:
    creatinina, proteinuria, pressione_sistolica, pressione_diastolica,
    M, E, S, T, C, iperteso, sesso, eta, Antihypertensive, Immunosuppressants, FishOil
    """

    base_dir = os.path.dirname(os.path.abspath(__file__))
    save_pth = os.path.join(base_dir, "models")
    if not os.path.isdir(save_pth):
        raise FileNotFoundError(f"⚠️ Cartella modelli non trovata: {save_pth}")


    # Carica scaler
    scaler_file = os.path.join(save_pth, f"scaler_fold_8.pkl")
    model_file = os.path.join(save_pth, f"best_model_fold_8.pth")

    if not os.path.exists(scaler_file) or not os.path.exists(model_file):
        raise FileNotFoundError("⚠️ File del modello o scaler non trovati")

    scaler = joblib.load(scaler_file)

    dropout = 0.5

    # --- Prepara i dati in input ---
    sesso_val = 0 if data.get("sesso") == "M" else 1  # M=0, F=1
    therapy = max(data.get("Antihypertensive", 0), data.get("Immunosuppressants", 0), data.get("FishOil", 0))

    values = [
        data.get("creatinina", 0),
        data.get("proteinuria", 0),
        data.get("pressione_sistolica", 0),
        data.get("pressione_diastolica", 0),
        data.get("M", 0),
        data.get("E", 0),
        data.get("S", 0),
        data.get("T", 0),
        data.get("C", 0),
        data.get("iperteso", 0),
        sesso_val,
        data.get("eta", 0),
        therapy
    ]

    X = np.array(values, dtype=np.float32).reshape(1, -1)
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
    esito = "Positivo" if prob >= 0.5 else "Negativo"

    return {"probabilita": prob_percent, "esito": esito}

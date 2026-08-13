import os
from pathlib import Path
import numpy as np
import joblib

MODEL_PATH = Path(os.getenv("MODEL_PATH", Path(__file__).resolve().parents[2] / "ml" / "model.pkl"))

def score(features):
    if not MODEL_PATH.exists():
        return 0.0
    decision = float(joblib.load(MODEL_PATH).decision_function(np.array([features]))[0])
    return max(0.0, min(100.0, 50 - decision * 200))

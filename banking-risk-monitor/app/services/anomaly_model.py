import os
from pathlib import Path
from functools import lru_cache
import numpy as np
import joblib

MODEL_PATH = Path(os.getenv("MODEL_PATH", Path(__file__).resolve().parents[2] / "ml" / "model.pkl"))

@lru_cache(maxsize=1)
def model():
    """Load the trained model once per application process, not once per row."""
    return joblib.load(MODEL_PATH) if MODEL_PATH.exists() else None

def score(features):
    trained_model = model()
    if trained_model is None:
        return 0.0
    decision = float(trained_model.decision_function(np.array([features]))[0])
    return max(0.0, min(100.0, 50 - decision * 200))

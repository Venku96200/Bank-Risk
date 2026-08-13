"""Train the *unsupervised* Isolation Forest model.

The script can use either the small project generator output or the supplied
bank_fraud.csv.  Crucially, `is_fraud` and `fraud_type` are never read: they
are labels and must not influence an unsupervised anomaly model.
"""
from argparse import ArgumentParser
from pathlib import Path
import sys
import joblib
import numpy as np
import pandas as pd
from sklearn.ensemble import IsolationForest
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

PROJECT_COLUMNS = ["transaction_id", "customer_id", "timestamp", "amount", "account_age_days"]
BANK_COLUMNS = ["transaction_id", "customer_id", "transaction_date", "transaction_time", "hour_of_day",
                "account_age_years", "transaction_amount", "transaction_freq_monthly",
                "time_since_last_txn_hrs", "device_type", "city"]

def project_features(path: Path) -> np.ndarray:
    df = pd.read_csv(path, usecols=PROJECT_COLUMNS)
    df["timestamp"] = pd.to_datetime(df["timestamp"])
    average = df.groupby("customer_id")["amount"].transform("mean")
    return np.column_stack([np.log1p(df.amount), df.amount / average.clip(lower=1),
        np.ones(len(df)), np.ones(len(df)), np.full(len(df), 1440), np.zeros(len(df)),
        np.zeros(len(df)), df.timestamp.dt.hour, df.account_age_days])

def bank_fraud_features(path: Path, sample_size: int) -> np.ndarray:
    # `usecols` intentionally omits `is_fraud` and `fraud_type`.
    df = pd.read_csv(path, usecols=BANK_COLUMNS)
    if len(df) > sample_size:
        df = df.sample(sample_size, random_state=42)
    df["timestamp"] = pd.to_datetime(df.transaction_date + " " + df.transaction_time)
    df = df.sort_values(["customer_id", "timestamp"])
    average = df.groupby("customer_id")["transaction_amount"].transform("mean")
    # First observed device/city is the customer's baseline; later changes are signals.
    first_device = df.groupby("customer_id").device_type.transform("first")
    first_city = df.groupby("customer_id").city.transform("first")
    minutes = (df.time_since_last_txn_hrs.fillna(24) * 60).clip(upper=10080)
    # The source has monthly frequency rather than exact 10-minute/24-hour counts.
    # It is retained as a behavioural-frequency proxy in both velocity positions.
    frequency = df.transaction_freq_monthly.fillna(0)
    return np.column_stack([np.log1p(df.transaction_amount),
        df.transaction_amount / average.clip(lower=1), frequency / 30, frequency,
        minutes, (df.device_type != first_device).astype(int), (df.city != first_city).astype(int),
        df.hour_of_day, (df.account_age_years * 365).clip(lower=0)])

def train(source: Path, sample_size: int = 100_000):
    features = bank_fraud_features(source, sample_size) if "transaction_amount" in pd.read_csv(source, nrows=1).columns else project_features(source)
    # Standardisation prevents large-scale features such as age dominating the forest.
    model = make_pipeline(StandardScaler(), IsolationForest(n_estimators=300, contamination=0.05, random_state=42, n_jobs=-1))
    model.fit(features)
    output = Path(__file__).parent / "model.pkl"
    joblib.dump(model, output)
    print(f"Saved unsupervised Isolation Forest trained on {len(features):,} unlabeled records to {output}")

if __name__ == "__main__":
    parser = ArgumentParser()
    parser.add_argument("--source", type=Path, default=ROOT / "data" / "transactions.csv")
    parser.add_argument("--sample-size", type=int, default=100_000)
    args = parser.parse_args()
    train(args.source, args.sample_size)

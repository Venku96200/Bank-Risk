"""
Train an unsupervised Isolation Forest model.
"""

import pickle
import numpy as np
import pandas as pd

from sklearn.ensemble import IsolationForest
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler


# --------------------------------------------------
# 1. Columns used from the datasets
# --------------------------------------------------

PROJECT_COLUMNS = [
    "transaction_id",
    "customer_id",
    "timestamp",
    "amount",
    "account_age_days"
]

BANK_COLUMNS = [
    "transaction_id",
    "customer_id",
    "transaction_date",
    "transaction_time",
    "hour_of_day",
    "account_age_years",
    "transaction_amount",
    "transaction_freq_monthly",
    "time_since_last_txn_hrs",
    "device_type",
    "city"
]


# --------------------------------------------------
# 2. Feature engineering for project dataset
# --------------------------------------------------

def project_features(path):

    df = pd.read_csv(path, usecols=PROJECT_COLUMNS)

    # Convert timestamp from string to datetime
    df["timestamp"] = pd.to_datetime(df["timestamp"])

    # Average transaction amount for each customer
    average = df.groupby("customer_id")["amount"].transform("mean")

    features = np.column_stack([
        np.log1p(df["amount"]),
        df["amount"] / average.clip(lower=1),

        # These features are not available in this dataset,
        # so we use default values.
        np.ones(len(df)),
        np.ones(len(df)),
        np.full(len(df), 1440),
        np.zeros(len(df)),
        np.zeros(len(df)),

        # Features that are available
        df["timestamp"].dt.hour,
        df["account_age_days"]
    ])

    return features


# --------------------------------------------------
# 3. Feature engineering for bank fraud dataset
# --------------------------------------------------

def bank_fraud_features(path, sample_size):

    df = pd.read_csv(path, usecols=BANK_COLUMNS)

    # Use only sample_size rows if dataset is larger
    if len(df) > sample_size:
        df = df.sample(sample_size, random_state=42)

    # Combine date and time into one timestamp
    df["timestamp"] = pd.to_datetime(
        df["transaction_date"] + " " + df["transaction_time"]
    )

    # Sort transactions customer-wise and chronologically
    df = df.sort_values(["customer_id", "timestamp"])

    # Average transaction amount for each customer
    average = df.groupby("customer_id")["transaction_amount"].transform("mean")

    # First device used by each customer
    first_device = df.groupby("customer_id")["device_type"].transform("first")

    # First city used by each customer
    first_city = df.groupby("customer_id")["city"].transform("first")

    # Time since previous transaction, in minutes
    minutes = (
        df["time_since_last_txn_hrs"]
        .fillna(24)
        * 60
    ).clip(upper=10080)

    # Monthly transaction frequency
    frequency = df["transaction_freq_monthly"].fillna(0)

    features = np.column_stack([
        # 1. Transaction amount
        np.log1p(df["transaction_amount"]),

        # 2. Amount compared to customer's average
        df["transaction_amount"] / average.clip(lower=1),

        # 3. Approximate 10-minute transaction velocity
        frequency / 30,

        # 4. Monthly transaction frequency
        frequency,

        # 5. Minutes since previous transaction
        minutes,

        # 6. New device?
        (df["device_type"] != first_device).astype(int),

        # 7. New city?
        (df["city"] != first_city).astype(int),

        # 8. Transaction hour
        df["hour_of_day"],

        # 9. Account age in days
        (df["account_age_years"] * 365).clip(lower=0)
    ])

    return features


# --------------------------------------------------
# 4. Train the model
# --------------------------------------------------

def train(source, sample_size=100_000):

    # Read only the first row to determine which dataset we have
    columns = pd.read_csv(source, nrows=1).columns

    if "transaction_amount" in columns:
        features = bank_fraud_features(source, sample_size)
    else:
        features = project_features(source)

    print("Number of transactions:", len(features))
    print("Number of features:", features.shape[1])

    # StandardScaler + Isolation Forest
    model = make_pipeline(

        StandardScaler(),

        IsolationForest(
            n_estimators=300,
            contamination=0.05,
            random_state=42,
            n_jobs=-1
        )
    )

    # Train the model
    model.fit(features)

    # Save the entire pipeline
    with open("ml/model.pkl", "wb") as file:
        pickle.dump(model, file)

    print("Model saved to ml/model.pkl")


# --------------------------------------------------
# 5. Run training
# --------------------------------------------------

source = "data/transactions.csv"

train(source)

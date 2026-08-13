from pathlib import Path
import sys, joblib, pandas as pd, numpy as np
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.ensemble import IsolationForest
ROOT=Path(__file__).resolve().parents[1]; sys.path.insert(0,str(ROOT))
from app.services.feature_engineering import vector
def train(csv_path=ROOT/"data"/"transactions.csv"):
    df=pd.read_csv(csv_path); df["timestamp"]=pd.to_datetime(df["timestamp"]); avg=df.groupby("customer_id").amount.transform("mean")
    features=np.array([[np.log1p(a),a/max(b,1),1,1,1440,0,0,t.hour,age] for a,b,t,age in zip(df.amount,avg,df.timestamp,df.account_age_days)])
    model=make_pipeline(StandardScaler(),IsolationForest(n_estimators=300,contamination=.05,random_state=42)); model.fit(features)
    output=Path(__file__).parent/"model.pkl"; joblib.dump(model,output); print(output)
if __name__=="__main__": train()

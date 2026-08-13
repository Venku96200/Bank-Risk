"""Create reproducible CSV data with intentional suspicious patterns."""
from datetime import datetime, timedelta
from pathlib import Path
import numpy as np, pandas as pd
rng=np.random.default_rng(42)
def generate(n=6000):
    customers=[f"C{n:04d}" for n in range(300)]; avgs={c:rng.uniform(25,400) for c in customers}; start=datetime(2026,1,1)
    rows=[]
    for i in range(n):
        c=rng.choice(customers); anomaly=rng.random()<.07; avg=avgs[c]; amount=float(rng.lognormal(np.log(avg),.45))
        if anomaly: amount*=rng.integers(5,16)
        stamp=start+timedelta(minutes=int(rng.integers(0,60*24*90)))
        if anomaly and rng.random()<.4: stamp=stamp.replace(hour=int(rng.choice([1,2,3,23])))
        rows.append({"transaction_id":f"TX{i:06d}","customer_id":c,"timestamp":stamp.isoformat(),"amount":round(amount,2),"merchant_category":rng.choice(["retail","grocery","travel","cash"]),"location":f"City-{rng.integers(1,20) if anomaly else int(c[1:])%5}","device_id":f"D{rng.integers(1000,9999) if anomaly else int(c[1:])%3}","transaction_type":"card","account_age_days":int(rng.integers(30,2000))})
    return pd.DataFrame(rows)
if __name__=="__main__":
    output=Path(__file__).parent/"transactions.csv"; generate().to_csv(output,index=False); print(output)

from datetime import timedelta
import math
from sqlalchemy import select
from app.models import Transaction

def transaction_context(db, customer_id, timestamp, device, location, known_devices, known_locations, start, end):
    prior = db.scalars(select(Transaction).where(Transaction.customer_id == customer_id, Transaction.timestamp < timestamp).order_by(Transaction.timestamp.desc())).all()
    ten, day = timestamp-timedelta(minutes=10), timestamp-timedelta(hours=24)
    return {"velocity_10m": sum(x.timestamp >= ten for x in prior)+1, "velocity_24h": sum(x.timestamp >= day for x in prior)+1,
            "minutes_since_previous_transaction": (timestamp-prior[0].timestamp).total_seconds()/60 if prior else 1440.0,
            "new_device": device not in known_devices, "new_location": location not in known_locations,
            "unusual_hour": not start <= timestamp.hour <= end}

def vector(amount, avg, c, timestamp, age):
    return [math.log1p(amount), amount/max(avg,1), c["velocity_10m"], c["velocity_24h"], c["minutes_since_previous_transaction"], int(c["new_device"]), int(c["new_location"]), timestamp.hour, age]

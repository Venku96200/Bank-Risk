import csv, io, json
from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from sqlalchemy import select
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import Customer, Transaction
from app.schemas import TransactionCreate
from app.services.feature_engineering import transaction_context, vector
from app.services.rule_engine import assess_rules
from app.services.anomaly_model import score as ml_score
from app.services.risk_scoring import calculate_final_score
from app.services.alert_service import create_alert_if_needed

router = APIRouter(prefix="/transactions", tags=["transactions"])

def serialise(t):
    return {"id":t.id,"transaction_id":t.transaction_id,"amount":t.amount,"timestamp":t.timestamp,"risk_level":t.risk_level,"final_score":t.final_score,"rule_score":t.rule_score,"ml_score":t.ml_score,"reasons":json.loads(t.reasons)}

def assess(db, payload):
    customer = db.scalar(select(Customer).where(Customer.customer_ref == payload.customer_id))
    if not customer:
        customer = Customer(customer_ref=payload.customer_id, average_amount=payload.amount, known_devices=payload.device_id, known_locations=payload.location)
        db.add(customer); db.flush()
    devices, locations = customer.known_devices.split("|") if customer.known_devices else [], customer.known_locations.split("|") if customer.known_locations else []
    ctx = transaction_context(db, customer.id, payload.timestamp, payload.device_id, payload.location, devices, locations, customer.normal_start_hour, customer.normal_end_hour)
    rules = assess_rules(payload.amount, customer.average_amount, ctx["new_device"], ctx["new_location"], ctx["unusual_hour"], ctx["velocity_10m"])
    ml = ml_score(vector(payload.amount, customer.average_amount, ctx, payload.timestamp, payload.account_age_days))
    final, level = calculate_final_score(rules.score, ml)
    values = payload.model_dump()
    values.pop("customer_id")  # API customer reference maps to the Customer row above.
    txn = Transaction(**values, customer_id=customer.id, customer_average=customer.average_amount, rule_score=rules.score, ml_score=ml, final_score=final, risk_level=level, reasons=json.dumps(rules.reasons))
    db.add(txn); db.flush(); create_alert_if_needed(db, txn)
    if payload.device_id not in devices: customer.known_devices = "|".join(devices+[payload.device_id])
    if payload.location not in locations: customer.known_locations = "|".join(locations+[payload.location])
    customer.average_amount = (customer.average_amount + payload.amount) / 2
    db.commit(); db.refresh(txn); return serialise(txn)

@router.post("")
def create(payload: TransactionCreate, db: Session = Depends(get_db)): return assess(db, payload)
@router.get("")
def list_transactions(limit:int=100, db:Session=Depends(get_db)): return [serialise(x) for x in db.scalars(select(Transaction).order_by(Transaction.timestamp.desc()).limit(limit))]
@router.get("/{transaction_id}")
def get_transaction(transaction_id:int, db:Session=Depends(get_db)):
    t=db.get(Transaction,transaction_id)
    if not t: raise HTTPException(404,"Transaction not found")
    return serialise(t)
@router.post("/bulk")
async def bulk(file: UploadFile = File(...), db: Session = Depends(get_db)):
    rows=list(csv.DictReader(io.StringIO((await file.read()).decode())))
    return {"created":[assess(db, TransactionCreate(**r)) for r in rows]}

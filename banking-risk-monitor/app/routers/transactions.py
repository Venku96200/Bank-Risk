import csv, io, json
from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from pydantic import ValidationError
from sqlalchemy import delete, select
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import Customer, RiskAlert, RiskReview, Transaction
from app.schemas import TransactionCreate
from app.services.feature_engineering import transaction_context, vector
from app.services.rule_engine import assess_rules
from app.services.anomaly_model import score as ml_score
from app.services.risk_scoring import calculate_final_score
from app.services.alert_service import create_alert_if_needed

router = APIRouter(prefix="/transactions", tags=["transactions"])

def serialise(t):
    return {"id":t.id,"transaction_id":t.transaction_id,"amount":t.amount,"timestamp":t.timestamp,"risk_level":t.risk_level,"final_score":t.final_score,"rule_score":t.rule_score,"ml_score":t.ml_score,"reasons":json.loads(t.reasons)}

def assess(db, payload, commit: bool = True):
    # Transaction IDs are external identifiers, so accepting a duplicate would
    # corrupt the audit trail. Return a client error before attempting an insert.
    if db.scalar(select(Transaction.id).where(Transaction.transaction_id == payload.transaction_id)):
        raise HTTPException(status_code=409, detail=f"Transaction ID '{payload.transaction_id}' already exists")
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
    if commit:
        db.commit()
    else:
        db.flush()
    db.refresh(txn)
    return serialise(txn)

@router.post("")
def create(payload: TransactionCreate, db: Session = Depends(get_db)): return assess(db, payload)
@router.get("")
def list_transactions(limit:int=100, db:Session=Depends(get_db)): return [serialise(x) for x in db.scalars(select(Transaction).order_by(Transaction.timestamp.desc()).limit(limit))]
@router.delete("")
def clear_transactions(db: Session = Depends(get_db)):
    review_count = db.execute(delete(RiskReview)).rowcount or 0
    alert_count = db.execute(delete(RiskAlert)).rowcount or 0
    txn_count = db.execute(delete(Transaction)).rowcount or 0
    customer_count = db.execute(delete(Customer)).rowcount or 0
    db.commit()
    return {"deleted": txn_count, "alerts": alert_count, "reviews": review_count, "customers": customer_count}
@router.get("/{transaction_id}")
def get_transaction(transaction_id:int, db:Session=Depends(get_db)):
    t=db.get(Transaction,transaction_id)
    if not t: raise HTTPException(404,"Transaction not found")
    return serialise(t)
@router.post("/bulk")
async def bulk(file: UploadFile = File(...), db: Session = Depends(get_db)):
    """Assess a CSV while returning actionable errors for invalid individual rows."""
    if not file.filename or not file.filename.lower().endswith(".csv"):
        raise HTTPException(400, "Upload a CSV file")
    try:
        rows = list(csv.DictReader(io.StringIO((await file.read()).decode("utf-8-sig"))))
    except UnicodeDecodeError as exc:
        raise HTTPException(400, "CSV must be UTF-8 encoded") from exc
    if not rows:
        raise HTTPException(400, "CSV contains no transaction rows")

    required = {"transaction_id", "customer_id", "amount", "location", "device_id", "account_age_days"}
    columns = set(rows[0])
    if missing := required - columns:
        raise HTTPException(422, f"Missing required columns: {', '.join(sorted(missing))}")
    if not ({"timestamp", "date_time"} & columns):
        raise HTTPException(422, "Missing a timestamp column. Use 'timestamp' or 'date_time'.")

    created, errors = [], []
    for row_number, row in enumerate(rows, start=2):
        # Some exports use date_time and include an is_anomaly label. The label is
        # deliberately not consumed: the production scorer assesses behaviour itself.
        row["timestamp"] = row.get("timestamp") or row.get("date_time")
        try:
            created.append(assess(db, TransactionCreate(**row), commit=False))
        except ValidationError as exc:
            errors.append({"row": row_number, "error": exc.errors()[0]["msg"]})
        except HTTPException as exc:
            errors.append({"row": row_number, "error": str(exc.detail)})
    db.commit()
    return {"created": created, "errors": errors}

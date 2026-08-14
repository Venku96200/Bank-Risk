import json
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import RiskAlert, RiskReview
from app.schemas import ReviewUpdate
from app.services.rag_explainer import explain

router=APIRouter(prefix="/alerts",tags=["alerts"])

def item(a): return {"id":a.id,"level":a.level,"status":a.status,"created_at":a.created_at,"transaction_id":a.transaction_id,"score":a.transaction.final_score}

def transaction_item(t):
    return {
        "id": t.id,
        "transaction_id": t.transaction_id,
        "customer_id": t.customer.customer_ref if t.customer else None,
        "timestamp": t.timestamp,
        "amount": t.amount,
        "merchant_category": t.merchant_category,
        "location": t.location,
        "device_id": t.device_id,
        "transaction_type": t.transaction_type,
        "account_age_days": t.account_age_days,
        "customer_average": t.customer_average,
        "rule_score": t.rule_score,
        "ml_score": t.ml_score,
        "final_score": t.final_score,
        "risk_level": t.risk_level,
        "reasons": json.loads(t.reasons),
    }

@router.get("")
def list_alerts(level:str|None=None,status:str|None=None,db:Session=Depends(get_db)):
    q=select(RiskAlert).order_by(RiskAlert.created_at.desc())
    if status is not None:
        q=q.where(RiskAlert.status==status)
    else:
        q=q.where(RiskAlert.status != "CLEARED")
    if level:q=q.where(RiskAlert.level==level)
    return [item(a) for a in db.scalars(q)]

@router.delete("")
def clear_alerts(db:Session=Depends(get_db)):
    alerts = db.scalars(select(RiskAlert).where(RiskAlert.status != "CLEARED")).all()
    for alert in alerts:
        alert.status = "CLEARED"
    db.commit()
    return {"cleared": len(alerts), "status": "CLEARED"}

@router.get("/{alert_id}")
def get_alert(alert_id:int,db:Session=Depends(get_db)):
    a=db.get(RiskAlert,alert_id)
    if not a: raise HTTPException(404,"Alert not found")
    return item(a)|{"transaction": transaction_item(a.transaction), "reasons":json.loads(a.transaction.reasons), "rag_explanation":a.rag_explanation}

@router.get("/{alert_id}/explain")
def get_explanation(alert_id:int,db:Session=Depends(get_db)):
    a=db.get(RiskAlert,alert_id)
    if not a: raise HTTPException(404,"Alert not found")
    result=explain(json.loads(a.transaction.reasons)); a.rag_explanation=result["explanation"]; db.commit()
    return result

@router.patch("/{alert_id}/review")
def review(alert_id:int,payload:ReviewUpdate,db:Session=Depends(get_db)):
    a=db.get(RiskAlert,alert_id)
    if not a: raise HTTPException(404,"Alert not found")
    action=payload.action.upper()
    if action not in {"REVIEWED","FALSE_POSITIVE","ESCALATED"}: raise HTTPException(400,"Use REVIEWED, FALSE_POSITIVE, or ESCALATED")
    a.status=action; db.add(RiskReview(alert_id=a.id,action=action,notes=payload.notes)); db.commit()
    return item(a)

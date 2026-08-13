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
@router.get("")
def list_alerts(level:str|None=None,status:str|None=None,db:Session=Depends(get_db)):
    q=select(RiskAlert).order_by(RiskAlert.created_at.desc())
    if level:q=q.where(RiskAlert.level==level)
    if status:q=q.where(RiskAlert.status==status)
    return [item(a) for a in db.scalars(q)]
@router.get("/{alert_id}")
def get_alert(alert_id:int,db:Session=Depends(get_db)):
    a=db.get(RiskAlert,alert_id)
    if not a: raise HTTPException(404,"Alert not found")
    return item(a)|{"reasons":json.loads(a.transaction.reasons),"rag_explanation":a.rag_explanation}
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

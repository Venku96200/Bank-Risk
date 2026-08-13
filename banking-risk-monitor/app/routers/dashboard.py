from fastapi import APIRouter, Depends
from sqlalchemy import func, select
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import RiskAlert, Transaction
router=APIRouter(prefix="/dashboard",tags=["dashboard"])
@router.get("/summary")
def summary(db:Session=Depends(get_db)):
    return {"total_transactions":db.scalar(select(func.count(Transaction.id))) or 0,"open_alerts":db.scalar(select(func.count(RiskAlert.id)).where(RiskAlert.status=="OPEN")) or 0,"high_risk":db.scalar(select(func.count(Transaction.id)).where(Transaction.risk_level=="HIGH")) or 0,"critical":db.scalar(select(func.count(Transaction.id)).where(Transaction.risk_level=="CRITICAL")) or 0}
@router.get("/trends")
def trends(db:Session=Depends(get_db)):
    rows=db.execute(select(Transaction.risk_level,func.count(Transaction.id)).group_by(Transaction.risk_level)).all()
    return {"distribution":dict(rows)}

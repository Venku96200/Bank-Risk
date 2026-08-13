from app.models import RiskAlert

def create_alert_if_needed(db, transaction):
    if transaction.risk_level not in {"HIGH", "CRITICAL"}: return None
    alert = RiskAlert(transaction_id=transaction.id, level=transaction.risk_level)
    db.add(alert); db.flush()
    return alert

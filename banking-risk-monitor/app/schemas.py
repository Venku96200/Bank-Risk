from datetime import datetime
from pydantic import BaseModel, Field

class TransactionCreate(BaseModel):
    transaction_id: str
    customer_id: str
    timestamp: datetime
    amount: float = Field(gt=0)
    merchant_category: str = "retail"
    location: str
    device_id: str
    transaction_type: str = "card"
    account_age_days: int = Field(ge=0)

class ReviewUpdate(BaseModel):
    action: str
    notes: str | None = None

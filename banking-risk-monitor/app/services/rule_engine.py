"""Deterministic, explainable rules used alongside the anomaly model."""
from dataclasses import dataclass

@dataclass
class RuleResult:
    score: int
    reasons: list[str]

def assess_rules(amount: float, customer_average: float, new_device: bool,
                 new_location: bool, unusual_hour: bool, velocity_10m: int) -> RuleResult:
    points, reasons = 0, []
    ratio = amount / max(customer_average, 1.0)
    if ratio > 5:
        points += 25; reasons.append(f"Amount is {ratio:.1f}x customer average")
    if new_device:
        points += 20; reasons.append("New device detected")
    if new_location:
        points += 20; reasons.append("New location detected")
    if unusual_hour:
        points += 10; reasons.append("Transaction occurred outside customer's normal hours")
    if velocity_10m >= 5:
        points += 15; reasons.append(f"Velocity burst: {velocity_10m} transactions in 10 minutes")
    return RuleResult(min(points, 100), reasons)

def normalized_anomaly_score(raw_score: float) -> float:
    return max(0.0, min(100.0, raw_score))

def calculate_final_score(rule_score: float, ml_score: float) -> tuple[int, str]:
    score = round(0.6 * max(0, min(100, rule_score)) + 0.4 * normalized_anomaly_score(ml_score))
    level = "LOW" if score <= 30 else "MEDIUM" if score <= 60 else "HIGH" if score <= 80 else "CRITICAL"
    return score, level

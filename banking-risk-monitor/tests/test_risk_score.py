from app.services.risk_scoring import calculate_final_score
def test_score_is_bounded():
    assert calculate_final_score(999,999)[0]==100
    assert calculate_final_score(-9,-4)[0]==0

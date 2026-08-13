from app.services.rule_engine import assess_rules
def test_amount_rule_threshold():
    assert assess_rules(501,100,False,False,False,0).score==25
def test_velocity_rule():
    assert "Velocity burst" in assess_rules(10,100,False,False,False,5).reasons[0]

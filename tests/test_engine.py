from app.engine import run_checks


def test_composable_task_checks():
    passed, details = run_checks("Billing refund requested", {"contains_all": ["billing", "refund"], "contains_none": ["password"]})
    assert passed is True
    assert details == {"contains_all": True, "contains_none": True}


def test_exact_check_fails_for_wrong_output():
    passed, details = run_checks("shipping", {"exact_match": "billing"})
    assert passed is False
    assert details["exact_match"] is False

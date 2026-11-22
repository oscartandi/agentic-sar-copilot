import pytest
from fastapi.testclient import TestClient
from src.api import app
from src.database import fetch_customer_and_txns, get_connection, init_and_seed_db
from src.models import EscalationPriority, SubjectRole
from src.orchestrator import run_sar_investigation
from src.validator import validate_sar_narrative
from src.agents.txn_agent import analyze_transactions
from src.agents.typology_agent import evaluate_typologies
from src.models import EvidenceBundle

client = TestClient(app)


def _get_test_db():
    conn = get_connection(":memory:")
    init_and_seed_db(conn)
    return conn


def test_money_mule_and_layering():
    conn = _get_test_db()
    report = run_sar_investigation(conn, "CUST_101")
    assert report.subject_role == SubjectRole.COMPLICIT_ACTOR
    assert "MONEY_MULE_PASS_THROUGH" in report.detected_typologies
    assert "ML_LAYERING" in report.detected_typologies
    assert report.recommended_action == EscalationPriority.HIGH_PRIORITY_SAR
    assert report.guardrail_verified is True


def test_ml_suspicious_source_of_funds():
    conn = _get_test_db()
    report = run_sar_investigation(conn, "CUST_102")
    assert "ML_SUSPICIOUS_SOF" in report.detected_typologies
    assert report.subject_role == SubjectRole.COMPLICIT_ACTOR
    assert report.guardrail_verified is True


def test_elder_financial_exploitation_age_60_threshold():
    conn = _get_test_db()
    report = run_sar_investigation(conn, "CUST_103")
    assert report.customer_age == 64
    assert "ELDER_FINANCIAL_EXPLOITATION" in report.detected_typologies
    assert report.subject_role == SubjectRole.VICTIM
    assert report.recommended_action == EscalationPriority.HIGH_PRIORITY_SAR
    assert "SUSPECTED VICTIM" in report.sar_narrative


def test_account_takeover_ato():
    conn = _get_test_db()
    report = run_sar_investigation(conn, "CUST_104")
    assert "ACCOUNT_TAKEOVER_ATO" in report.detected_typologies
    assert report.subject_role == SubjectRole.VICTIM
    assert report.guardrail_verified is True


def test_scam_victim_authorized_push():
    conn = _get_test_db()
    report = run_sar_investigation(conn, "CUST_105")
    assert "SCAM_AUTHORIZED_PUSH" in report.detected_typologies
    assert report.subject_role == SubjectRole.VICTIM


def test_merchant_acquiring_fraud():
    conn = _get_test_db()
    report = run_sar_investigation(conn, "CUST_106")
    assert "PAYMENT_ACQUIRING_FRAUD" in report.detected_typologies
    assert report.subject_role == SubjectRole.COMPLICIT_ACTOR


def test_csam_zero_tolerance_immediate_escalation():
    conn = _get_test_db()
    report = run_sar_investigation(conn, "CUST_107")
    assert "CSAM_ZERO_TOLERANCE_ESCALATION" in report.detected_typologies
    assert report.recommended_action == EscalationPriority.IMMEDIATE_ZERO_TOLERANCE_ESCALATION
    assert report.risk_score == 100


def test_benign_baseline_false_positive_control():
    conn = _get_test_db()
    report = run_sar_investigation(conn, "CUST_108")
    assert report.detected_typologies == []
    assert report.subject_role == SubjectRole.NEUTRAL_BENIGN
    assert report.recommended_action == EscalationPriority.CLOSE_FALSE_POSITIVE


def test_guardrail_rejects_hallucinated_amount_and_txn_id():
    conn = _get_test_db()
    customer, txns = fetch_customer_and_txns(conn, "CUST_101")
    metrics = analyze_transactions(customer, txns)
    matches, role, score, priority = evaluate_typologies(customer, txns, metrics)
    evidence = EvidenceBundle(
        case_id="CASE-CUST_101",
        customer=customer,
        metrics=metrics,
        triggered_typologies=matches,
        overall_subject_role=role,
        risk_score=score,
        recommended_action=priority,
    )

    fake_narrative_amount = "Subject wired $999,999.00 via [TXN_1011]."
    ok_amt, msg_amt = validate_sar_narrative(fake_narrative_amount, evidence)
    assert ok_amt is False
    assert "unverified dollar amounts" in msg_amt

    fake_narrative_txn = "Subject wired $4,800.00 via [TXN_FAKE_999]."
    ok_txn, msg_txn = validate_sar_narrative(fake_narrative_txn, evidence)
    assert ok_txn is False
    assert "unverified transaction IDs" in msg_txn


def test_api_endpoints_and_workbench():
    health = client.get("/health")
    assert health.status_code == 200

    api_res = client.get("/api/v1/investigate/CUST_103")
    assert api_res.status_code == 200
    assert "ELDER_FINANCIAL_EXPLOITATION" in api_res.json()["detected_typologies"]

    wb_res = client.get("/workbench?case=CUST_101")
    assert wb_res.status_code == 200
    assert "Marcus Vance" in wb_res.text

    not_found = client.get("/api/v1/investigate/UNKNOWN_999")
    assert not_found.status_code == 404

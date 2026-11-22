import sqlite3
from src.agents.txn_agent import analyze_transactions
from src.agents.typology_agent import evaluate_typologies
from src.agents.writer_agent import generate_sar_narrative
from src.database import fetch_customer_and_txns
from src.models import EvidenceBundle, SARInvestigationResponse
from src.validator import validate_sar_narrative


def run_sar_investigation(
    conn: sqlite3.Connection, customer_id: str
) -> SARInvestigationResponse:
    # 1. KYC & Ledger Retrieval
    customer, txns = fetch_customer_and_txns(conn, customer_id)

    # 2. Deterministic Forensic Math
    metrics = analyze_transactions(customer, txns)

    # 3. Regulatory Typology & Subject Role Classification
    matches, subject_role, risk_score, priority = evaluate_typologies(
        customer, txns, metrics
    )

    evidence = EvidenceBundle(
        case_id=f"CASE-{customer.customer_id}",
        customer=customer,
        metrics=metrics,
        triggered_typologies=matches,
        overall_subject_role=subject_role,
        risk_score=risk_score,
        recommended_action=priority,
    )

    # 4. 5Ws SAR Narrative Synthesis
    narrative = generate_sar_narrative(evidence, txns)

    # 5. Compliance Guardrail Verification
    is_verified, guardrail_notes = validate_sar_narrative(narrative, evidence)
    if not is_verified:
        raise RuntimeError(f"Compliance Guardrail Blocked Output: {guardrail_notes}")

    return SARInvestigationResponse(
        case_id=evidence.case_id,
        customer_name=customer.full_name,
        customer_age=customer.age,
        subject_role=subject_role,
        risk_score=risk_score,
        recommended_action=priority,
        detected_typologies=[m.typology_code for m in matches],
        sar_narrative=narrative,
        guardrail_verified=is_verified,
        guardrail_notes=guardrail_notes,
    )

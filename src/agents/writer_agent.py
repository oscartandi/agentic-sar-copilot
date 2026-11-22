from typing import List
from src.models import (
    EscalationPriority,
    EvidenceBundle,
    SubjectRole,
    TransactionRecord,
)


def generate_sar_narrative(
    evidence: EvidenceBundle, txns: List[TransactionRecord]
) -> str:
    c = evidence.customer
    m = evidence.metrics

    if evidence.recommended_action == EscalationPriority.CLOSE_FALSE_POSITIVE:
        return (
            f"INVESTIGATION DISPOSITION — CLOSE AS FALSE POSITIVE\n"
            f"Subject: {c.full_name} ({c.customer_id}), Age {c.age}, Occupation: {c.occupation}.\n"
            f"Summary: Review of {m.inbound_txn_count} inbound (${m.total_inbound_usd:,.2f}) and "
            f"{m.outbound_txn_count} outbound (${m.total_outbound_usd:,.2f}) transactions "
            f"({', '.join(f'[{tid}]' for tid in m.all_valid_txn_ids)}) aligns with declared monthly income "
            f"of ${c.declared_monthly_income:,.2f}. No suspicious financial crime typologies identified."
        )

    # Frame Subject Role accurately (Complicit Perpetrator vs. Protected Victim)
    if evidence.overall_subject_role == SubjectRole.VICTIM:
        role_statement = (
            f"Subject {c.full_name} ({c.customer_id}), Age {c.age}, appears to be a SUSPECTED VICTIM "
            f"targeted by external bad actors."
        )
    else:
        role_statement = (
            f"Subject {c.full_name} ({c.customer_id}), Age {c.age}, is identified as a SUSPECTED "
            f"PERPETRATOR / FACILITATOR exhibiting high-risk transactional behavior."
        )

    timestamps = sorted(t.timestamp for t in txns)
    window_start = timestamps[0][:10] if timestamps else "N/A"
    window_end = timestamps[-1][:10] if timestamps else "N/A"
    channels = ", ".join(sorted({t.channel for t in txns}))

    typology_bullets = "\n".join(
        f"  - [{t.typology_code}] {t.typology_name}: {t.evidence_summary} "
        f"(Citations: {', '.join(f'[{tid}]' for tid in t.cited_txn_ids)})"
        for t in evidence.triggered_typologies
    )

    txn_lines = "\n".join(
        f"  * [{t.txn_id}] {t.timestamp} | {t.direction} via {t.channel} | "
        f"${t.amount_usd:,.2f} | Counterparty: {t.counterparty_name} ({t.counterparty_id}) | "
        f"Device: {t.device_id} ({t.ip_country})"
        for t in txns
    )

    if evidence.recommended_action == EscalationPriority.IMMEDIATE_ZERO_TOLERANCE_ESCALATION:
        action_banner = (
            "RECOMMENDED ACTION: IMMEDIATE ZERO-TOLERANCE SAR FILING & LAW ENFORCEMENT / NCMEC ESCALATION."
        )
    elif evidence.recommended_action == EscalationPriority.HIGH_PRIORITY_SAR:
        action_banner = "RECOMMENDED ACTION: HIGH-PRIORITY SAR FILING & ACCOUNT RESTRICTION REVIEW."
    else:
        action_banner = "RECOMMENDED ACTION: STANDARD SAR FILING & ENHANCED DUE DILIGENCE (EDD)."

    return (
        f"SUSPICIOUS ACTIVITY REPORT (SAR) — AUTOMATED CO-PILOT DRAFT\n"
        f"====================================================================\n"
        f"1. WHO (SUBJECT & ROLE):\n"
        f"{role_statement} Onboarding profile lists occupation as '{c.occupation}' with declared "
        f"monthly income of ${c.declared_monthly_income:,.2f} (KYC Risk Rating: {c.kyc_risk_rating}).\n\n"
        f"2. WHAT (SUSPICIOUS ACTIVITY & TYPOLOGIES):\n"
        f"Forensic Risk Score: {evidence.risk_score}/100.\n"
        f"{typology_bullets}\n\n"
        f"3. WHEN (ACTIVITY WINDOW):\n"
        f"Suspicious activity occurred between {window_start} and {window_end} across "
        f"{len(txns)} transaction(s) totaling ${m.total_inbound_usd:,.2f} inbound and "
        f"${m.total_outbound_usd:,.2f} outbound.\n\n"
        f"4. WHERE (CHANNELS & INFRASTRUCTURE):\n"
        f"Activity spanned payment channel(s): {channels}. Registered device: {c.registered_device_id}.\n\n"
        f"5. WHY (SUPPORTING TRANSACTION LEDGER & CITATIONS):\n"
        f"{txn_lines}\n\n"
        f"{action_banner}"
    )

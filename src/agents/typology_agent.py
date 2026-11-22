from typing import List, Tuple
from src.models import (
    CustomerProfile,
    EscalationPriority,
    ForensicMetrics,
    SubjectRole,
    TransactionRecord,
    TypologyMatch,
)


def evaluate_typologies(
    customer: CustomerProfile,
    txns: List[TransactionRecord],
    metrics: ForensicMetrics,
) -> Tuple[List[TypologyMatch], SubjectRole, int, EscalationPriority]:
    matches: List[TypologyMatch] = []

    # 1. CSAM Zero-Tolerance Escalation (Highest Priority)
    csam_txns = [
        t.txn_id for t in txns if "CSAM_INDICATOR" in t.memo_or_tag.upper()
    ]
    if csam_txns:
        matches.append(
            TypologyMatch(
                category="CSAM / Severe Harm",
                typology_code="CSAM_ZERO_TOLERANCE_ESCALATION",
                typology_name="Severe Exploitation Indicator — Immediate Mandatory Escalation",
                severity_points=100,
                subject_role=SubjectRole.COMPLICIT_ACTOR,
                regulatory_reference="FinCEN Advisory / Mandatory Law Enforcement & NCMEC Referral",
                evidence_summary=f"Severe exploitation red-flag metadata matched on {', '.join(csam_txns)}. Zero auto-closure permitted.",
                cited_txn_ids=csam_txns,
            )
        )

    # 2. Account Takeover (ATO)
    if metrics.unrecognized_device_txns and metrics.security_events_detected:
        matches.append(
            TypologyMatch(
                category="Account Takeover (ATO)",
                typology_code="ACCOUNT_TAKEOVER_ATO",
                typology_name="Credential Compromise & Unauthorized Balance Drain",
                severity_points=75,
                subject_role=SubjectRole.VICTIM,
                regulatory_reference="FFIEC Authentication & Cyber-Event SAR Guidance",
                evidence_summary=(
                    f"Transactions {', '.join(metrics.unrecognized_device_txns)} originated from unrecognized device/IP "
                    f"immediately following security anomalies ({', '.join(metrics.security_events_detected)})."
                ),
                cited_txn_ids=metrics.unrecognized_device_txns,
            )
        )

    # 3. Elder Financial Exploitation (EFE - Age >= 60)
    efe_txns = [
        t.txn_id
        for t in txns
        if t.direction == "OUTBOUND"
        and t.is_new_counterparty
        and any(k in t.memo_or_tag.upper() for k in ["URGENT", "IRS", "TAX", "UNLOCK", "BOND"])
    ]
    if customer.age >= 60 and (efe_txns or metrics.new_payee_outbound_usd >= 10000.0):
        cited = efe_txns or [t.txn_id for t in txns if t.direction == "OUTBOUND"]
        matches.append(
            TypologyMatch(
                category="Elder Financial Exploitation (EFE)",
                typology_code="ELDER_FINANCIAL_EXPLOITATION",
                typology_name="Older Adult (Age 60+) Coerced / Imposter Outbound Transfers",
                severity_points=80,
                subject_role=SubjectRole.VICTIM,
                regulatory_reference="FinCEN Advisory FIN-2022-A002 (Elder Financial Exploitation)",
                evidence_summary=(
                    f"Customer age {customer.age} (meets >=60 EFE threshold) executed ${metrics.new_payee_outbound_usd:,.2f} "
                    f"in rapid outbound transfers to newly added counterparties with urgency/imposter indicators."
                ),
                cited_txn_ids=cited,
            )
        )

    # 4. Money Mule (Rapid Pass-Through Fan-In -> Funnel Out)
    if metrics.unique_inbound_senders >= 4 and metrics.pass_through_ratio >= 0.80:
        matches.append(
            TypologyMatch(
                category="Money Mule",
                typology_code="MONEY_MULE_PASS_THROUGH",
                typology_name="High-Velocity P2P Fan-In & Rapid Pass-Through Funneling",
                severity_points=75,
                subject_role=SubjectRole.COMPLICIT_ACTOR,
                regulatory_reference="FinCEN P2P & Money Mule Typology Guidance",
                evidence_summary=(
                    f"Received ${metrics.total_inbound_usd:,.2f} from {metrics.unique_inbound_senders} unrelated senders "
                    f"and funneled {int(metrics.pass_through_ratio * 100)}% outbound within 60 minutes."
                ),
                cited_txn_ids=metrics.all_valid_txn_ids,
            )
        )

    # 5. Money Laundering — Layering (Cross-Channel P2P -> Wire Rapid Movement)
    channels_used = {t.channel for t in txns}
    if len(channels_used) >= 2 and metrics.pass_through_ratio >= 0.80:
        matches.append(
            TypologyMatch(
                category="Money Laundering (Layering)",
                typology_code="ML_LAYERING",
                typology_name="Cross-Channel Rapid Layering & Settlement",
                severity_points=45,
                subject_role=SubjectRole.COMPLICIT_ACTOR,
                regulatory_reference="BSA / FATF Layering & Rapid Movement of Funds Red Flags",
                evidence_summary=(
                    f"Funds moved rapidly across distinct channels ({', '.join(sorted(channels_used))}) "
                    f"with minimal holding period ({metrics.rapid_outbound_count_under_60m} outbound transfers <60m)."
                ),
                cited_txn_ids=metrics.all_valid_txn_ids,
            )
        )

    # 6. Money Laundering — Suspicious Source of Funds (SOF)
    if metrics.income_deviation_multiple >= 3.0 and metrics.total_inbound_usd >= 10000.0:
        inbound_ids = [t.txn_id for t in txns if t.direction == "INBOUND"]
        matches.append(
            TypologyMatch(
                category="Money Laundering (Suspicious Source of Funds)",
                typology_code="ML_SUSPICIOUS_SOF",
                typology_name="Unexplained Inbound Volume Inconsistent with KYC Profile",
                severity_points=70,
                subject_role=SubjectRole.COMPLICIT_ACTOR,
                regulatory_reference="FinCEN CDD / Source of Funds & Structuring Red Flags",
                evidence_summary=(
                    f"Total inbound volume of ${metrics.total_inbound_usd:,.2f} is {metrics.income_deviation_multiple}x "
                    f"the customer's declared monthly income (${customer.declared_monthly_income:,.2f})."
                ),
                cited_txn_ids=inbound_ids,
            )
        )

    # 7. Scam Victim (Authorized Push Payment / Crypto Investment Scam)
    scam_txns = [
        t.txn_id
        for t in txns
        if any(k in t.memo_or_tag.upper() for k in ["CRYPTO POOL", "GUARANTEED YIELD", "TAX RELEASE"])
    ]
    if scam_txns and customer.age < 60:
        matches.append(
            TypologyMatch(
                category="Scam (Authorized Push Payment / Investment)",
                typology_code="SCAM_AUTHORIZED_PUSH",
                typology_name="Escalating Authorized Push Payments to High-Risk Investment Counterparty",
                severity_points=65,
                subject_role=SubjectRole.VICTIM,
                regulatory_reference="FinCEN Pig-Butchering / Investment Scam Advisory FIN-2023-A003",
                evidence_summary=(
                    f"Customer sent escalating payments (${metrics.new_payee_outbound_usd:,.2f}) to newly added "
                    f"crypto/investment counterparty with advance-fee withdrawal markers."
                ),
                cited_txn_ids=scam_txns,
            )
        )

    # 8. Payment / Merchant Acquiring Fraud
    fraud_txns = [
        t.txn_id
        for t in txns
        if any(k in t.memo_or_tag.upper() for k in ["CARD_TESTING", "CHARGEBACK"])
    ]
    if fraud_txns:
        matches.append(
            TypologyMatch(
                category="Fraud (Card / Acquiring)",
                typology_code="PAYMENT_ACQUIRING_FRAUD",
                typology_name="Merchant Card Testing & Rapid Settlement Bust-Out",
                severity_points=75,
                subject_role=SubjectRole.COMPLICIT_ACTOR,
                regulatory_reference="Card Network Acquiring Fraud & Merchant Bust-Out Guidelines",
                evidence_summary=(
                    f"Merchant exhibited card-testing/chargeback spikes (${metrics.total_inbound_usd:,.2f}) "
                    f"followed by immediate outbound settlement."
                ),
                cited_txn_ids=metrics.all_valid_txn_ids,
            )
        )

    # Determine Overall Risk Score, Subject Role & Escalation Priority
    if not matches:
        return [], SubjectRole.NEUTRAL_BENIGN, 10, EscalationPriority.CLOSE_FALSE_POSITIVE

    raw_score = sum(m.severity_points for m in matches)
    risk_score = min(100, raw_score)

    if any(m.typology_code == "CSAM_ZERO_TOLERANCE_ESCALATION" for m in matches):
        priority = EscalationPriority.IMMEDIATE_ZERO_TOLERANCE_ESCALATION
    elif risk_score >= 70:
        priority = EscalationPriority.HIGH_PRIORITY_SAR
    else:
        priority = EscalationPriority.STANDARD_SAR_REVIEW

    # If any complicit actor typology fired, classify subject as COMPLICIT_ACTOR; otherwise VICTIM
    if any(m.subject_role == SubjectRole.COMPLICIT_ACTOR for m in matches):
        overall_role = SubjectRole.COMPLICIT_ACTOR
    else:
        overall_role = SubjectRole.VICTIM

    return matches, overall_role, risk_score, priority

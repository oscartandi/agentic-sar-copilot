from enum import Enum
from typing import List, Optional
from pydantic import BaseModel, Field


class SubjectRole(str, Enum):
    COMPLICIT_ACTOR = "COMPLICIT_ACTOR"
    VICTIM = "VICTIM"
    NEUTRAL_BENIGN = "NEUTRAL_BENIGN"


class EscalationPriority(str, Enum):
    CLOSE_FALSE_POSITIVE = "CLOSE_FALSE_POSITIVE"
    STANDARD_SAR_REVIEW = "STANDARD_SAR_REVIEW"
    HIGH_PRIORITY_SAR = "HIGH_PRIORITY_SAR"
    IMMEDIATE_ZERO_TOLERANCE_ESCALATION = "IMMEDIATE_ZERO_TOLERANCE_ESCALATION"


class CustomerProfile(BaseModel):
    customer_id: str
    full_name: str
    age: int
    occupation: str
    declared_monthly_income: float
    account_opened_date: str
    kyc_risk_rating: str
    registered_device_id: str


class TransactionRecord(BaseModel):
    txn_id: str
    customer_id: str
    direction: str  # INBOUND or OUTBOUND
    channel: str    # P2P, ACH, WIRE, CARD_ACQUIRING
    counterparty_id: str
    counterparty_name: str
    is_new_counterparty: bool
    amount_usd: float
    timestamp: str
    device_id: str
    ip_country: str
    memo_or_tag: str
    security_event: Optional[str] = None  # e.g., PASSWORD_RESET_NEW_DEVICE


class TypologyMatch(BaseModel):
    category: str
    typology_code: str
    typology_name: str
    severity_points: int
    subject_role: SubjectRole
    regulatory_reference: str
    evidence_summary: str
    cited_txn_ids: List[str]


class ForensicMetrics(BaseModel):
    total_inbound_usd: float
    total_outbound_usd: float
    inbound_txn_count: int
    outbound_txn_count: int
    unique_inbound_senders: int
    income_deviation_multiple: float
    pass_through_ratio: float
    rapid_outbound_count_under_60m: int
    unrecognized_device_txns: List[str]
    security_events_detected: List[str]
    new_payee_outbound_usd: float
    high_risk_tags_detected: List[str]
    all_valid_txn_ids: List[str]
    all_valid_amounts: List[float]


class EvidenceBundle(BaseModel):
    case_id: str
    customer: CustomerProfile
    metrics: ForensicMetrics
    triggered_typologies: List[TypologyMatch]
    overall_subject_role: SubjectRole
    risk_score: int = Field(ge=0, le=100)
    recommended_action: EscalationPriority


class SARInvestigationResponse(BaseModel):
    case_id: str
    customer_name: str
    customer_age: int
    subject_role: SubjectRole
    risk_score: int
    recommended_action: EscalationPriority
    detected_typologies: List[str]
    sar_narrative: str
    guardrail_verified: bool
    guardrail_notes: str

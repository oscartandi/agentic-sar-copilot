from datetime import datetime
from typing import List
from src.models import CustomerProfile, ForensicMetrics, TransactionRecord


def analyze_transactions(
    customer: CustomerProfile, txns: List[TransactionRecord]
) -> ForensicMetrics:
    inbound_txns = [t for t in txns if t.direction == "INBOUND"]
    outbound_txns = [t for t in txns if t.direction == "OUTBOUND"]

    total_inbound = round(sum(t.amount_usd for t in inbound_txns), 2)
    total_outbound = round(sum(t.amount_usd for t in outbound_txns), 2)

    unique_senders = len({t.counterparty_id for t in inbound_txns})
    income_multiple = (
        round(total_inbound / customer.declared_monthly_income, 2)
        if customer.declared_monthly_income > 0
        else 0.0
    )

    # Calculate rapid pass-through outbound volume within 60 minutes of an inbound credit
    rapid_outbound_volume = 0.0
    rapid_outbound_count = 0
    inbound_times = [datetime.fromisoformat(t.timestamp) for t in inbound_txns]

    for out_t in outbound_txns:
        out_time = datetime.fromisoformat(out_t.timestamp)
        if any(
            0 <= (out_time - in_time).total_seconds() <= 3600
            for in_time in inbound_times
        ):
            rapid_outbound_volume += out_t.amount_usd
            rapid_outbound_count += 1

    pass_through_ratio = (
        round(rapid_outbound_volume / total_inbound, 2) if total_inbound > 0 else 0.0
    )

    unrecognized_devices = [
        t.txn_id for t in txns if t.device_id != customer.registered_device_id
    ]
    security_events = [
        f"{t.txn_id}:{t.security_event}" for t in txns if t.security_event
    ]
    new_payee_outbound = round(
        sum(t.amount_usd for t in outbound_txns if t.is_new_counterparty), 2
    )
    high_risk_tags = [
        f"{t.txn_id}:{t.memo_or_tag}"
        for t in txns
        if any(
            kw in t.memo_or_tag.upper()
            for kw in [
                "CSAM_INDICATOR",
                "URGENT",
                "IRS",
                "TAX",
                "UNLOCK",
                "CRYPTO POOL",
                "GUARANTEED YIELD",
                "CARD_TESTING",
                "CHARGEBACK",
            ]
        )
    ]

    return ForensicMetrics(
        total_inbound_usd=total_inbound,
        total_outbound_usd=total_outbound,
        inbound_txn_count=len(inbound_txns),
        outbound_txn_count=len(outbound_txns),
        unique_inbound_senders=unique_senders,
        income_deviation_multiple=income_multiple,
        pass_through_ratio=pass_through_ratio,
        rapid_outbound_count_under_60m=rapid_outbound_count,
        unrecognized_device_txns=unrecognized_devices,
        security_events_detected=security_events,
        new_payee_outbound_usd=new_payee_outbound,
        high_risk_tags_detected=high_risk_tags,
        all_valid_txn_ids=[t.txn_id for t in txns],
        all_valid_amounts=[round(t.amount_usd, 2) for t in txns]
        + [total_inbound, total_outbound, new_payee_outbound, customer.declared_monthly_income],
    )

import re
from typing import Set, Tuple
from src.models import EvidenceBundle


def validate_sar_narrative(
    narrative: str, evidence: EvidenceBundle
) -> Tuple[bool, str]:
    """
    Deterministic compliance guardrail:
    1. Extracts all dollar figures ($X,XXX.XX) and transaction citations ([TXN_XXXX]) from the narrative.
    2. Verifies every cited transaction ID exists in the SQL evidence bundle.
    3. Verifies every dollar amount in the narrative matches an actual ledger or aggregated metric figure.
    """
    cited_txns: Set[str] = set(re.findall(r"\[(TXN_[A-Z0-9_]+)\]", narrative))
    valid_txns: Set[str] = set(evidence.metrics.all_valid_txn_ids)

    unknown_txns = cited_txns - valid_txns
    if unknown_txns:
        return (
            False,
            f"GUARDRAIL FAILED: Narrative cited unverified transaction IDs: {sorted(unknown_txns)}",
        )

    raw_amounts = re.findall(r"\$([0-9,]+(?:\.[0-9]{2})?)", narrative)
    extracted_amounts: Set[float] = {
        round(float(val.replace(",", "")), 2) for val in raw_amounts
    }
    allowed_amounts: Set[float] = {
        round(val, 2) for val in evidence.metrics.all_valid_amounts
    }

    unverified_amounts = extracted_amounts - allowed_amounts
    if unverified_amounts:
        return (
            False,
            f"GUARDRAIL FAILED: Narrative contains unverified dollar amounts: {sorted(unverified_amounts)}",
        )

    if not cited_txns and valid_txns:
        return (
            False,
            "GUARDRAIL FAILED: Narrative failed to cite any supporting transaction IDs.",
        )

    return (
        True,
        f"VERIFIED: {len(cited_txns)} transaction citation(s) and {len(extracted_amounts)} dollar figure(s) 100% grounded in SQL ledger.",
    )

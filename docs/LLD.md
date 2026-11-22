# Low-Level Design (LLD): Agentic SAR Investigation & Narrative Co-Pilot

## 1. Repository & Module Structure

```text
agentic-sar-copilot/
├── docs/
│   ├── HLD.md                    # High-Level System Architecture & Governance
│   └── LLD.md                    # Low-Level Database Schema, State Machine & Guardrails
├── src/
│   ├── __init__.py
│   ├── models.py                 # Pydantic schemas for Agent I/O & API contracts
│   ├── database.py               # SQLite connection & synthetic FinCrime case seeder
│   ├── orchestrator.py           # Async investigation pipeline & retry controller
│   ├── agents/
│   │   ├── kyc_agent.py          # Customer profile & expected-vs-actual income check
│   │   ├── txn_agent.py          # Deterministic SQL/Python P2P & structuring metrics
│   │   ├── typology_agent.py     # Regulatory red-flag & typology knowledge matcher
│   │   └── writer_agent.py       # 5Ws SAR narrative generator (Template + LLM mode)
│   ├── validator.py              # Regex/AST hallucination & citation verification engine
│   └── api.py                    # FastAPI REST endpoints & HTML Investigator Workbench
├── tests/
│   ├── test_txn_agent.py         # Unit tests for structuring & pass-through math
│   ├── test_validator.py         # Unit tests catching fabricated dollar amounts/IDs
│   └── test_api.py               # End-to-end investigation & SAR workflow tests
├── requirements.txt
└── README.md
```

---

## 2. Relational Database Schema (`src/database.py`)

### Table: `customers`

| Column | Type | Constraints | Description |
| :--- | :--- | :--- | :--- |
| `customer_id` | `TEXT` | `PRIMARY KEY` | Unique customer identifier (`CUST_101` – `CUST_108`) |
| `full_name` | `TEXT` | `NOT NULL` | Subject legal or business name |
| `age` | `INTEGER` | `NOT NULL` | Customer age in years (used for `age >= 60` EFE check) |
| `occupation` | `TEXT` | `NOT NULL` | Stated profession at onboarding |
| `declared_monthly_income` | `REAL` | `NOT NULL` | Stated monthly income in USD |
| `account_opened_date` | `TEXT` | `NOT NULL` | ISO-8601 onboarding date |
| `kyc_risk_rating` | `TEXT` | `NOT NULL` | `LOW`, `MEDIUM`, or `HIGH` |
| `registered_device_id` | `TEXT` | `NOT NULL` | Known primary device fingerprint |

### Table: `transactions`

| Column | Type | Constraints | Description |
| :--- | :--- | :--- | :--- |
| `txn_id` | `TEXT` | `PRIMARY KEY` | Unique transaction reference (`TXN_1011`) |
| `customer_id` | `TEXT` | `FOREIGN KEY` | References `customers(customer_id)` |
| `direction` | `TEXT` | `NOT NULL` | `INBOUND` or `OUTBOUND` |
| `channel` | `TEXT` | `NOT NULL` | `P2P`, `ACH`, `WIRE`, or `CARD_ACQUIRING` |
| `counterparty_id` | `TEXT` | `NOT NULL` | External sender/recipient identifier |
| `counterparty_name` | `TEXT` | `NOT NULL` | External counterparty display name |
| `is_new_counterparty` | `INTEGER` | `NOT NULL` | `1` if first-time counterparty, `0` otherwise |
| `amount_usd` | `REAL` | `NOT NULL` | Transaction value in USD |
| `timestamp` | `TEXT` | `NOT NULL` | ISO-8601 UTC timestamp |
| `device_id` | `TEXT` | `NOT NULL` | Session device fingerprint |
| `ip_country` | `TEXT` | `NOT NULL` | ISO-3166 country code |
| `memo_or_tag` | `TEXT` | `NOT NULL` | Payment memo or risk telemetry tag |
| `security_event` | `TEXT` | `NULLABLE` | Auth anomaly (`PASSWORD_RESET_NEW_DEVICE`, etc.) |

---

## 3. Supported FinCrime Typology Rules & Role Classification (`src/agents/typology_agent.py`)

Every investigation classifies both the **Typology** and the **Subject Role** (`COMPLICIT_ACTOR` vs. `VICTIM` vs. `NEUTRAL_BENIGN`):

| Typology Code | Category | Trigger Condition | Subject Role |
| :--- | :--- | :--- | :--- |
| `CSAM_ZERO_TOLERANCE_ESCALATION` | CSAM / Severe Harm | High-risk exploitation metadata match (`IMMEDIATE_ZERO_TOLERANCE_ESCALATION`) | `COMPLICIT_ACTOR` |
| `ACCOUNT_TAKEOVER_ATO` | Account Takeover | Unrecognized `device_id` + auth reset event followed by rapid outbound drain | `VICTIM` |
| `ELDER_FINANCIAL_EXPLOITATION` | Elder Financial Exploitation | `age >= 60` + urgent/imposter outbound transfers to new counterparties (`>= $10,000` or urgency keywords) | `VICTIM` |
| `MONEY_MULE_PASS_THROUGH` | Money Mule | `>= 4` unique inbound P2P senders + `>= 80%` outbound funneling within 60 mins | `COMPLICIT_ACTOR` |
| `ML_LAYERING` | Money Laundering (Layering) | Multi-channel movement (`P2P -> WIRE/ACH`) with `>= 80%` pass-through `< 60 mins` | `COMPLICIT_ACTOR` |
| `ML_SUSPICIOUS_SOF` | Money Laundering (SOF) | 30-day inbound volume `>= 3.0x` `declared_monthly_income` (`>= $10,000`) | `COMPLICIT_ACTOR` |
| `SCAM_AUTHORIZED_PUSH` | Scam (APP / Investment) | Escalating outbound push payments to new crypto/investment counterparties (`age < 60`) | `VICTIM` |
| `PAYMENT_ACQUIRING_FRAUD` | Fraud (Card / Acquiring) | Card-testing / chargeback spikes followed by immediate outbound payout | `COMPLICIT_ACTOR` |


---

## 4. Hallucination Guardrail Algorithm (`src/validator.py`)

To guarantee regulatory audit readiness, `validate_sar_draft(narrative: str, evidence: EvidenceBundle)` executes a strict deterministic check:
1. **Currency Extraction:** Uses regex `\$[0-9,]+(?:\.[0-9]{2})?` to extract every dollar figure mentioned in the SAR narrative.
2. **Citation Extraction:** Uses regex `\[TXN_[A-Z0-9_]+\]` to extract every cited transaction ID.
3. **Set Membership Verification:**
   * Verifies `extracted_amounts.issubset(evidence.allowed_amounts)`
   * Verifies `extracted_txn_ids.issubset(evidence.valid_txn_ids)`
4. **Retry Loop:** If any unverified figure or ID is detected, the orchestrator rejects the draft, appends an explicit error correction prompt, and retries up to `max_retries = 2`.

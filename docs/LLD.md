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
| `customer_id` | `TEXT` | `PRIMARY KEY` | Unique customer identifier (e.g., `CUST_101`) |
| `full_name` | `TEXT` | `NOT NULL` | Subject legal name |
| `occupation` | `TEXT` | `NOT NULL` | Declared profession at onboarding |
| `declared_monthly_income` | `REAL` | `NOT NULL` | Stated monthly income in USD |
| `account_opened_date` | `TEXT` | `NOT NULL` | ISO-8601 onboarding date |
| `kyc_risk_rating` | `TEXT` | `NOT NULL` | `LOW`, `MEDIUM`, or `HIGH` |

### Table: `transactions`

| Column | Type | Constraints | Description |
| :--- | :--- | :--- | :--- |
| `txn_id` | `TEXT` | `PRIMARY KEY` | Unique transaction reference (`TXN_9001`) |
| `customer_id` | `TEXT` | `FOREIGN KEY` | References `customers(customer_id)` |
| `direction` | `TEXT` | `NOT NULL` | `INBOUND` or `OUTBOUND` |
| `channel` | `TEXT` | `NOT NULL` | `P2P`, `ACH`, `WIRE`, or `CARD_ACQUIRING` |
| `counterparty_id` | `TEXT` | `NOT NULL` | External sender/recipient identifier |
| `amount_usd` | `REAL` | `NOT NULL` | Transaction value in USD |
| `timestamp` | `TEXT` | `NOT NULL` | ISO-8601 UTC timestamp |

---

## 3. Deterministic Forensic Formulas (`src/agents/txn_agent.py`)

1. **Income-to-Volume Deviation Ratio:**
   $$\text{Income Multiple} = \frac{\text{Total 30-Day Inbound Volume}}{\text{Declared Monthly Income}}$$
   *Flagged if $\text{Income Multiple} \ge 3.0\times$.*

2. **Rapid Pass-Through (Mule) Ratio:**
   $$\text{Pass-Through Ratio} = \frac{\text{Outbound Volume within 60 mins of Inbound Credit}}{\text{Total Inbound Volume}}$$
   *Flagged as `RAPID_PASS_THROUGH_MULE` if $\text{Pass-Through Ratio} \ge 0.80$.*

3. **Sub-Threshold Structuring Indicator:**
   *Count of transactions where $\$8,500 \le \text{amount\_usd} < \$10,000$ within a rolling 7-day window. Flagged as `STRUCTURING_SMURFING` if count $\ge 3$.*

---

## 4. Hallucination Guardrail Algorithm (`src/validator.py`)

To guarantee regulatory audit readiness, `validate_sar_draft(narrative: str, evidence: EvidenceBundle)` executes a strict deterministic check:
1. **Currency Extraction:** Uses regex `\$[0-9,]+(?:\.[0-9]{2})?` to extract every dollar figure mentioned in the SAR narrative.
2. **Citation Extraction:** Uses regex `\[TXN_[A-Z0-9_]+\]` to extract every cited transaction ID.
3. **Set Membership Verification:**
   * Verifies `extracted_amounts.issubset(evidence.allowed_amounts)`
   * Verifies `extracted_txn_ids.issubset(evidence.valid_txn_ids)`
4. **Retry Loop:** If any unverified figure or ID is detected, the orchestrator rejects the draft, appends an explicit error correction prompt, and retries up to `max_retries = 2`.

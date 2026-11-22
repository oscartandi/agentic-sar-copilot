import sqlite3
from typing import Dict, List, Optional, Tuple
from src.models import CustomerProfile, TransactionRecord

DB_PATH = ":memory:"


def get_connection(db_path: str = DB_PATH) -> sqlite3.Connection:
    conn = sqlite3.connect(db_path, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn


def init_and_seed_db(conn: sqlite3.Connection) -> None:
    cursor = conn.cursor()

    cursor.executescript("""
        DROP TABLE IF EXISTS transactions;
        DROP TABLE IF EXISTS customers;

        CREATE TABLE customers (
            customer_id TEXT PRIMARY KEY,
            full_name TEXT NOT NULL,
            age INTEGER NOT NULL,
            occupation TEXT NOT NULL,
            declared_monthly_income REAL NOT NULL,
            account_opened_date TEXT NOT NULL,
            kyc_risk_rating TEXT NOT NULL,
            registered_device_id TEXT NOT NULL
        );

        CREATE TABLE transactions (
            txn_id TEXT PRIMARY KEY,
            customer_id TEXT NOT NULL,
            direction TEXT NOT NULL,
            channel TEXT NOT NULL,
            counterparty_id TEXT NOT NULL,
            counterparty_name TEXT NOT NULL,
            is_new_counterparty INTEGER NOT NULL,
            amount_usd REAL NOT NULL,
            timestamp TEXT NOT NULL,
            device_id TEXT NOT NULL,
            ip_country TEXT NOT NULL,
            memo_or_tag TEXT NOT NULL,
            security_event TEXT,
            FOREIGN KEY (customer_id) REFERENCES customers(customer_id)
        );
    """)

    customers = [
        # 1. Money Mule + ML Layering
        ("CUST_101", "Marcus Vance", 29, "Freelance Graphic Designer", 3500.0, "2026-06-12", "MEDIUM", "DEV_101_REG"),
        # 2. ML Suspicious Source of Funds (SOF)
        ("CUST_102", "Elena Rostova", 34, "Retail Store Associate", 2800.0, "2025-11-03", "LOW", "DEV_102_REG"),
        # 3. Elder Financial Exploitation (EFE - Age 64, >= 60 threshold)
        ("CUST_103", "Arthur Pendelton", 64, "Retired School Principal", 4200.0, "2019-04-18", "LOW", "DEV_103_REG"),
        # 4. Account Takeover (ATO)
        ("CUST_104", "Priya Nair", 31, "Product Analyst", 6500.0, "2022-08-20", "LOW", "DEV_104_REG"),
        # 5. Scam Victim (Authorized Push Payment / Crypto Investment Scam)
        ("CUST_105", "Liam O'Connor", 41, "Civil Engineer", 7000.0, "2021-02-14", "LOW", "DEV_105_REG"),
        # 6. Payment / Merchant Acquiring Fraud
        ("CUST_106", "Apex Digital Goods LLC", 38, "E-Commerce Merchant", 12000.0, "2026-09-01", "HIGH", "DEV_106_REG"),
        # 7. CSAM Priority Escalation Protocol (Synthetic Metadata Flag)
        ("CUST_107", "Victor Krol", 45, "IT Contractor", 5500.0, "2024-01-10", "HIGH", "DEV_107_REG"),
        # 8. Benign Baseline Customer (False-Positive Control)
        ("CUST_108", "Sarah Jenkins", 36, "Marketing Manager", 6000.0, "2020-05-11", "LOW", "DEV_108_REG"),
    ]

    cursor.executemany(
        "INSERT INTO customers VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
        customers,
    )

    transactions = [
        # --- CUST_101: Money Mule + ML Layering (Fan-in P2P -> Outbound Wire < 45 mins) ---
        ("TXN_1011", "CUST_101", "INBOUND", "P2P", "EXT_01", "Sender Alpha", 1, 4800.0, "2026-11-18T10:00:00", "DEV_101_REG", "US", "P2P transfer", None),
        ("TXN_1012", "CUST_101", "INBOUND", "P2P", "EXT_02", "Sender Beta", 1, 5200.0, "2026-11-18T10:08:00", "DEV_101_REG", "US", "P2P transfer", None),
        ("TXN_1013", "CUST_101", "INBOUND", "P2P", "EXT_03", "Sender Gamma", 1, 4500.0, "2026-11-18T10:15:00", "DEV_101_REG", "US", "P2P transfer", None),
        ("TXN_1014", "CUST_101", "INBOUND", "P2P", "EXT_04", "Sender Delta", 1, 5000.0, "2026-11-18T10:21:00", "DEV_101_REG", "US", "P2P transfer", None),
        ("TXN_1015", "CUST_101", "INBOUND", "P2P", "EXT_05", "Sender Epsilon", 1, 4500.0, "2026-11-18T10:26:00", "DEV_101_REG", "US", "P2P transfer", None),
        ("TXN_1016", "CUST_101", "OUTBOUND", "WIRE", "EXT_SHELL_99", "Offshore Clearing Ltd", 1, 22800.0, "2026-11-18T10:40:00", "DEV_101_REG", "US", "Consulting settlement", None),

        # --- CUST_102: ML Suspicious Source of Funds (13.5x declared income) ---
        ("TXN_2021", "CUST_102", "INBOUND", "ACH", "EXT_201", "Unknown Holding Corp", 1, 9500.0, "2026-11-10T09:15:00", "DEV_102_REG", "US", "Invoice 881", None),
        ("TXN_2022", "CUST_102", "INBOUND", "ACH", "EXT_202", "Vanguardia Trade SA", 1, 9600.0, "2026-11-12T14:20:00", "DEV_102_REG", "US", "Invoice 882", None),
        ("TXN_2023", "CUST_102", "INBOUND", "WIRE", "EXT_203", "Baltic Commodities", 1, 9400.0, "2026-11-14T11:05:00", "DEV_102_REG", "US", "Invoice 883", None),
        ("TXN_2024", "CUST_102", "INBOUND", "WIRE", "EXT_204", "Meridian Global", 1, 9500.0, "2026-11-16T16:45:00", "DEV_102_REG", "US", "Invoice 884", None),

        # --- CUST_103: Elder Financial Exploitation (Age 64 >= 60, urgent new beneficiary wires) ---
        ("TXN_3031", "CUST_103", "OUTBOUND", "WIRE", "EXT_301", "Global Tech Support Relief", 1, 6500.0, "2026-11-15T11:10:00", "DEV_103_REG", "US", "URGENT TAX IRS PENALTY FEE", None),
        ("TXN_3032", "CUST_103", "OUTBOUND", "WIRE", "EXT_301", "Global Tech Support Relief", 1, 8000.0, "2026-11-16T09:30:00", "DEV_103_REG", "US", "URGENT ACCOUNT UNLOCK FEE", None),
        ("TXN_3033", "CUST_103", "OUTBOUND", "P2P", "EXT_302", "Agent Miller Recovery", 1, 4500.0, "2026-11-17T13:15:00", "DEV_103_REG", "US", "SECURED BOND RELEASE", None),

        # --- CUST_104: Account Takeover (ATO - New device/foreign IP + password reset + drain) ---
        ("TXN_4041", "CUST_104", "OUTBOUND", "P2P", "EXT_401", "FastCash Mule 01", 1, 7500.0, "2026-11-19T03:14:00", "DEV_UNKNOWN_99", "RO", "Transfer", "PASSWORD_RESET_NEW_DEVICE"),
        ("TXN_4042", "CUST_104", "OUTBOUND", "P2P", "EXT_402", "FastCash Mule 02", 1, 6800.0, "2026-11-19T03:17:00", "DEV_UNKNOWN_99", "RO", "Transfer", "EMAIL_CHANGED_NEW_IP"),

        # --- CUST_105: Authorized Push Payment / Investment Scam Victim ---
        ("TXN_5051", "CUST_105", "OUTBOUND", "P2P", "EXT_501", "Apex Quant Crypto VIP", 1, 3000.0, "2026-11-11T15:00:00", "DEV_105_REG", "US", "VIP CRYPTO POOL DEPOSIT", None),
        ("TXN_5052", "CUST_105", "OUTBOUND", "WIRE", "EXT_501", "Apex Quant Crypto VIP", 1, 12000.0, "2026-11-14T16:20:00", "DEV_105_REG", "US", "GUARANTEED YIELD TIER 2", None),
        ("TXN_5053", "CUST_105", "OUTBOUND", "WIRE", "EXT_501", "Apex Quant Crypto VIP", 1, 15000.0, "2026-11-18T17:05:00", "DEV_105_REG", "US", "WITHDRAWAL TAX RELEASE", None),

        # --- CUST_106: Merchant / Acquiring Card Fraud ---
        ("TXN_6061", "CUST_106", "INBOUND", "CARD_ACQUIRING", "CARD_BATCH_01", "Stolen BIN Cluster A", 1, 18500.0, "2026-11-17T02:10:00", "DEV_106_REG", "US", "CARD_TESTING_CHARGEBACK_SPIKE", None),
        ("TXN_6062", "CUST_106", "OUTBOUND", "ACH", "EXT_601", "Unverified Payout Acct", 1, 18000.0, "2026-11-17T02:45:00", "DEV_106_REG", "US", "Rapid merchant settlement", None),

        # --- CUST_107: CSAM Zero-Tolerance Priority Escalation (Metadata Indicator Only) ---
        ("TXN_7071", "CUST_107", "OUTBOUND", "P2P", "EXT_701", "Flagged Media Broker", 1, 150.0, "2026-11-19T22:10:00", "DEV_107_REG", "US", "CSAM_INDICATOR_NCMEC_HASH_MATCH", None),
        ("TXN_7072", "CUST_107", "OUTBOUND", "P2P", "EXT_701", "Flagged Media Broker", 1, 200.0, "2026-11-19T22:25:00", "DEV_107_REG", "US", "CSAM_INDICATOR_ILLICIT_STREAM", None),

        # --- CUST_108: Benign Baseline Customer (Normal Salary + Bills) ---
        ("TXN_8081", "CUST_108", "INBOUND", "ACH", "EMP_ACME", "Acme Corp Payroll", 0, 3000.0, "2026-11-01T08:00:00", "DEV_108_REG", "US", "Biweekly Payroll", None),
        ("TXN_8082", "CUST_108", "INBOUND", "ACH", "EMP_ACME", "Acme Corp Payroll", 0, 3000.0, "2026-11-15T08:00:00", "DEV_108_REG", "US", "Biweekly Payroll", None),
        ("TXN_8083", "CUST_108", "OUTBOUND", "ACH", "UTIL_01", "City Power & Light", 0, 145.0, "2026-11-05T12:00:00", "DEV_108_REG", "US", "Electric Bill", None),
    ]

    cursor.executemany(
        "INSERT INTO transactions VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
        transactions,
    )
    conn.commit()


def fetch_customer_and_txns(
    conn: sqlite3.Connection, customer_id: str
) -> Tuple[CustomerProfile, List[TransactionRecord]]:
    cursor = conn.cursor()
    row = cursor.execute(
        "SELECT * FROM customers WHERE customer_id = ?", (customer_id,)
    ).fetchone()
    if not row:
        raise ValueError(f"Customer '{customer_id}' not found in ledger.")

    customer = CustomerProfile(**dict(row))
    txn_rows = cursor.execute(
        "SELECT * FROM transactions WHERE customer_id = ? ORDER BY timestamp ASC",
        (customer_id,),
    ).fetchall()

    txns = []
    for r in txn_rows:
        data = dict(r)
        data["is_new_counterparty"] = bool(data["is_new_counterparty"])
        txns.append(TransactionRecord(**data))

    return customer, txns

from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse
from src.database import get_connection, init_and_seed_db
from src.models import SARInvestigationResponse
from src.orchestrator import run_sar_investigation

app = FastAPI(
    title="Agentic SAR Investigation & Narrative Co-Pilot",
    description="Multi-agent FinCrime investigation platform with deterministic SQL forensics and hallucination-guarded FinCEN SAR synthesis.",
    version="1.0.0",
)

_conn = get_connection()
init_and_seed_db(_conn)


@app.get("/", include_in_schema=False)
def root():
    return RedirectResponse(url="/workbench")


@app.get("/health")
def health():
    return {"status": "healthy", "database": "seeded_synthetic_ledger"}


@app.get("/api/v1/investigate/{customer_id}", response_model=SARInvestigationResponse)
def investigate_customer(customer_id: str):
    try:
        return run_sar_investigation(_conn, customer_id.upper())
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc))


@app.get("/workbench", response_class=HTMLResponse)
def investigator_workbench(case: str = "CUST_101"):
    cases = [
        ("CUST_101", "Marcus Vance — Money Mule & ML Layering"),
        ("CUST_102", "Elena Rostova — ML Suspicious Source of Funds"),
        ("CUST_103", "Arthur Pendelton (Age 64) — Elder Financial Exploitation"),
        ("CUST_104", "Priya Nair — Account Takeover (ATO)"),
        ("CUST_105", "Liam O'Connor — Scam Victim (Authorized Push)"),
        ("CUST_106", "Apex Digital Goods — Card / Acquiring Fraud"),
        ("CUST_107", "Victor Krol — CSAM Priority Escalation Protocol"),
        ("CUST_108", "Sarah Jenkins — Benign Baseline (False-Positive Control)"),
    ]
    try:
        report = run_sar_investigation(_conn, case.upper())
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc))

    options_html = "".join(
        f'<option value="{cid}" {"selected" if cid == case.upper() else ""}>{cid}: {label}</option>'
        for cid, label in cases
    )
    badges = "".join(
        f'<span style="background:#1e293b;color:#38bdf8;padding:4px 10px;border-radius:6px;margin-right:6px;font-size:12px;">{t}</span>'
        for t in (report.detected_typologies or ["NO_TYPOLOGY_DETECTED"])
    )

    return f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Agentic SAR Co-Pilot Workbench</title>
        <style>
            body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; background:#0f172a; color:#e2e8f0; margin:0; padding:24px; }}
            .container {{ max-width: 960px; margin: auto; }}
            .card {{ background:#1e293b; border:1px solid #334155; border-radius:10px; padding:20px; margin-bottom:20px; }}
            select, button {{ padding:10px 14px; border-radius:6px; border:1px solid #475569; background:#0f172a; color:#f8fafc; font-size:14px; }}
            button {{ background:#0284c7; border:none; cursor:pointer; font-weight:600; }}
            pre {{ background:#020617; padding:16px; border-radius:8px; white-space:pre-wrap; line-height:1.5; border:1px solid #334155; font-size:13px; color:#f1f5f9; }}
            .pill {{ display:inline-block; padding:4px 10px; border-radius:999px; font-weight:700; font-size:12px; background:#065f46; color:#6ee7b7; }}
        </style>
    </head>
    <body>
        <div class="container">
            <h2>🛡️ Agentic SAR Investigation & Narrative Co-Pilot</h2>
            <form method="get" action="/workbench" style="margin-bottom:20px;">
                <select name="case">{options_html}</select>
                <button type="submit">Run Multi-Agent Investigation</button>
            </form>
            <div class="card">
                <p><strong>Case ID:</strong> {report.case_id} | <strong>Subject:</strong> {report.customer_name} (Age {report.customer_age}) | <strong>Role:</strong> {report.subject_role.value}</p>
                <p><strong>Forensic Risk Score:</strong> {report.risk_score}/100 | <strong>Disposition:</strong> {report.recommended_action.value}</p>
                <p><strong>Triggered Typologies:</strong> {badges}</p>
                <p><span class="pill">✓ {report.guardrail_notes}</span></p>
            </div>
            <div class="card">
                <h3>Generated 5Ws FinCEN-Ready SAR Narrative</h3>
                <pre>{report.sar_narrative}</pre>
            </div>
        </div>
    </body>
    </html>
    """

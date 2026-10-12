"""
Tester feedback store for the psychologist evaluation round.

Responses are appended to feedback/responses.csv (created on first use) with a
timestamp and an anonymous tester id. No health data is stored - only the tester's
answers about the application.
"""
import csv
import json
import os
from datetime import datetime
from pathlib import Path

from src import config as C

try:
    import requests
except ImportError:  # requests ships with streamlit; guard anyway
    requests = None

FEEDBACK_DIR = C.ROOT / "feedback"
FEEDBACK_FILE = FEEDBACK_DIR / "responses.csv"
ADMIN_CODE = os.environ.get("MANAS_ADMIN_CODE", "manas2026")


def _secret(name, default=""):
    """Read from Streamlit secrets (cloud) or environment variables (local)."""
    try:
        import streamlit as st
        v = st.secrets.get(name)  # type: ignore[attr-defined]
        if v:
            return str(v)
    except Exception:
        pass
    return os.environ.get(name, default)


def admin_code():
    return _secret("MANAS_ADMIN_CODE", ADMIN_CODE)


def webhook():
    """Google Sheets sync endpoint (Apps Script web app URL) and shared key, if configured."""
    return _secret("FEEDBACK_WEBHOOK_URL"), _secret("FEEDBACK_WEBHOOK_KEY")


def sync_enabled():
    return bool(webhook()[0])

# Likert statements (1 = strongly disagree, 5 = strongly agree)
STATEMENTS = [
    ("clarity", "The mind-weather status (Clear / Clouds gathering / Storm likely) was immediately understandable."),
    ("explanations", "The explanations of WHY risk went up made clinical sense to me."),
    ("early_warning_value", "A 7-day early warning like this would be useful in my practice."),
    ("trust", "I would trust this tool as a prompt for a check-in (not as a diagnosis)."),
    ("workload", "About one false-alarm day per month per client is an acceptable workload."),
    ("whatif", "The what-if simulator would help me discuss lifestyle changes with a client."),
    ("caseload", "The counsellor caseload view would help me prioritise who to contact."),
    ("safety", "The safety framing (no suicide-risk prediction, helpline, human in the loop) is appropriate."),
    ("ease", "The application was easy to use without training."),
    ("recommend", "I would recommend piloting this in a campus or workplace wellness setting."),
]

OPEN_QUESTIONS = [
    ("trust_more", "What would make you trust this tool more?"),
    ("missing", "What is missing that you would need before using it with real clients?"),
    ("concerns", "Any ethical, clinical or practical concerns?"),
    ("other", "Anything else?"),
]

FIELDS = ["timestamp", "tester_id", "name", "role", "years_experience", "setting", "wearable_familiarity",
          "would_use"] + [k for k, _ in STATEMENTS] + [k for k, _ in OPEN_QUESTIONS] + ["contact_ok", "email"]


def save(response: dict):
    """Append to the local CSV, then (if configured) push the same row to Google Sheets.
    Returns (row, sync_status) where sync_status is 'synced', 'failed: <reason>' or 'off'."""
    FEEDBACK_DIR.mkdir(exist_ok=True)
    new = not FEEDBACK_FILE.exists()
    row = {k: response.get(k, "") for k in FIELDS}
    row["timestamp"] = datetime.now().isoformat(timespec="seconds")
    with open(FEEDBACK_FILE, "a", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=FIELDS)
        if new:
            w.writeheader()
        w.writerow(row)
    status = "off"
    url, key = webhook()
    if url:
        status = push_to_sheet(row, url, key)
    return row, status


def push_to_sheet(row, url, key, timeout=15):
    if requests is None:
        return "failed: requests not installed"
    try:
        payload = {k: ("" if v is None else str(v)) for k, v in row.items()}
        payload["key"] = key
        r = requests.post(url, json=payload, timeout=timeout, allow_redirects=True)
        try:
            body = r.json()
        except ValueError:
            body = {}
        if r.ok and body.get("ok"):
            return "synced"
        return f"failed: HTTP {r.status_code} {body.get('error', '')}".strip()
    except Exception as e:  # network errors never block the local save
        return f"failed: {type(e).__name__}"


def load_all(prefer_sheet=True):
    """All responses: from Google Sheets when configured (so the organiser view works in the cloud),
    otherwise from the local CSV."""
    import pandas as pd
    url, key = webhook()
    if prefer_sheet and url and requests is not None:
        try:
            r = requests.get(url, params={"key": key}, timeout=20, allow_redirects=True)
            rows = r.json()
            if isinstance(rows, list):
                return pd.DataFrame(rows, columns=FIELDS) if rows else pd.DataFrame(columns=FIELDS)
        except Exception:
            pass
    if not FEEDBACK_FILE.exists():
        return pd.DataFrame(columns=FIELDS)
    return pd.read_csv(FEEDBACK_FILE)

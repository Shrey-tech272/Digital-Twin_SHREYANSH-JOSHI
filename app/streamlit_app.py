"""
Manas Twin - interactive dashboard (v2: story mode, mind-weather, dark/light themes).

Run from the repository root:
    streamlit run app/streamlit_app.py
"""
import hashlib
import json
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src import config as C  # noqa: E402
from src.fhir import build_bundle  # noqa: E402
from src import feedback as FB  # noqa: E402
from src.simulator import simulate_custom  # noqa: E402
from src.train import readable  # noqa: E402
from src.twin import DigitalTwin, fmt_clock, load_assets  # noqa: E402

st.set_page_config(page_title="Manas Twin · Mind-weather for depressive-episode early warning",
                   page_icon="🧠", layout="wide", initial_sidebar_state="expanded")

# =============================================================================
# Theme
# =============================================================================
PALETTES = {
    "light": dict(bg="#F5F8F8", surface="#FFFFFF", surface2="#EDF4F3", text="#13262F", muted="#5B6B73",
                  border="#DCE6E5", teal="#0F7C78", amber="#C98316", red="#C8553D", green="#2E9D6B",
                  teal_t="rgba(15,124,120,0.10)", amber_t="rgba(201,131,22,0.12)", red_t="rgba(200,85,61,0.11)",
                  green_t="rgba(46,157,107,0.10)", grid="#E3EAEA", shadow="0 1px 3px rgba(19,38,47,0.07)"),
    "dark": dict(bg="#0D181D", surface="#15242A", surface2="#1C2F36", text="#E7EFF1", muted="#9DB1B6",
                 border="#28403F", teal="#42BDB2", amber="#F0B44C", red="#F07E66", green="#56C98F",
                 teal_t="rgba(66,189,178,0.14)", amber_t="rgba(240,180,76,0.15)", red_t="rgba(240,126,102,0.15)",
                 green_t="rgba(86,201,143,0.13)", grid="#24373C", shadow="0 1px 3px rgba(0,0,0,0.35)"),
}

if "dark" not in st.session_state:
    st.session_state.dark = False
MODE = "dark" if st.session_state.dark else "light"
P = PALETTES[MODE]

WEATHER = {
    "Stable": dict(icon="☀️", sky="Clear skies", color=P["green"], tint=P["green_t"],
                   plain="Rhythm is close to their usual self."),
    "Watch": dict(icon="⛅", sky="Clouds gathering", color=P["amber"], tint=P["amber_t"],
                  plain="Some signals are drifting away from their normal."),
    "Early warning": dict(icon="⛈️", sky="Storm likely", color=P["red"], tint=P["red_t"],
                          plain="Strong drift: a low-mood episode may be close."),
    "Learning baseline": dict(icon="🌱", sky="Still learning", color=P["muted"], tint=P["surface2"],
                              plain="The twin needs 60 days to learn what normal looks like."),
}
ACTIONS = {
    "Stable": "No action suggested. Routine check-ins as usual.",
    "Watch": "Suggested: a light-touch check-in; review sleep, activity and stressors with the client.",
    "Early warning": "Suggested: contact within 48 hours and administer a PHQ-9. Clinical judgement decides next steps.",
    "Learning baseline": "Keep collecting data so the twin can learn this client's normal.",
}

CSS = f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&display=swap');
:root {{
  --bg:{P['bg']}; --surface:{P['surface']}; --surface2:{P['surface2']}; --text:{P['text']}; --muted:{P['muted']};
  --border:{P['border']}; --teal:{P['teal']}; --amber:{P['amber']}; --red:{P['red']}; --green:{P['green']};
  --teal-t:{P['teal_t']}; --shadow:{P['shadow']};
}}
html, body, .stApp, [data-testid="stAppViewContainer"] {{ background: var(--bg) !important; color: var(--text);
  font-family: 'Plus Jakarta Sans', 'Segoe UI', system-ui, sans-serif; }}
.stApp p, .stApp li, .stApp label, .stApp h1, .stApp h2, .stApp h3, .stApp h4, .stApp h5,
.stApp div[data-testid="stMarkdownContainer"] {{ color: var(--text); font-family: 'Plus Jakarta Sans', 'Segoe UI', system-ui, sans-serif; }}
.stApp div[data-testid="stMarkdownContainer"] span {{ font-family: inherit; }}
header[data-testid="stHeader"] {{ background: transparent !important; }}
header[data-testid="stHeader"] * {{ color: var(--muted) !important; }}
[data-testid="stSidebar"] {{ background: var(--surface) !important; border-right: 1px solid var(--border); }}
[data-testid="stSidebar"] * {{ color: var(--text); }}
.block-container {{ padding-top: 1.2rem; max-width: 1350px; }}
[data-baseweb="select"] > div, [data-baseweb="input"], [data-baseweb="input"] input, [data-baseweb="base-input"] {{
  background: var(--surface2) !important; color: var(--text) !important; border-color: var(--border) !important; }}
[data-baseweb="select"], [data-baseweb="select"] div {{ background-color: var(--surface2) !important; color: var(--text) !important; }}
[data-baseweb="select"] input {{ color: var(--text) !important; }}
[data-testid="stSelectbox"] div, [data-testid="stNumberInput"] div, [data-testid="stNumberInput"] input {{
  background-color: var(--surface2) !important; color: var(--text) !important; border-color: var(--border) !important; }}
[data-testid="stSelectbox"] [data-testid="stWidgetLabel"], [data-testid="stSelectbox"] [data-testid="stWidgetLabel"] *,
[data-testid="stNumberInput"] [data-testid="stWidgetLabel"], [data-testid="stNumberInput"] [data-testid="stWidgetLabel"] *,
[data-testid="stSelectbox"] > div:first-child:has([data-testid="stWidgetLabel"]) {{ background-color: transparent !important; }}
[data-testid="stSelectbox"] svg {{ fill: var(--muted) !important; color: var(--muted) !important; }}
[role="listbox"] {{ background-color: var(--surface) !important; }}
[role="option"] {{ background-color: var(--surface) !important; color: var(--text) !important; }}
[role="option"] * {{ color: var(--text) !important; }}
[role="option"]:hover, [role="option"][aria-selected="true"], [role="option"][data-focused="true"] {{ background-color: var(--surface2) !important; }}
[data-baseweb="select"] svg {{ fill: var(--muted) !important; }}
div[data-baseweb="popover"] ul, div[data-baseweb="popover"] [role="listbox"] {{ background: var(--surface) !important; }}
div[data-baseweb="popover"] li {{ color: var(--text) !important; background: var(--surface) !important; }}
div[data-baseweb="popover"] li:hover, div[data-baseweb="popover"] [aria-selected="true"] {{ background: var(--surface2) !important; }}
[data-testid="stSliderTickBarMin"], [data-testid="stSliderTickBarMax"] {{ color: var(--muted) !important; }}
.stButton button, .stDownloadButton button {{ background: var(--surface) !important; color: var(--text) !important;
  border: 1px solid var(--border) !important; border-radius: 999px !important; font-weight: 600; }}
.stButton button p, .stDownloadButton button p {{ color: inherit !important; }}
.stButton button:hover, .stDownloadButton button:hover {{ border-color: var(--teal) !important; color: var(--teal) !important; }}
.stButton button[kind="primary"] {{ background: var(--teal) !important; color: #fff !important; border-color: var(--teal) !important; }}
.stButton button[kind="primary"] p {{ color: #fff !important; }}
.stButton button:disabled {{ opacity: 0.45; }}
[data-testid="stExpander"] details {{ background: var(--surface) !important; border: 1px solid var(--border) !important; border-radius: 14px; }}
[data-testid="stExpander"] summary {{ color: var(--text) !important; }}
[data-testid="stCode"] pre, .stCode pre {{ background: var(--surface2) !important; }}
[data-testid="stCode"] code, [data-testid="stCode"] code span {{ color: var(--text) !important; background: transparent !important; }}
hr {{ border-color: var(--border) !important; }}
.st-key-nav div[role="radiogroup"] {{ gap: 0.45rem; flex-wrap: wrap; }}
.st-key-nav [data-testid="stRadioOption"], .st-key-nav div[role="radiogroup"] > label {{ background: var(--surface);
  border: 1px solid var(--border); border-radius: 999px; padding: 0.38rem 0.95rem; margin: 0 !important; box-shadow: var(--shadow); cursor: pointer; }}
.st-key-nav [data-testid="stRadioOption"] > div > div:not([data-testid="stMarkdownContainer"]),
.st-key-nav div[role="radiogroup"] > label > div:first-child:not([data-testid="stMarkdownContainer"]):not(:has([data-testid="stMarkdownContainer"])) {{ display: none !important; }}
.st-key-nav [data-testid="stRadioOption"][data-selected="true"], .st-key-nav [data-testid="stRadioOption"]:has(input:checked),
.st-key-nav div[role="radiogroup"] > label:has(input:checked) {{ background: var(--teal); border-color: var(--teal); }}
.st-key-nav [data-testid="stRadioOption"][data-selected="true"] p, .st-key-nav [data-testid="stRadioOption"]:has(input:checked) p,
.st-key-nav div[role="radiogroup"] > label:has(input:checked) p {{ color: #fff !important; }}
.st-key-nav [data-testid="stRadioOption"] p, .st-key-nav div[role="radiogroup"] > label p {{ font-weight: 600; font-size: 0.92rem; }}
.st-key-nav [data-testid="stRadioOption"]:hover {{ border-color: var(--teal); }}
.brand {{ display:flex; align-items:center; gap:0.6rem; margin-bottom:0.3rem; }}
.brand .logo {{ width:40px; height:40px; border-radius:12px; background:linear-gradient(135deg,var(--teal),#2F5D8A);
  display:flex; align-items:center; justify-content:center; font-size:1.3rem; }}
.brand .t {{ font-weight:800; font-size:1.25rem; line-height:1.1; }}
.brand .s {{ font-size:0.78rem; color:var(--muted) !important; }}
.card {{ background:var(--surface); border:1px solid var(--border); border-radius:18px; padding:1rem 1.15rem; box-shadow:var(--shadow); height:100%; }}
.muted, .muted * {{ color:var(--muted) !important; }}
.eyebrow {{ font-size:0.74rem; font-weight:700; letter-spacing:0.08em; text-transform:uppercase; color:var(--muted) !important; }}
.hero {{ border-radius:22px; padding:1.3rem 1.5rem; border:1px solid var(--border); display:flex; gap:1.3rem; align-items:center; box-shadow:var(--shadow); }}
.hero .wx {{ font-size:4.2rem; line-height:1; }}
.hero .status {{ font-size:1.7rem; font-weight:800; line-height:1.15; }}
.hero .sub {{ font-size:1rem; margin-top:0.35rem; }}
.hero .num {{ text-align:right; min-width:150px; }}
.hero .num .big {{ font-size:2.5rem; font-weight:800; line-height:1; margin-top:0.2rem; }}
.pill {{ display:inline-block; padding:0.18rem 0.7rem; border-radius:999px; font-size:0.78rem; font-weight:700; white-space:nowrap; }}
.sig {{ background:var(--surface); border:1px solid var(--border); border-radius:16px; padding:0.8rem 0.9rem 0.6rem; box-shadow:var(--shadow); height:100%; }}
.sig .h {{ display:flex; justify-content:space-between; align-items:center; gap:0.4rem; }}
.sig .name {{ font-weight:700; font-size:0.92rem; }}
.sig .vals {{ font-size:0.82rem; color:var(--muted) !important; margin:0.25rem 0 0.1rem; }}
.sig .vals b {{ color:var(--text) !important; }}
.sig .verdict {{ font-size:0.88rem; font-weight:600; margin-top:0.15rem; }}
.callout {{ border-radius:14px; padding:0.8rem 1rem; border:1px solid var(--border); font-size:0.95rem; }}
.drv {{ display:grid; grid-template-columns: 1.6rem 1fr 34%; gap:0.6rem; align-items:center; padding:0.42rem 0; border-bottom:1px dashed var(--border); }}
.drv:last-child {{ border-bottom:none; }}
.drv .bar {{ height:10px; border-radius:6px; background:var(--red); }}
.drv .track {{ background:var(--surface2); border-radius:6px; }}
.tl {{ position:relative; padding-left:1.1rem; }}
.tl .ev {{ position:relative; padding:0 0 0.9rem 1.1rem; border-left:2px solid var(--border); }}
.tl .ev:last-child {{ border-left-color:transparent; }}
.tl .dot {{ position:absolute; left:-0.95rem; top:-0.15rem; width:1.75rem; height:1.75rem; border-radius:50%; display:flex; align-items:center;
  justify-content:center; background:var(--surface2); font-size:0.9rem; }}
.tl .d {{ font-size:0.78rem; color:var(--muted) !important; }}
table.mt {{ width:100%; border-collapse:separate; border-spacing:0; font-size:0.9rem; }}
table.mt th {{ text-align:left; font-size:0.72rem; text-transform:uppercase; letter-spacing:0.06em; color:var(--muted) !important; padding:0.5rem 0.55rem; border-bottom:1px solid var(--border); }}
table.mt td {{ padding:0.55rem 0.55rem; border-bottom:1px solid var(--border); color:var(--text); }}
table.mt tr:hover td {{ background:var(--surface2); }}
.steps {{ display:flex; gap:0.4rem; margin:0.2rem 0 0.8rem; }}
.steps .s {{ flex:1; height:6px; border-radius:4px; background:var(--border); }}
.steps .s.on {{ background:var(--teal); }}
.story {{ font-size:1.06rem; line-height:1.65; }}
.kpi .v {{ font-size:2.1rem; font-weight:800; line-height:1.1; color:var(--c, var(--teal)) !important; }}
.kpi .l {{ font-size:0.88rem; }}
.kpi .c {{ font-size:0.78rem; color:var(--muted) !important; margin-top:0.2rem; }}
.foot {{ font-size:0.78rem; color:var(--muted) !important; }}
.foot b {{ color:var(--text) !important; }}
</style>"""
st.markdown(CSS, unsafe_allow_html=True)


def style_fig(fig, height=None, legend=False):
    fig.update_layout(
        template="plotly_dark" if MODE == "dark" else "plotly_white",
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        font=dict(family="Plus Jakarta Sans, Segoe UI, sans-serif", color=P["text"], size=12),
        margin=dict(l=10, r=10, t=10, b=10), showlegend=legend,
        hoverlabel=dict(bgcolor=P["surface"], font_color=P["text"]),
    )
    fig.update_xaxes(gridcolor=P["grid"], zeroline=False, linecolor=P["border"])
    fig.update_yaxes(gridcolor=P["grid"], zeroline=False, linecolor=P["border"])
    if height:
        fig.update_layout(height=height)
    return fig


def show_chart(fig, key=None, target=None):
    target = target or st
    kw = dict(theme=None, config={"displayModeBar": False})
    if key:
        kw["key"] = key
    try:
        target.plotly_chart(fig, width="stretch", **kw)
    except TypeError:
        target.plotly_chart(fig, use_container_width=True, **kw)


def html(s, target=None):
    (target or st).markdown(s, unsafe_allow_html=True)


# =============================================================================
# Data + helpers
# =============================================================================
@st.cache_resource(show_spinner="Waking up the twins ...")
def assets():
    return load_assets()


@st.cache_resource(show_spinner=False, max_entries=60)
def _twin_cached(pid):
    return DigitalTwin(pid, assets())


def twin(pid):
    """Twin for a stored client, or for a client enrolled live in this session."""
    custom = st.session_state.get("custom_clients", {})
    if pid in custom:
        return custom[pid]["twin"]
    return _twin_cached(pid)


A = assets()
META = A["meta"]
THR = META["threshold"]
SHOWCASE = json.loads((C.DATA_DIR / "showcase.json").read_text())["patients"]
SHOW_IDS = [s["patient_id"] for s in SHOWCASE]
TEST_IDS = META["test_patients"]
PAT = A["patients"].set_index("patient_id")

# Display names make the synthetic people relatable. They are invented, like the data.
M_NAMES = ["Arjun", "Rohan", "Aditya", "Kabir", "Vihaan", "Ishaan", "Rahul", "Siddharth", "Nikhil", "Karthik",
           "Aman", "Varun", "Pranav", "Harsh", "Yash", "Dev", "Farhan", "Aakash", "Manav", "Joel"]
F_NAMES = ["Ananya", "Priya", "Diya", "Meera", "Isha", "Kavya", "Sneha", "Riya", "Aisha", "Pooja",
           "Neha", "Tanvi", "Shreya", "Nandini", "Sara", "Aditi", "Fatima", "Lakshmi", "Mitali", "Anjali"]
FIXED = {"MT0441": "Arjun", "MT0156": "Rohan"}


def name_of(pid):
    custom = st.session_state.get("custom_clients", {})
    if pid in custom:
        return custom[pid]["name"]
    if pid in FIXED:
        return FIXED[pid]
    h = int(hashlib.md5(pid.encode()).hexdigest(), 16)
    pool = F_NAMES if PAT.loc[pid, "sex"] == "F" else M_NAMES
    return pool[h % len(pool)]


def patient_row(pid):
    custom = st.session_state.get("custom_clients", {})
    return custom[pid]["twin"].patient if pid in custom else PAT.loc[pid]


SIG_ICON = {"sleep_hours": "😴", "sleep_onset": "🌙", "sleep_efficiency": "🛏️", "resting_hr": "❤️",
            "hrv_rmssd": "💓", "steps": "🚶", "night_screen_min": "📱", "social_contacts": "💬"}
SIG_SHORT = {"sleep_hours": "Sleep", "sleep_onset": "Bedtime", "sleep_efficiency": "Sleep quality",
             "resting_hr": "Resting heart rate", "hrv_rmssd": "Heart-rate variability", "steps": "Steps",
             "night_screen_min": "Late-night phone", "social_contacts": "Social contact"}
SIG_HELP = {"hrv_rmssd": "Variation between heartbeats; it tends to fall under stress.",
            "sleep_efficiency": "Share of time in bed actually asleep."}


def fmt_val(sig, v):
    if v is None or pd.isna(v):
        return "–"
    if sig == "sleep_hours":
        return f"{int(v)}h {int(round((v % 1) * 60)) % 60:02d}m"
    if sig == "sleep_onset":
        return fmt_clock(v)
    if sig == "sleep_efficiency":
        return f"{v:.0f}%"
    if sig == "resting_hr":
        return f"{v:.0f} bpm"
    if sig == "hrv_rmssd":
        return f"{v:.0f} ms"
    if sig == "steps":
        return f"{v:,.0f}"
    if sig == "night_screen_min":
        return f"{v:.0f} min"
    return f"{v:.0f}/day"


def risk_score(sig, z):
    """Deviation in the 'toward risk' direction."""
    if pd.isna(z):
        return 0.0
    d = C.RISK_DIRECTION[sig]
    return abs(z) if d == 0 else d * z


def phrase(sig, now, base):
    """Everyday-language description of a change."""
    if pd.isna(now) or pd.isna(base) or not base:
        return None
    pct = 100 * (now - base) / base
    mins = (now - base) * 60
    return {
        "sleep_hours": f"sleeping {abs(mins):.0f} min {'less' if mins < 0 else 'more'} than usual",
        "sleep_onset": f"going to bed {abs(mins):.0f} min {'later' if mins > 0 else 'earlier'} than usual",
        "sleep_efficiency": "sleeping less soundly" if pct < 0 else "sleeping more soundly",
        "resting_hr": f"running a resting heart rate {abs(pct):.0f}% {'higher' if pct > 0 else 'lower'} than usual",
        "hrv_rmssd": f"showing heart-rate variability {abs(pct):.0f}% {'lower' if pct < 0 else 'higher'} than usual",
        "steps": f"walking {abs(pct):.0f}% {'less' if pct < 0 else 'more'} than usual",
        "night_screen_min": f"spending {abs(pct):.0f}% {'more' if pct > 0 else 'less'} time on the phone late at night",
        "social_contacts": f"having {abs(pct):.0f}% {'fewer' if pct < 0 else 'more'} social contacts",
    }[sig]


def verdict(score):
    if score >= 1.5:
        return "Big change", P["red"], P["red_t"]
    if score >= 0.75:
        return "Drifting", P["amber"], P["amber_t"]
    return "Usual", P["green"], P["green_t"]


RHYTHM_PREFIXES = ("z7_", "z3_", "dz7_", "raw7_")
RHYTHM_OTHER = {"twin_deviation_index", "sleep_onset_irregularity7", "missing_days7"}


def is_rhythm_feature(f):
    return f.startswith(RHYTHM_PREFIXES) or f in RHYTHM_OTHER


BACKGROUND_TEXT = {"phq9_last": "a high recent PHQ-9", "phq9_change": "a recent PHQ-9 swing", "days_since_phq9": "time since the last PHQ-9",
                   "prior_episodes": "previous episodes", "diagnosed_episodes_so_far": "a recent diagnosed episode",
                   "days_since_last_diagnosis": "a recent diagnosed episode", "family_history_depression": "family history",
                   "on_antidepressant": "current medication", "known_stressor_period": "exam / work-crunch season",
                   "age": "age", "is_student": "being a student", "is_female": "sex", "hypothyroidism": "hypothyroidism",
                   "anaemia": "anaemia", "vitamin_d_deficiency": "vitamin D deficiency"}


def background_share(tw, day, feats=None):
    """Share of the positive SHAP push that comes from history/context rather than this week's rhythm."""
    ex = tw.explain(day, k=60, feats=feats)
    pos = ex[ex.shap > 0]
    if not len(pos):
        return 0.0, []
    bg = pos[~pos.feature.map(is_rhythm_feature)]
    names = [BACKGROUND_TEXT.get(f, readable(f).lower()) for f in bg.sort_values("shap", ascending=False).feature.head(3)]
    return float(bg.shap.sum() / pos.shap.sum()), names


def summary_sentence(tw, day):
    s = tw.state(day)
    nm = name_of(tw.pid)
    sg = s["signals"].copy()
    sg["score"] = [risk_score(a, b) for a, b in zip(sg.signal, sg.z)]
    top = sg[sg.score >= 0.6].sort_values("score", ascending=False).head(3)
    parts = [p for p in (phrase(r.signal, r.current_7d, r.baseline) for r in top.itertuples()) if p]
    pron = "her" if patient_row(tw.pid)["sex"] == "F" else "his"
    share, names = background_share(tw, day) if s["band"] in ("Watch", "Early warning") else (0.0, [])
    bg_txt = ", ".join(names[:-1]) + (" and " if len(names) > 1 else "") + names[-1] if names else ""
    if not parts:
        base = f"Over the last week, {nm}'s rhythm has looked like {pron} usual self."
        if share >= 0.5 and names:
            base += f" The estimate is driven mainly by background risk ({bg_txt}), not by this week's data."
        return base
    sent = (f"Over the last week, {nm} has been {parts[0]}." if len(parts) == 1
            else f"Over the last week, {nm} has been {', '.join(parts[:-1])} and {parts[-1]}.")
    if share >= 0.6 and names:
        sent += f" Background risk ({bg_txt}) adds to this."
    return sent


def in_care(tw, day):
    e = tw.ehr_until(day)
    dx = e[e["type"] == "diagnosis"]
    if len(dx):
        return (pd.Timestamp(tw.daily.loc[day, "date"]) - pd.Timestamp(dx["date"].iloc[-1])).days <= 60
    return False


def sparkline(values, base, sd, color, w=220, h=44):
    v = np.array(values, dtype=float)
    ok = ~np.isnan(v)
    if ok.sum() < 3:
        return ""
    has_band = not (np.isnan(base) or np.isnan(sd))
    lo_b, hi_b = (base - sd, base + sd) if has_band else (np.nan, np.nan)
    lo = np.nanmin(np.r_[v[ok], lo_b]) if has_band else np.nanmin(v)
    hi = np.nanmax(np.r_[v[ok], hi_b]) if has_band else np.nanmax(v)
    rng = (hi - lo) or 1

    def y(q):
        return h - 3 - (q - lo) / rng * (h - 6)
    xs = np.linspace(2, w - 2, len(v))
    pts = " ".join(f"{x:.1f},{y(q):.1f}" for x, q in zip(xs[ok], v[ok]))
    band = (f"<rect x='0' y='{y(hi_b):.1f}' width='{w}' height='{max(1, y(lo_b) - y(hi_b)):.1f}' rx='4' "
            f"fill='{P['teal']}' opacity='0.15'/>") if has_band else ""
    last = f"<circle cx='{xs[ok][-1]:.1f}' cy='{y(v[ok][-1]):.1f}' r='3.4' fill='{color}'/>"
    return (f"<svg viewBox='0 0 {w} {h}' width='100%' height='{h}' preserveAspectRatio='none'>{band}"
            f"<polyline points='{pts}' fill='none' stroke='{color}' stroke-width='2.2' stroke-linejoin='round' "
            f"stroke-linecap='round' vector-effect='non-scaling-stroke'/>{last}</svg>")


# =============================================================================
# Reusable visual components
# =============================================================================
def hero(tw, day, target=None, compact=False):
    s = tw.state(day)
    nm = name_of(tw.pid)
    band = s["band"]
    w = WEATHER[band]
    risk_txt = "–" if pd.isna(s["risk"]) else f"{100 * s['risk']:.1f}%"
    rel = "" if pd.isna(s["relative_risk"]) else f"{s['relative_risk']:.1f}× a typical person"
    if pd.notna(s["risk"]):
        line = 100 * tw.threshold
        if s.get("rising"):
            rel += f" · ↗ just crossed the alert line ({line:.1f}%) today; shown as Watch until it holds"
        elif s.get("borderline"):
            rel += f" · {'just over' if s['risk'] >= tw.threshold else 'just under'} the alert line ({line:.1f}%)"
    sentence = summary_sentence(tw, day) if band != "Learning baseline" else w["plain"]
    care = (f"<div style='margin-top:0.55rem'><span class='pill' style='background:{P['teal_t']};color:{P['teal']}'>"
            "🩺 Already in care · the twin keeps watching for relapse</span></div>") if in_care(tw, day) else ""
    if compact:
        html(f"""
<div class='hero' style='background:{w['tint']};flex-direction:column;align-items:flex-start;gap:0.4rem'>
  <div style='display:flex;align-items:center;gap:0.9rem'>
    <div class='wx' style='font-size:3.2rem'>{w['icon']}</div>
    <div><div class='eyebrow'>{nm}'s mind-weather</div>
      <div class='status' style='color:{w['color']}'>{w['sky']}</div>
      <div class='muted' style='font-weight:700'>{band}</div></div>
    <div style='margin-left:auto;text-align:right;padding-left:1rem'><div class='big' style='font-size:2.3rem;font-weight:800;color:{w['color']}'>{risk_txt}</div>
      <div class='muted' style='font-size:0.8rem'>chance of an episode<br>in the next 7 days</div></div>
  </div>
  <div class='sub'>{sentence}</div>
  <div class='sub muted' style='font-size:0.92rem'>👉 {ACTIONS[band]}</div>{care}
</div>""", target)
        return
    html(f"""
<div class='hero' style='background:{w['tint']}'>
  <div class='wx'>{w['icon']}</div>
  <div style='flex:1'>
    <div class='eyebrow'>{nm}'s mind-weather · {pd.Timestamp(s['date']).strftime('%a %d %b %Y')}</div>
    <div class='status' style='color:{w['color']}'>{w['sky']} <span class='muted' style='font-size:1rem;font-weight:700'>· {band}{' · rising' if s.get('rising') else ''}</span></div>
    <div class='sub'>{sentence}</div>
    <div class='sub muted' style='font-size:0.92rem'>👉 {ACTIONS[band]}</div>{care}
  </div>
  <div class='num'><div class='eyebrow'>Chance of an episode<br>in the next 7 days</div>
    <div class='big' style='color:{w['color']}'>{risk_txt}</div><div class='muted' style='font-size:0.85rem'>{rel}</div></div>
</div>""", target)


def signal_cards(tw, day, cols=4):
    s = tw.state(day)
    full = tw.daily.set_index("day")
    win = range(max(0, day - 29), day + 1)
    sg = s["signals"]
    for i0 in range(0, len(sg), cols):
        cs = st.columns(cols)
        for c, r in zip(cs, sg.iloc[i0:i0 + cols].itertuples()):
            vtxt, vcol, vt = verdict(risk_score(r.signal, r.z))
            sm = full[r.signal].rolling(3, min_periods=1).mean().reindex(win).values
            sd = full[r.signal].shift(C.BASELINE_GAP).rolling(C.BASELINE_WINDOW, min_periods=20).std().get(day, np.nan)
            ph = phrase(r.signal, r.current_7d, r.baseline) or "not enough data yet"
            if vtxt == "Usual" and ph != "not enough data yet":
                ph = "close to usual"
            tip = f" title='{SIG_HELP[r.signal]}'" if r.signal in SIG_HELP else ""
            html(f"""
<div class='sig'{tip}>
  <div class='h'><div class='name'>{SIG_ICON[r.signal]} {SIG_SHORT[r.signal]}</div>
    <span class='pill' style='background:{vt};color:{vcol}'>{vtxt}</span></div>
  <div class='vals'>usual <b>{fmt_val(r.signal, r.baseline)}</b> → last 7 days <b>{fmt_val(r.signal, r.current_7d)}</b></div>
  {sparkline(sm, r.baseline, sd, vcol)}
  <div class='verdict' style='color:{vcol}'>{ph[0].upper() + ph[1:]}</div>
</div>""", c)
        st.write("")


def risk_chart(tw, upto, start=C.MIN_HISTORY_DAYS, end=None, height=330, gt=True, mark_day=True):
    rs = tw.risk_series()
    end = end if end is not None else upto
    rs = rs[(rs.day >= start - 2) & (rs.day <= upto)]
    dates = pd.to_datetime(rs.date)
    r = 100 * rs.risk
    t = 100 * THR
    ymax = float(min(max(1.7 * t, (r.max() if r.notna().any() else 0) * 1.15), 22))
    x0 = pd.Timestamp(tw.daily.loc[max(start - 2, 0), "date"])
    x1 = pd.Timestamp(tw.daily.loc[min(max(end, upto) + 2, tw.n_days - 1), "date"])
    fig = go.Figure()
    for y0, y1, col in [(0, t / 2, P["green"]), (t / 2, t, P["amber"]), (t, ymax, P["red"])]:
        fig.add_hrect(y0=y0, y1=y1, fillcolor=col, opacity=0.07 if MODE == "light" else 0.10, line_width=0, layer="below")
    for y_, lab in [(t / 4, "☀️ clear"), (t * 0.75, "⛅ watch"), (min(t * 1.3, ymax * 0.93), "⛈️ early warning")]:
        fig.add_annotation(x=x1, y=y_, xanchor="right", text=lab, showarrow=False, font=dict(size=10, color=P["muted"]))
    if gt:
        flags = rs.in_episode.values
        a = None
        for i, f in enumerate(flags):
            if f and a is None:
                a = i
            if a is not None and (not f or i == len(flags) - 1):
                b = i if f else i - 1
                fig.add_vrect(x0=dates.iloc[a], x1=dates.iloc[b], fillcolor=P["muted"], opacity=0.18, line_width=0,
                              annotation_text="actual episode", annotation_position="top left",
                              annotation_font=dict(size=10, color=P["muted"]))
                a = None
    e = tw.ehr_until(upto)
    for _, ev in e[e["type"] == "diagnosis"].iterrows():
        if pd.Timestamp(ev["date"]) >= x0:
            fig.add_vline(x=pd.Timestamp(ev["date"]), line_dash="dot", line_color=P["muted"])
            fig.add_annotation(x=pd.Timestamp(ev["date"]), y=ymax * 0.9, text=" 🩺 diagnosed", showarrow=False,
                               xanchor="left", font=dict(size=11, color=P["text"]))
    fig.add_trace(go.Scatter(x=dates, y=r.clip(upper=ymax * 0.98), mode="lines", customdata=r,
                             line=dict(color=P["text"], width=2.6, shape="spline", smoothing=0.5),
                             hovertemplate="%{x|%d %b}<br>%{customdata:.1f}% chance<extra></extra>"))
    if mark_day and len(rs) and pd.notna(rs.iloc[-1].risk):
        last = rs.iloc[-1]
        fig.add_trace(go.Scatter(x=[pd.Timestamp(last.date)], y=[min(100 * last.risk, ymax * 0.98)], mode="markers",
                                 marker=dict(size=14, color=WEATHER[tw.band(last.risk, tw.prev_risk(int(last.day)))]["color"],
                                             line=dict(color=P["surface"], width=3)), hoverinfo="skip"))
    fig.update_yaxes(range=[0, ymax], title="chance of an episode in next 7 days (%)", title_font_size=11)
    fig.update_xaxes(range=[x0, x1], tickformat="%d %b")
    return style_fig(fig, height)


DRV_ICON = {f"{p}{s}": SIG_ICON[s] for s in C.SIGNALS for p in ("z7_", "z3_", "dz7_", "raw7_")}
DRV_ICON.update({"phq9_last": "📋", "phq9_change": "📋", "days_since_phq9": "📋", "known_stressor_period": "📚",
                 "prior_episodes": "🗂️", "twin_deviation_index": "🧭", "sleep_onset_irregularity7": "🌙",
                 "missing_days7": "⌚", "family_history_depression": "👪", "on_antidepressant": "💊", "age": "🎂"})


def driver_text(feature, value, row_now, row_base):
    """Turn a model feature into an everyday sentence."""
    for pre in ("z7_", "z3_", "dz7_", "raw7_"):
        if feature.startswith(pre):
            sig = feature[len(pre):]
            if pre == "raw7_":
                return f"{SIG_SHORT[sig]} this week: {fmt_val(sig, row_now.get(sig))}"
            ph = phrase(sig, row_now.get(sig), row_base.get(sig))
            when = "in the last 3 days" if pre == "z3_" else "this week" if pre == "z7_" else "vs. last week"
            if not ph:
                return f"{SIG_SHORT[sig]} changing ({when})"
            return f"{ph[0].upper() + ph[1:]} ({when})"
    v = value
    if feature == "phq9_last":
        return f"Latest mood check-in (PHQ-9) score: {v:.0f}"
    if feature == "phq9_change":
        return (f"Mood check-in score {'dropped' if v < 0 else 'rose'} {abs(v):.0f} points at the last check-in "
                "(big swings often follow a recent episode)")
    if feature == "days_since_phq9":
        return f"{v:.0f} days since the last mood check-in"
    if feature == "known_stressor_period":
        return "Exam or work-crunch season" if v else "Not in an exam / crunch period"
    if feature == "prior_episodes":
        return f"Has had {v:.0f} depressive episode{'s' if v != 1 else ''} before"
    if feature == "twin_deviation_index":
        return "Overall drift away from their own normal"
    if feature == "sleep_onset_irregularity7":
        return "Irregular bedtimes this week"
    if feature == "missing_days7":
        return f"Watch not worn on {v:.0f} of the last 7 days"
    if feature == "family_history_depression":
        return "Family history of depression"
    if feature == "on_antidepressant":
        return "Currently on an antidepressant"
    return readable(feature)


def drivers_html(ex, max_items=6, tw=None, day=None, feats=None):
    ex = ex[ex.shap > 0].head(max_items)
    if not len(ex):
        return "<div class='muted'>Nothing is pushing the risk up right now.</div>"
    mx = ex.shap.max()
    now, base = {}, {}
    if tw is not None:
        fx = feats if feats is not None else tw.feats
        row = fx.loc[fx.day == day].iloc[0]
        now = {s_: row[f"raw7_{s_}"] for s_ in C.SIGNALS}
        base = {s_: row[f"base_{s_}"] for s_ in C.SIGNALS}
    def row(r, color):
        txt = driver_text(r.feature, r.value, now, base) if tw is not None else r.driver
        return (f"<div class='drv'><div>{DRV_ICON.get(r.feature, '•')}</div><div style='font-size:0.9rem'>{txt}</div>"
                f"<div class='track'><div class='bar' style='width:{max(6, 100 * r.shap / mx):.0f}%;background:{color}'></div></div></div>")
    week = [r for r in ex.itertuples() if is_rhythm_feature(r.feature)]
    bg = [r for r in ex.itertuples() if not is_rhythm_feature(r.feature)]
    out = ""
    if week:
        out += "<div class='eyebrow' style='margin:0.2rem 0'>This week's rhythm</div>" + "".join(row(r, P["red"]) for r in week)
    if bg:
        out += "<div class='eyebrow' style='margin:0.6rem 0 0.2rem'>Background risk (history &amp; context)</div>" + "".join(row(r, P["amber"]) for r in bg)
    return out


def callout(text, kind="info", target=None):
    bg, bd = {"info": (P["teal_t"], P["teal"]), "warn": (P["amber_t"], P["amber"]), "danger": (P["red_t"], P["red"])}[kind]
    html(f"<div class='callout' style='background:{bg};border-color:{bd}'>{text}</div>", target)


def ehr_timeline(tw, day):
    e = tw.ehr_until(day)
    if not len(e):
        return "<div class='muted'>No health-record events yet.</div>"
    icon = {"phq9_screening": "📋", "diagnosis": "🩺", "medication_start": "💊", "therapy_referral": "🗣️"}
    out = "<div class='tl'>"
    for _, r in e.iloc[::-1].head(8).iterrows():
        if r["type"] == "phq9_screening":
            sc = int(r["phq9"])
            sev = ("minimal" if sc < 5 else "mild" if sc < 10 else "moderate" if sc < 15
                   else "moderately severe" if sc < 20 else "severe")
            label = f"PHQ-9 check-in: <b>{sc}</b> <span class='muted'>({sev})</span>"
        elif r["type"] == "diagnosis":
            label = f"<b>Diagnosed</b>: depressive episode (ICD-10 F32), PHQ-9 {int(r['phq9'])}"
        elif r["type"] == "medication_start":
            label = f"Started <b>{r['detail']}</b>"
        else:
            label = "Referred for <b>talk therapy (CBT)</b>"
        out += (f"<div class='ev'><div class='dot'>{icon.get(r['type'], '•')}</div>"
                f"<div class='d'>{pd.Timestamp(r['date']).strftime('%d %b %Y')}</div><div>{label}</div></div>")
    return out + "</div>"


# =============================================================================
# Sidebar
# =============================================================================
# Apply navigation requests made at the end of the previous run (widgets can't be
# changed once they are drawn, so we set their state here, before drawing).
if "pending_client" in st.session_state:
    st.session_state["client_select"] = st.session_state.pop("pending_client")
if "pending_page" in st.session_state:
    st.session_state["nav_page"] = st.session_state.pop("pending_page")

with st.sidebar:
    html("<div class='brand'><div class='logo'>🧠</div><div><div class='t'>Manas Twin</div>"
         "<div class='s'>Early warning for depressive episodes</div></div></div>")
    st.toggle("🌙 Dark mode", key="dark")
    st.divider()
    only_test = st.checkbox("Only clients unseen during training", value=True,
                            help="Keeps the demo honest: these synthetic clients were never used to train the model.")
    pool = TEST_IDS if only_test else A["patients"]["patient_id"].tolist()
    custom_ids = list(st.session_state.get("custom_clients", {}).keys())
    options = custom_ids + SHOW_IDS + [p for p in pool if p not in SHOW_IDS]

    def _label(p):
        if p in custom_ids:
            return f"🆕 {name_of(p)} · {p}"
        return f"⭐ {name_of(p)} · {p}" if p in SHOW_IDS else f"{name_of(p)} · {p}"
    pid = st.selectbox("Client", options, format_func=_label, key="client_select")
    tw = twin(pid)
    default_day = next((s_["suggested_day"] for s_ in SHOWCASE if s_["patient_id"] == pid), 150)
    key = f"day_{pid}"
    if key not in st.session_state:
        st.session_state[key] = default_day
    day = st.slider("Date", C.MIN_HISTORY_DAYS, tw.n_days - 1, key=key, format="day %d",
                    help="Move through time to watch the twin update.")
    html(f"<div class='muted' style='margin-top:-0.6rem'>📅 {pd.Timestamp(tw.daily.loc[day, 'date']).strftime('%A, %d %B %Y')}</div>")
    show_gt = st.checkbox("Show actual episodes", value=True,
                          help="Ground truth from the synthetic simulator, shown for evaluation. The twin never sees it.")
    st.divider()
    if st.button("🔄 New tester · reset the app", width="stretch",
                 help="Clears all selections so the next person starts fresh."):
        keep = st.session_state.get("dark", False)
        for k in list(st.session_state.keys()):
            del st.session_state[k]
        st.session_state.dark = keep
        st.rerun()
    html(f"<div class='foot' style='margin-top:0.6rem'>⚠️ Research prototype. Clients are <b>synthetic</b>. Not a diagnostic tool.<br><br>"
         f"💚 If you or someone you know is struggling: <b>{C.HELPLINE}</b></div>")

# =============================================================================
# Navigation
# =============================================================================
P_GUIDE, P_STORY, P_TWIN, P_WHATIF, P_CLIN, P_LIVE, P_PERF, P_FEEDBACK, P_ABOUT = PAGES = [
    "📘 Guide", "📖 Story", "🧠 Twin", "🔮 What-if", "🩺 Clinician", "📡 Live", "📊 Evidence", "📝 Feedback", "ℹ️ About"]
with st.container(key="nav"):
    page = st.radio("Navigate", PAGES, horizontal=True, label_visibility="collapsed", key="nav_page")
st.write("")

# =============================================================================
# 📖 Story mode
# =============================================================================
STORY_PID = "MT0441"
STORY = [
    dict(day=95, title="Meet Arjun",
         text="Arjun is 18, an engineering student in Kochi. His smartwatch and phone have been quietly feeding his "
              "<b>digital twin</b>, a living virtual copy of his daily rhythm, for three months. By now the twin has "
              "learned what <b>normal looks like for him</b>: how long he sleeps, when he goes to bed, how much he "
              "moves and how his heart behaves.", cards=True),
    dict(day=108, title="Exams begin",
         text="End-semester exams start. Arjun sleeps a bit less, stays up later and spends more time on his phone at "
              "night. On their own these changes look small, and a one-size-fits-all rule would ignore them. But the "
              "twin compares him with <b>his own normal</b>, and the clouds start gathering.", cards=True),
    dict(day=110, title="⛈️ Early warning, 7 days ahead",
         text="The twin's estimate crosses the alert line. Nothing dramatic has happened and nobody around Arjun has "
              "noticed anything. With his consent, his campus counsellor gets a gentle alert to check in and repeat a "
              "short PHQ-9 questionnaire. The panel on the right shows <b>why</b> the twin is worried.", drivers=True),
    dict(day=117, title="The episode begins",
         text="Seven days later, a depressive episode begins (the grey band, which comes from the simulator's hidden "
              "ground truth). This is exactly the window the twin was warning about."),
    dict(day=136, title="Usual care catches up, 19 days late",
         text="Without the twin, Arjun is only diagnosed on 17 May, 19 days into the episode, when he scores 16 on the "
              "PHQ-9. He starts medication and therapy. With the twin, support could have started on 21 April: "
              "<b>26 days earlier</b>."),
    dict(day=112, title="🔮 What if he'd had a better week?",
         text="The twin can also run experiments safely on the virtual Arjun. Suppose his last week had included an "
              "hour more sleep, a 45-minute earlier bedtime, 3,000 more steps a day, less late-night phone time and a "
              "few more conversations with friends. Here's how his outlook changes.", whatif=True),
]


def whatif_card(res, labels=("Actual week", "Your scenario")):
    wb, wa = WEATHER[res["band_before"]], WEATHER[res["band_after"]]
    change = (res["after"] / res["before"] - 1) * 100 if res["before"] else 0
    return f"""
<div class='card' style='text-align:center;padding:1.3rem'>
  <div style='display:flex;justify-content:space-around;align-items:center'>
    <div><div class='eyebrow'>{labels[0]}</div><div style='font-size:3.8rem'>{wb['icon']}</div>
      <div style='font-size:2.1rem;font-weight:800;color:{wb['color']}'>{100 * res['before']:.1f}%</div><div class='muted'>{wb['sky']}</div></div>
    <div style='font-size:2.2rem' class='muted'>→</div>
    <div><div class='eyebrow'>{labels[1]}</div><div style='font-size:3.8rem'>{wa['icon']}</div>
      <div style='font-size:2.1rem;font-weight:800;color:{wa['color']}'>{100 * res['after']:.1f}%</div><div class='muted'>{wa['sky']}</div></div>
  </div>
  <div style='margin-top:0.8rem;font-size:1.05rem'>Chance of an episode in the next 7 days
    <b style='color:{P['green'] if change <= 0 else P['red']}'>{'falls' if change <= 0 else 'rises'} by {abs(change):.0f}%</b></div>
</div>"""


if page == P_GUIDE:
    html("<h2 style='margin:0'>📘 Guide for psychologists and counsellors</h2>"
         "<div class='muted'>About 15 minutes: 3 to read, 10 to explore, 2 to give feedback. Thank you for testing.</div>")
    st.write("")
    c1, c2 = st.columns([1.15, 1])
    with c1:
        html("""<div class='card story'>
<div class='eyebrow' style='margin-bottom:0.4rem'>What you are looking at</div>
<b>Manas Twin</b> is a prototype <b>digital twin</b> for depression: a continuously updated model of one client's
daily rhythm (sleep, bedtime, heart-rate variability, activity, late-night phone use, social contact) joined with
their record (PHQ-9 screenings, diagnoses, medication). It learns what <b>normal looks like for that client</b> and
estimates the chance that a depressive episode <b>starts within the next 7 days</b>, shown as mind-weather:
<b>☀️ Clear skies · ⛅ Clouds gathering · ⛈️ Storm likely</b>.<br><br>
<div class='eyebrow' style='margin-bottom:0.4rem'>What it is not</div>
It does <b>not</b> diagnose, does <b>not</b> assess suicide or self-harm risk, and does <b>not</b> replace your
judgement. It is designed as a <b>prompt for a human check-in</b>. All clients in this prototype are
<b>synthetic</b> (computer-generated); no real person's data is shown.
</div>""")
        st.write("")
        html("""<div class='card'>
<div class='eyebrow' style='margin-bottom:0.5rem'>Please try these 5 tasks (≈10 min)</div>
<div class='tl'>
<div class='ev'><div class='dot'>1</div><div><b>📖 Story</b> · click <i>Next</i> through the 6 steps (3 min).
<span class='muted'>Does the sequence make clinical sense?</span></div></div>
<div class='ev'><div class='dot'>2</div><div><b>🧠 Twin</b> · client ⭐ Arjun. In the sidebar, drag the date from <b>day 100 to 125</b>.
<span class='muted'>Note the day <i>you</i> would first have been concerned, and when the twin flagged.</span></div></div>
<div class='ev'><div class='dot'>3</div><div><b>🩺 Clinician</b> · open two records from the caseload.
<span class='muted'>Do the "why" explanations and the PHQ-9 timeline read sensibly? Try <i>Enrol a demo client</i>.</span></div></div>
<div class='ev'><div class='dot'>4</div><div><b>🔮 What-if</b> · press <i>Full healthy week</i>, then move one slider yourself.
<span class='muted'>Are these realistic levers for a client? Is the caveat clear enough?</span></div></div>
<div class='ev'><div class='dot'>5</div><div><b>📊 Evidence</b> · skim the numbers, including the real-data check.
<span class='muted'>Is the performance framed honestly?</span></div></div>
</div>
<div style='margin-top:0.4rem'>Then please fill in <b>📝 Feedback</b>. Be as critical as you like: that is the point.</div>
</div>""")
    with c2:
        html(f"""<div class='card'>
<div class='eyebrow' style='margin-bottom:0.5rem'>How to read the screen</div>
<table class='mt'>
<tr><th>Element</th><th>Meaning</th></tr>
<tr><td>☀️ Clear skies</td><td>7-day episode risk below {100 * THR / 2:.1f}%. Rhythm close to the client's own normal.</td></tr>
<tr><td>⛅ Clouds gathering</td><td>Risk {100 * THR / 2:.1f}–{100 * THR:.1f}%. Some signals drifting. Light-touch check-in.</td></tr>
<tr><td>⛈️ Storm likely</td><td>Risk ≥ {100 * THR:.1f}% (about 3× the cohort base rate) <i>and</i> rising for more than one day (a single-day jump shows as Watch · rising). Contact within 48 h and a PHQ-9.</td></tr>
<tr><td>Chance of an episode</td><td>Probability that a depressive episode <i>begins</i> in the next 7 days. Not severity.</td></tr>
<tr><td>× a typical person</td><td>Relative to the cohort base rate ({100 * tw.base_rate:.1f}% per week).</td></tr>
<tr><td>Usual / Drifting / Big change</td><td>How far the last 7 days sit from the client's own 45-day baseline (≈0.75 and 1.5 SD).</td></tr>
<tr><td>HRV</td><td>Heart-rate variability (RMSSD). Lower under sustained stress.</td></tr>
<tr><td>PHQ-9 bands</td><td>0–4 minimal · 5–9 mild · 10–14 moderate · 15–19 moderately severe · 20–27 severe.</td></tr>
<tr><td>Grey band "actual episode"</td><td>Simulator ground truth, shown only to evaluate. The twin never sees it.</td></tr>
</table></div>""")
        st.write("")
        html("""<div class='card'>
<div class='eyebrow' style='margin-bottom:0.5rem'>Questions clinicians usually ask</div>
<div style='font-size:0.92rem;line-height:1.55'>
<b>Why no diagnosis?</b> Onset prediction is a screening signal; diagnosis needs a clinician and a conversation.<br>
<b>How many false alarms?</b> About one false-alarm day a month per client at the current threshold; you can see the trade-off under 📊 Evidence.<br>
<b>Who sees the data?</b> Design: the client, and with their revocable consent, their counsellor. Institutions see only aggregates.<br>
<b>What if the client has no smartwatch?</b> A phone-only mode (sleep, screen time, social contact) is on the roadmap.<br>
<b>What about crisis?</b> Out of scope by design. The app signposts Tele-MANAS 14416 and relies on the human in the loop.<br>
<b>Is this real data?</b> The clients are synthetic. The rhythm features were checked on real wrist-actigraphy from 55 people (see 📊 Evidence).
</div></div>""")
    st.write("")
    callout("Tip: use <b>🔄 New tester · reset the app</b> in the sidebar before handing over to the next person.", "info")

elif page == P_STORY:
    st.session_state.setdefault("story_step", 0)
    i = st.session_state.story_step
    stp = STORY[i]
    stw = twin(STORY_PID)
    html("<div class='steps'>" + "".join(f"<div class='s {'on' if k <= i else ''}'></div>" for k in range(len(STORY))) + "</div>")
    html(f"<div class='eyebrow'>Story · step {i + 1} of {len(STORY)} · "
         f"{pd.Timestamp(stw.daily.loc[stp['day'], 'date']).strftime('%d %B %Y')}</div>"
         f"<h2 style='margin:0.1rem 0 0.6rem'>{stp['title']}</h2>")
    left, right = st.columns([1, 1.1])
    with left:
        html(f"<div class='card story'>{stp['text']}</div>")
        st.write("")
        b1, b2, _ = st.columns([1, 1, 1.4])
        if b1.button("← Back", disabled=i == 0, width="stretch"):
            st.session_state.story_step -= 1
            st.rerun()
        if i < len(STORY) - 1:
            if b2.button("Next →", type="primary", width="stretch"):
                st.session_state.story_step += 1
                st.rerun()
        elif b2.button("↺ Restart", type="primary", width="stretch"):
            st.session_state.story_step = 0
            st.rerun()
    with right:
        if stp.get("whatif"):
            res = stw.what_if(stp["day"], sleep_hours=1, sleep_onset_shift_h=-0.75, steps=3000,
                              night_screen_min=-45, social_contacts=5)
            html(whatif_card(res, ("His actual week", "With a better week")))
            st.write("")
            callout("A model-based experiment: it shows how the twin's estimate responds, not a guaranteed effect. "
                    "Try your own changes in the <b>🔮 What-if</b> tab.", "info")
        else:
            hero(stw, stp["day"], compact=True)
    st.write("")
    if stp.get("drivers"):
        c1, c2 = st.columns([1.4, 1])
        show_chart(risk_chart(stw, stp["day"], 60, 140, 300), key=f"story_chart_{i}", target=c1)
        html("<div class='card'><div class='eyebrow' style='margin-bottom:0.4rem'>Why the twin is worried</div>"
             + drivers_html(stw.explain(stp["day"]), tw=stw, day=stp["day"]) + "</div>", c2)
    elif not stp.get("whatif"):
        show_chart(risk_chart(stw, stp["day"], 60, 140, 300), key=f"story_chart_{i}")
    if stp.get("cards"):
        st.write("")
        html("<div class='eyebrow' style='margin-bottom:0.4rem'>Arjun's body rhythm · last 30 days · shaded band = his normal range</div>")
        signal_cards(stw, stp["day"])

# =============================================================================
# 🧠 Twin
# =============================================================================
elif page == P_TWIN:
    p = patient_row(pid)
    html(f"<div class='eyebrow'>{p['cohort'].title()} · {p['age']} · {p['city']} · prior episodes: {p['prior_episodes']}"
         f" · family history: {'yes' if p['family_history_depression'] else 'no'}"
         f"{' · 📚 exam / work-crunch period' if tw.state(day)['stressor'] else ''}</div>")
    st.write("")
    hero(tw, day)
    st.write("")
    c1, c2 = st.columns([1.55, 1])
    with c1:
        html("<div class='eyebrow'>How the outlook has changed</div>")
        show_chart(risk_chart(tw, day, gt=show_gt), key="twin_chart")
    html("<div class='card'><div class='eyebrow' style='margin-bottom:0.4rem'>What's pushing the risk up</div>"
         + drivers_html(tw.explain(day), tw=tw, day=day) + "<div class='foot' style='margin-top:0.5rem'>Longer bar = stronger push "
         "on the estimate (SHAP).</div></div>", c2)
    st.write("")
    html(f"<div class='eyebrow' style='margin-bottom:0.4rem'>{name_of(pid)}'s body rhythm · last 30 days · "
         "shaded band = normal range</div>")
    signal_cards(tw, day)

# =============================================================================
# 🔮 What-if
# =============================================================================
elif page == P_WHATIF:
    nm = name_of(pid)
    WI = dict(wi_sleep=0.0, wi_bed=0.0, wi_steps=0, wi_screen=0, wi_social=0)
    for k, v in WI.items():
        st.session_state.setdefault(k, v)

    def preset(**kv):
        for k, v in WI.items():
            st.session_state[k] = kv.get(k, v)

    html(f"<h3 style='margin:0'>🔮 Try a different week for {nm}</h3>"
         f"<div class='muted'>Change {nm}'s last 7 days and watch the twin re-run. Date: "
         f"{pd.Timestamp(tw.daily.loc[day, 'date']).strftime('%d %b %Y')} (change it in the sidebar).</div>")
    st.write("")
    b = st.columns(4)
    b[0].button("😴 Sleep more", on_click=preset, kwargs=dict(wi_sleep=1.0, wi_bed=-0.75), width="stretch")
    b[1].button("🚶 Move more", on_click=preset, kwargs=dict(wi_steps=3000), width="stretch")
    b[2].button("🌿 Full healthy week", on_click=preset, type="primary",
                kwargs=dict(wi_sleep=1.0, wi_bed=-0.75, wi_steps=3000, wi_screen=-45, wi_social=5), width="stretch")
    b[3].button("↺ Reset", on_click=preset, width="stretch")
    st.write("")
    c1, c2 = st.columns([1, 1.15])
    with c1:
        with st.container(border=True):
            st.slider("😴 Sleep per night (hours)", -2.0, 2.0, step=0.25, key="wi_sleep")
            st.slider("🌙 Bedtime (hours, minus = earlier)", -2.0, 2.0, step=0.25, key="wi_bed")
            st.slider("🚶 Steps per day", -4000, 6000, step=500, key="wi_steps")
            st.slider("📱 Late-night phone (minutes)", -120, 120, step=5, key="wi_screen")
            st.slider("💬 Social contacts per day", -15, 15, step=1, key="wi_social")
    res = tw.what_if(day, sleep_hours=st.session_state.wi_sleep, sleep_onset_shift_h=st.session_state.wi_bed,
                     steps=st.session_state.wi_steps, night_screen_min=st.session_state.wi_screen,
                     social_contacts=st.session_state.wi_social)
    with c2:
        html(whatif_card(res))
        st.write("")
        html("<div class='card'><div class='eyebrow' style='margin-bottom:0.4rem'>What would still push risk up</div>"
             + drivers_html(res["drivers_after"], 4, tw=tw, day=day, feats=res["feats_after"]) + "</div>")
    st.write("")
    callout("This is a <b>model-based experiment</b> on the twin: it shows how the estimate responds if these signals "
            "had looked different. It is not a guaranteed causal effect, and it is meant to support a conversation "
            "with a counsellor, not replace one.", "warn")

# =============================================================================
# 🩺 Clinician
# =============================================================================
elif page == P_CLIN:
    date_txt = pd.Timestamp(tw.daily.loc[day, "date"]).strftime("%d %b %Y")
    r = A["risk"][A["risk"].day == day].merge(A["patients"][["patient_id", "cohort", "age", "sex", "city"]], on="patient_id")
    r = r[r.patient_id.isin(pool)].copy()
    for cid, c in st.session_state.get("custom_clients", {}).items():
        ct = c["twin"]
        f = ct.feats.loc[ct.feats.day == day].iloc[0]
        r = pd.concat([r, pd.DataFrame([dict(patient_id=cid, day=day, risk=f["risk"], twin_deviation_index=f["twin_deviation_index"],
                                            cohort=ct.patient["cohort"], age=ct.patient["age"], sex=ct.patient["sex"],
                                            city=ct.patient["city"])])], ignore_index=True)
    r = r.dropna(subset=["risk"])
    prev = A["risk"][A["risk"].day == day - 1][["patient_id", "risk"]].rename(columns={"risk": "prev"})
    r = r.merge(prev, on="patient_id", how="left")
    for cid, c in st.session_state.get("custom_clients", {}).items():
        r.loc[r.patient_id == cid, "prev"] = c["twin"].prev_risk(day)
    enc = A["enc"]
    phq = enc[(enc.day <= day) & enc.phq9.notna()].sort_values("day").groupby("patient_id").agg(last_phq9=("phq9", "last"))
    r = r.merge(phq, on="patient_id", how="left")
    r["band"] = [tw.band(a, b) for a, b in zip(r.risk, r.prev)]
    html(f"<h3 style='margin:0'>🩺 Counsellor caseload · {date_txt}</h3><div class='muted'>Everyone the service supports, "
         "sorted by how stormy their mind-weather looks today. Change the date in the sidebar.</div>")
    with st.expander("➕ Enrol a demo client (synthetic) and watch the twin learn them"):
        html("<div class='muted' style='margin-bottom:0.4rem'>Choose a profile. A synthetic client with 240 days of wearable "
             "data and a health record is generated, and their twin is built on the spot.</div>")
        e1, e2, e3, e4 = st.columns(4)
        nm_new = e1.text_input("Display name", value="Meera")
        coh = e2.selectbox("Profile", ["student", "professional"])
        age_new = e3.number_input("Age", 18, 40, 24)
        sex_new = e4.selectbox("Sex", ["F", "M"])
        e1, e2, e3, e4 = st.columns(4)
        city_new = e1.selectbox("City", C.CITIES)
        prior_new = e2.number_input("Prior episodes", 0, 5, 1)
        fam_new = e3.checkbox("Family history of depression", value=False)
        vul_new = e4.slider("Underlying vulnerability", 0.0, 1.0, 0.45, 0.05,
                            help="Simulator parameter: how easily stress tips this person into an episode.")
        if st.button("Enrol client and build twin", type="primary"):
            cc = st.session_state.setdefault("custom_clients", {})
            new_id = f"NEW{len(cc) + 1:04d}"
            pr, dd, ee = simulate_custom(new_id, seed=int(time.time()) % 100000, cohort=coh, age=int(age_new), sex=sex_new,
                                         city=city_new, prior_episodes=int(prior_new), family_history_depression=bool(fam_new),
                                         vulnerability=float(vul_new))
            cc[new_id] = {"twin": DigitalTwin(new_id, assets(), frames=dict(patient=pr, daily=dd, enc=ee)),
                          "name": (nm_new.strip() or "New client")}
            st.session_state[f"day_{new_id}"] = 150
            st.session_state["pending_client"] = new_id
            st.session_state["pending_page"] = P_TWIN
            st.rerun()
    st.write("")
    k = st.columns(4)
    for col, (lab, val, colr) in zip(k, [("People supported", len(r), P["teal"]),
                                         ("⛈️ Early warning", int((r.band == "Early warning").sum()), P["red"]),
                                         ("⛅ Watch", int((r.band == "Watch").sum()), P["amber"]),
                                         ("☀️ Clear", int((r.band == "Stable").sum()), P["green"])]):
        html(f"<div class='card kpi'><div class='l'>{lab}</div><div class='v' style='--c:{colr}'>{val}</div></div>", col)
    st.write("")
    top = r.sort_values("risk", ascending=False).head(12)
    rows = ""
    for t in top.itertuples():
        w = WEATHER[t.band]
        phq_txt = "–" if pd.isna(t.last_phq9) else f"{t.last_phq9:.0f}"
        rows += (f"<tr><td><b>{name_of(t.patient_id)}</b> <span class='muted'>{t.patient_id}</span></td>"
                 f"<td><span class='pill' style='background:{w['tint']};color:{w['color']}'>{w['icon']} {t.band}</span></td>"
                 f"<td><b>{100 * t.risk:.1f}%</b></td><td>{t.twin_deviation_index:+.2f}</td><td>{phq_txt}</td>"
                 f"<td>{t.cohort.title()}, {t.age} · {t.city}</td></tr>")
    c1, c2 = st.columns([1.5, 1])
    html(f"<div class='card'><table class='mt'><tr><th>Person</th><th>Status</th><th>7-day risk</th><th>Drift</th>"
         f"<th>Last PHQ-9</th><th>Profile</th></tr>{rows}</table>"
         f"<div class='foot' style='margin-top:0.5rem'>Top 12 of {len(r)} shown. Drift = how far the last week is from the "
         "person's own normal (0 = usual).</div></div>", c1)
    with c2:
        ids = top.patient_id.tolist()
        rec = st.selectbox("Open a health record", ids, index=ids.index(pid) if pid in ids else 0,
                           format_func=lambda x: f"{name_of(x)} · {x}")
        rtw = twin(rec)
        rs_ = rtw.state(day)
        w = WEATHER[rs_["band"]]
        html(f"<div class='card'><div style='display:flex;gap:0.8rem;align-items:center'><div style='font-size:2.4rem'>{w['icon']}</div>"
             f"<div><div style='font-weight:800;font-size:1.15rem'>{name_of(rec)}</div><div class='muted'>{w['sky']} · "
             f"{100 * rs_['risk']:.1f}% risk</div></div></div><div class='muted' style='margin:0.6rem 0 0.2rem'>{summary_sentence(rtw, day)}</div>"
             f"<hr style='margin:0.7rem 0'>{ehr_timeline(rtw, day)}</div>")
        st.write("")
        bundle = build_bundle(rec, day, A["patients"], A["daily"], A["enc"])
        with st.expander(f"🔗 FHIR record ({len(bundle['entry'])} resources) for ABDM-style exchange"):
            st.download_button("⬇ Download FHIR JSON", json.dumps(bundle, indent=2), file_name=f"{rec}_day{day}_fhir.json")
            st.code(json.dumps(bundle, indent=2)[:3000] + "\n...", language="json")

# =============================================================================
# 📡 Live
# =============================================================================
elif page == P_LIVE:
    nm = name_of(pid)
    html(f"<h3 style='margin:0'>📡 Live feed · {nm}</h3><div class='muted'>Replays the watch and phone data day by day, "
         "as if it were arriving now. The twin re-learns and re-scores every day.</div>")
    st.write("")
    c1, c2, c3 = st.columns(3)
    start = c1.number_input("Start at day", C.MIN_HISTORY_DAYS, tw.n_days - 2, max(C.MIN_HISTORY_DAYS, day - 15))
    n = c2.slider("Days to replay", 5, 40, 20)
    speed = c3.select_slider("Speed", ["slow", "normal", "fast"], value="normal")
    delay = {"slow": 0.8, "normal": 0.35, "fast": 0.12}[speed]
    go_btn = st.button("▶ Start live replay", type="primary")
    hero_ph, tick_ph, chart_ph = st.empty(), st.empty(), st.empty()
    lo = max(C.MIN_HISTORY_DAYS, int(start) - 20)
    if not go_btn:
        hero(tw, int(start), hero_ph)
        show_chart(risk_chart(tw, int(start), lo, int(start) + n, 300, show_gt), key="live_idle", target=chart_ph)
    else:
        for t in range(int(start), min(int(start) + n, tw.n_days)):
            d = tw.daily.loc[t]
            hero(tw, t, hero_ph)
            items = [("😴", "Sleep", fmt_val("sleep_hours", d.sleep_hours)), ("🌙", "Bedtime", fmt_val("sleep_onset", d.sleep_onset)),
                     ("💓", "HRV", fmt_val("hrv_rmssd", d.hrv_rmssd)), ("🚶", "Steps", fmt_val("steps", d.steps)),
                     ("📱", "Night phone", fmt_val("night_screen_min", d.night_screen_min))]
            html("<div style='display:flex;gap:0.6rem;flex-wrap:wrap;margin:0.8rem 0'>" + "".join(
                f"<div class='card' style='flex:1;min-width:120px;padding:0.6rem 0.8rem'><div class='muted' style='font-size:0.8rem'>"
                f"{i} {lab} today</div><div style='font-weight:800;font-size:1.25rem'>{v}</div></div>" for i, lab, v in items)
                + "</div>", tick_ph)
            show_chart(risk_chart(tw, t, lo, int(start) + n, 300, show_gt), key=f"live_{t}", target=chart_ph)
            time.sleep(delay)
        callout("Replay finished. Move the sidebar date to explore any day.", "info")

# =============================================================================
# 📊 Performance
# =============================================================================
elif page == P_PERF:
    m = json.loads((C.REPORT_DIR / "metrics.json").read_text())
    t, p = m["twin"], m["population"]
    html("<h3 style='margin:0'>📊 Does it work? Part 1: the synthetic cohort</h3><div class='muted'>Tested on 180 synthetic people the model never saw "
         "during training, against a one-size-fits-all model that ignores each person's own normal.</div>")
    st.write("")
    k = st.columns(4)
    kp = [(f"{t['episodes_detected']} of {t['episodes_evaluated']}", "episodes flagged before they began",
           f"one-size-fits-all: {p['episodes_detected']} of {p['episodes_evaluated']}"),
          (f"{t['median_lead_time_days']:.0f} days", "typical warning before onset", "time for a counsellor to act"),
          (f"{t['false_alert_days_per_30_quiet_days']:.1f}", "false-alarm days per month",
           f"one-size-fits-all: {p['false_alert_days_per_30_quiet_days']:.1f}"),
          (f"{t['auroc']:.2f}", "AUROC (0.5 = coin flip, 1 = perfect)", f"one-size-fits-all: {p['auroc']:.2f}")]
    for col, (v, lab, c) in zip(k, kp):
        html(f"<div class='card kpi'><div class='v'>{v}</div><div class='l'>{lab}</div><div class='c'>{c}</div></div>", col)
    st.write("")
    c1, c2 = st.columns(2)
    comp = [("Episodes flagged early (%)", 100 * t["episode_detection_rate"], 100 * p["episode_detection_rate"], "{:.0f}%"),
            ("False-alarm days / month ×10", 10 * t["false_alert_days_per_30_quiet_days"], 10 * p["false_alert_days_per_30_quiet_days"], "{:.0f}"),
            ("AUROC ×100", 100 * t["auroc"], 100 * p["auroc"], "{:.0f}")]
    fig = go.Figure()
    fig.add_trace(go.Bar(name="Manas Twin (personal normal)", y=[c[0] for c in comp], x=[c[1] for c in comp], orientation="h",
                         marker_color=P["teal"], text=[c[3].format(c[1]) for c in comp], textposition="outside"))
    fig.add_trace(go.Bar(name="One-size-fits-all", y=[c[0] for c in comp], x=[c[2] for c in comp], orientation="h",
                         marker_color=P["muted"], text=[c[3].format(c[2]) for c in comp], textposition="outside"))
    fig.update_layout(barmode="group", legend=dict(orientation="h", y=-0.12), bargap=0.35)
    fig.update_xaxes(visible=False, range=[0, 105])
    fig.update_yaxes(autorange="reversed")
    html("<div class='eyebrow'>Personal normal vs. one-size-fits-all</div>", c1)
    show_chart(style_fig(fig, 330, legend=True), key="perf_cmp", target=c1)
    imp = pd.read_csv(C.REPORT_DIR / "shap_global_importance.csv", index_col=0)["mean_abs_shap"].head(10)[::-1]
    fig2 = go.Figure(go.Bar(x=imp.values, y=[readable(f) for f in imp.index], orientation="h", marker_color=P["teal"]))
    fig2.update_xaxes(title="average influence (mean |SHAP|)")
    html("<div class='eyebrow'>What the twin pays most attention to</div>", c2)
    show_chart(style_fig(fig2, 330), key="perf_shap", target=c2)
    st.write("")
    callout("<b>Reading this honestly:</b> about half of episodes are flagged in advance, typically 6 days ahead, with "
            "roughly one false-alarm day a month. That makes the twin a <b>prompt for a human check-in</b>, not a "
            f"diagnosis. All results come from a synthetic cohort ({m['data']['patients']} people × "
            f"{m['data']['days_per_patient']} days); see the real-data check below.", "warn")
    st.write("")
    html("<h3 style='margin:0'>🧪 Real-data check: DEPRESJON wrist-actigraphy</h3><div class='muted'>Public dataset "
         "(Garcia-Ceja et al., 2018): minute-level wrist activity from 23 people with depression (MADRS-scored) and 32 "
         "controls, about 13 days each. No health record and no episode onsets, so it cannot train the full twin, but it "
         "can test whether the twin's rhythm features carry real signal.</div>")
    st.write("")
    dv_path = C.REPORT_DIR / "depresjon_validation.json"
    if dv_path.exists():
        dv = json.loads(dv_path.read_text())
        q1 = dv["q1_person_level"]
        k = st.columns(4)
        kp2 = [(f"{q1['auroc_lopo']:.2f}", "AUROC: depressed vs control", f"95% CI {q1['ci95'][0]:.2f}–{q1['ci95'][1]:.2f}, leave-one-person-out"),
               (f"{100 * q1['sensitivity_at_spec80']:.0f}%", "of depressed people identified", "at 80% specificity"),
               (f"{dv['people']}", "real people", f"{dv['depressed']} depressed · {dv['people'] - dv['depressed']} controls"),
               (f"{dv['complete_days']:,}", "complete days of actigraphy", f"median {dv['days_per_person_median']:.0f} days per person")]
        for col, (v, lab, c) in zip(k, kp2):
            html(f"<div class='card kpi'><div class='v'>{v}</div><div class='l'>{lab}</div><div class='c'>{c}</div></div>", col)
        st.write("")
        c1, c2 = st.columns([1.1, 1])
        uni = dv["q1_univariate"]
        rows = ""
        for f, lab in [("mean_activity", "Mean daily activity"), ("rest_minutes", "Minutes at rest per day"),
                       ("day_to_day_var", "Day-to-day variability"), ("night_share", "Night-time activity share"),
                       ("rel_amplitude", "Day–night contrast"), ("intradaily_var", "Fragmentation of rhythm")]:
            u = uni[f]
            sig = "✅" if u["p_value"] < 0.05 else ("◽" if u["p_value"] < 0.1 else "")
            rows += (f"<tr><td>{lab}</td><td>{u['depressed_median']:.3g}</td><td>{u['control_median']:.3g}</td>"
                     f"<td>{u['p_value']:.3f} {sig}</td></tr>")
        html(f"<div class='card'><div class='eyebrow' style='margin-bottom:0.4rem'>Rhythm features by group (medians)</div>"
             f"<table class='mt'><tr><th>Feature</th><th>Depressed</th><th>Control</th><th>p (Mann-Whitney)</th></tr>{rows}</table>"
             "<div class='foot' style='margin-top:0.5rem'>✅ p &lt; 0.05. People with depression moved less, rested more and "
             "varied less from day to day, in line with the digital-phenotyping literature.</div></div>", c1)
        ex = dv["examples"]
        fig3 = go.Figure()
        for pid_, colr, lab in [("control_3", P["green"], "Control (real person)"), ("condition_2", P["red"], "Depressed (real person)")]:
            e = ex[pid_]
            fig3.add_trace(go.Scatter(x=list(range(1, len(e["mean_activity"]) + 1)), y=e["mean_activity"], mode="lines+markers",
                                      name=lab, line=dict(color=colr, width=2.5)))
        fig3.update_xaxes(title="day of recording")
        fig3.update_yaxes(title="mean activity count")
        fig3.update_layout(legend=dict(orientation="h", y=-0.25))
        html("<div class='eyebrow'>Two real people, two weeks of wrist activity</div>", c2)
        show_chart(style_fig(fig3, 330, legend=True), key="dep_examples", target=c2)
        st.write("")
        callout("<b>Honest reading:</b> real wearable data carries a clear between-person depression signal, which supports the "
                "features the twin is built on. What DEPRESJON cannot test is the <i>within-person</i> early-warning step "
                "(no episode onsets, ~13 days per person), and symptom-severity correlations were not significant with 23 "
                "people. That is exactly what the planned longitudinal pilot is for.", "info")
    else:
        callout("Run <code>python -m src.validate_depresjon</code> after downloading DEPRESJON to generate this section.", "warn")

# =============================================================================
# ℹ️ About
# =============================================================================
elif page == P_FEEDBACK:
    html("<h2 style='margin:0'>📝 Your feedback</h2><div class='muted'>About 2 minutes. Responses are saved locally for the "
         "research team; no client data is stored with them. Critical feedback is the most useful kind.</div>")
    st.write("")
    if st.session_state.get("fb_done"):
        sync = st.session_state.get("fb_sync", "off")
        note = {"synced": " It has also been synced to the research team's sheet.",
                "off": ""}.get(sync, " (Saved on this device; the cloud sync did not go through, which is fine.)")
        callout(f"✅ Thank you, your feedback has been saved.{note} You can press <b>🔄 New tester</b> in the sidebar to "
                "hand over to the next person.", "info")
    else:
        with st.form("feedback_form", clear_on_submit=False):
            c1, c2, c3 = st.columns(3)
            name = c1.text_input("Name (optional)")
            role = c2.selectbox("Your role", ["Clinical psychologist", "Counselling psychologist", "Psychiatrist",
                                              "Counsellor / therapist", "Psychology student / trainee", "Other"])
            years = c3.selectbox("Years of practice", ["0–2", "3–5", "6–10", "11–20", "20+"])
            c1, c2 = st.columns(2)
            setting = c1.multiselect("Where you mainly work", ["Private practice", "Hospital / clinic", "College / campus wellness",
                                                              "Corporate / EAP", "NGO / helpline", "Academia / research", "Other"])
            wear = c2.selectbox("How familiar are you with wearable / digital-phenotyping data?",
                                ["Not at all", "A little", "Moderately", "Very"])
            html("<div class='eyebrow' style='margin:0.8rem 0 0.2rem'>Please rate each statement (1 = strongly disagree · 5 = strongly agree)</div>")
            ratings = {}
            for k, text in FB.STATEMENTS:
                ratings[k] = st.radio(text, [1, 2, 3, 4, 5], horizontal=True, index=None, key=f"fb_{k}")
            would = st.radio("Would you use a tool like this with clients, once validated on real data?",
                             ["Yes", "Maybe", "No"], horizontal=True, index=None)
            html("<div class='eyebrow' style='margin:0.8rem 0 0.2rem'>In your own words</div>")
            opens = {k: st.text_area(q, height=80) for k, q in FB.OPEN_QUESTIONS}
            c1, c2 = st.columns([1, 2])
            contact = c1.checkbox("You may contact me about a follow-up")
            email = c2.text_input("Email (only if you ticked the box)")
            submitted = st.form_submit_button("Submit feedback", type="primary")
        if submitted:
            missing = [t for k, t in FB.STATEMENTS if ratings[k] is None]
            if missing or would is None:
                callout("Please rate every statement (and answer 'would you use') before submitting.", "warn")
            else:
                st.session_state.setdefault("tester_id", hashlib.md5(f"{time.time()}".encode()).hexdigest()[:8])
                _, sync = FB.save(dict(tester_id=st.session_state.tester_id, name=name, role=role, years_experience=years,
                                       setting="; ".join(setting), wearable_familiarity=wear, would_use=would, **ratings,
                                       **opens, contact_ok=contact, email=email))
                st.session_state.fb_done = True
                st.session_state.fb_sync = sync
                st.rerun()
    st.write("")
    with st.expander("🔐 Organiser tools"):
        code = st.text_input("Organiser passcode", type="password")
        if code == FB.admin_code():
            html(f"Google Sheets sync: <b>{'on' if FB.sync_enabled() else 'off (local CSV only)'}</b>")
            df = FB.load_all()
            html(f"<b>{len(df)}</b> responses so far.")
            if len(df):
                means = df[[k for k, _ in FB.STATEMENTS]].apply(pd.to_numeric, errors="coerce").mean().round(2)
                fig = go.Figure(go.Bar(x=means.values, y=[t[:60] + ("…" if len(t) > 60 else "") for _, t in FB.STATEMENTS],
                                       orientation="h", marker_color=P["teal"]))
                fig.update_xaxes(range=[1, 5], title="mean rating (1–5)")
                fig.update_yaxes(autorange="reversed")
                show_chart(style_fig(fig, 380), key="fb_summary")
                st.download_button("⬇ Download all responses (CSV)", df.to_csv(index=False), "manas_twin_feedback.csv")
        elif code:
            callout("Wrong passcode.", "warn")

elif page == P_ABOUT:
    html("<h3 style='margin:0'>ℹ️ What is Manas Twin?</h3><div class='muted'>Manas (मनस्) means mind.</div>")
    st.write("")
    html("<div class='card story'>A <b>digital twin</b> is a living virtual copy of something real that stays in sync "
         "with it. Manas Twin is a virtual copy of one person's daily rhythm (sleep, heart, movement, phone use and "
         "social contact), paired with their health record. Like a weather forecast for the mind, it notices when the "
         "person drifts away from <b>their own normal</b> and warns about a week before a depressive episode is likely "
         "to begin, while there's still time to help.</div>")
    st.write("")
    steps = [("🌱", "Learn", "Learns your normal from 60+ days of watch and phone data."),
             ("🪞", "Mirror", "Compares your last week with your own normal, every day."),
             ("🔭", "Predict", "Estimates the chance an episode starts in the next 7 days."),
             ("💡", "Explain", "Shows the reasons in plain language."),
             ("🔮", "Simulate", "Lets you test what a better week would change.")]
    for c, (i, h, d) in zip(st.columns(5), steps):
        html(f"<div class='card' style='text-align:center;min-height:175px'><div style='font-size:2.2rem'>{i}</div>"
             f"<div style='font-weight:800;margin:0.2rem 0'>{h}</div><div class='muted' style='font-size:0.88rem'>{d}</div></div>", c)
    st.write("")
    html("<div class='eyebrow' style='margin-bottom:0.4rem'>Built to be safe</div>")
    guard = [("🔐", "Consent first", "Explicit, revocable consent in line with India's DPDP Act 2023 and ABDM."),
             ("🤝", "Human in the loop", "The twin alerts. A counsellor or clinician decides. It never diagnoses."),
             ("🚫", "Narrow scope", "Predicts depressive-episode onset only. It does not assess suicide or self-harm risk."),
             ("🕵️", "Privacy", "Pseudonymous IDs. Counts, never message content. Aggregate-only views for institutions.")]
    for c, (i, h, d) in zip(st.columns(4), guard):
        html(f"<div class='card' style='min-height:175px'><div style='font-size:1.6rem'>{i}</div><div style='font-weight:800;margin:0.2rem 0'>{h}</div>"
             f"<div class='muted' style='font-size:0.88rem'>{d}</div></div>", c)
    st.write("")
    callout(f"💚 If you are in distress or thinking about harming yourself, please reach out now: <b>{C.HELPLINE}</b>, "
            "or go to the nearest emergency department.", "danger")

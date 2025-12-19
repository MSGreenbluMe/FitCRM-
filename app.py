"""
FIT CRM - Streamlit Application with Dashboard
Webove rozhranie pre fitness trenerov
"""
import streamlit as st
import sys
import os
import json
import requests
from pathlib import Path
from datetime import datetime, timedelta
import tempfile
import plotly.express as px
import plotly.graph_objects as go
import random
import pandas as pd
import html
import base64
import hashlib
import subprocess

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

from src.email_parser import EmailParser, ClientProfile
from src.ai_generator import FitAIGenerator, ClientSegment
from src.pdf_generator import PDFGenerator
from src.mock_data import get_mock_clients, get_dashboard_stats, ClientData
from src import __version__ as APP_VERSION
from src.email_connector import ImapAccount, test_imap_connection, fetch_imap_messages

# Demo email data for simulated feed
DEMO_EMAILS = [
    {
        "id": "ticket_001",
        "subject": "Nový klient: Ján Novák",
        "from": "jan.novak@example.com",
        "time": "pred 5 min",
        "priority": "high",
        "status": "new",
        "content": """Novy klient z weboveho formulara:

Meno: Jan Novak
Email: jan.novak@example.com
Vek: 32
Pohlavie: muz
Vaha: 92 kg
Vyska: 178 cm
Ciel: Chcem schudnut 10-15 kg a zlepsit celkovu kondíciu. Uz dlhsie sa necitim dobre vo vlastnom tele.
Aktivita: Sedave zamestnanie v kancelarii, celý den za počítačom
Skusenosti: zaciatocnik - nikdy som pravidelne necvicil
Obmedzenia: ziadne potravinove alergie
Zdravotne problemy: obcasne bolesti chrbta od sedenia
Motivacia: Chcem sa citit lepsie, mat viac energie a byt zdravsi pre svoju rodinu.

Poznamky: Nemam vela casu, pracujem 8-17. Viem cvicit max 3x do tyzdna. Mam pristup do fitness centra."""
    },
    {
        "id": "ticket_002",
        "subject": "Nový klient: Peter Horváth",
        "from": "peter.horvath@example.com",
        "time": "pred 15 min",
        "priority": "normal",
        "status": "new",
        "content": """Novy klient z weboveho formulara:

Meno: Peter Horvath
Email: peter.horvath@example.com
Vek: 25
Pohlavie: muz
Vaha: 72 kg
Vyska: 182 cm
Ciel: Chcem nabrat svalovu hmotu a zvysit silu. Chcem vyzerat atleticky.
Aktivita: Aktivna - 2x tyzdenne futbal, plus chcem zacat posilnovnu
Skusenosti: mierne pokrocily - cvicil som rok dozadu, teraz chcem zacat znova
Obmedzenia: ziadne
Zdravotne problemy: ziadne
Motivacia: Chcem vyzerat dobre na plazi a mat silu na sporty.

Poznamky: Mam cas cvicit aj 4-5x tyzdenne. Preferujem klasicke posilovne cviky. Mam doma cinky 2x15kg a hrazdu."""
    },
    {
        "id": "ticket_003",
        "subject": "Nová klientka: Lucia Kováčová",
        "from": "lucia.kovacova@example.com",
        "time": "pred 1 hod",
        "priority": "normal",
        "status": "new",
        "content": """Novy klient z weboveho formulara:

Meno: Lucia Kovacova
Email: lucia.kovacova@example.com
Vek: 28
Pohlavie: zena
Vaha: 65 kg
Vyska: 168 cm
Ciel: Chcem spevnit postavu, hlavne brucho a zadok. Nechcem schudnut, skor tvarovat telo.
Aktivita: Mierna aktivita - chodim do prace pesie (30 min denne), obcas jogging
Skusenosti: zaciatocnicka v posilovni, ale chodim na jogu 2 roky
Obmedzenia: Laktozova intolerancia - nesmiem mliecne vyrobky
Zdravotne problemy: ziadne
Motivacia: Chcem sa citit silnejsia a sebavedomejsia. Rada by som nosila veci, co sa mi predtym nehodili.

Poznamky: Preferujem cvicenie s vlastnou vahou alebo s malymi cinkami. Nemam rada cardio na strojoch. Mam rada skupinove cvicenia."""
    },
    {
        "id": "ticket_004",
        "subject": "Demo klient: Test",
        "from": "test@example.com",
        "time": "pred 2 hod",
        "priority": "low",
        "status": "new",
        "content": """Novy klient z weboveho formulara:

Meno: Test Demo
Email: test@example.com
Vek: 30
Pohlavie: muz
Vaha: 80 kg
Vyska: 180 cm
Ciel: Chcem schudnut a zlepsit kondiciu
Aktivita: sedave zamestnanie (kancelaria)
Skusenosti: zaciatocnik
Obmedzenia: ziadne
Motivacia: Chcem sa citit lepsie a byt fit."""
    }
]


@st.cache_data(show_spinner=False)
def _git_sha_short() -> str:
    try:
        cwd = str(Path(__file__).parent)
        out = subprocess.check_output(["git", "rev-parse", "--short", "HEAD"], cwd=cwd, stderr=subprocess.DEVNULL)
        return out.decode("utf-8").strip()
    except Exception:
        return ""

# Page config
st.set_page_config(
    page_title="FIT CRM",
    page_icon="💪",
    layout="wide",
    initial_sidebar_state="collapsed"
)

def get_theme_css(dark_mode: bool) -> str:
    """Generate CSS based on theme mode"""
    if dark_mode:
        return """
        :root {
            --app-bg: #102216;
            --surface-1: #23482f;
            --surface-2: #1a3824;
            --surface-3: #2a5538;
            --shell-bg: #102216;
            --border: #23482f;
            --text: #e7f3eb;
            --muted: #92c9a4;
            --accent: #13ec5b;
            --accent-2: rgba(19, 236, 91, 0.16);
        }
        .stApp { background: var(--app-bg) !important; color: var(--text) !important; }
        .stMarkdown, .stMarkdown p { color: var(--text) !important; }
        h1, h2, h3, h4, h5, h6 { color: var(--text) !important; }
        [data-testid="stMetricValue"] { color: var(--text) !important; }
        [data-testid="stMetricLabel"] { color: var(--muted) !important; }
        .bento-card { background: var(--surface-1) !important; border-color: var(--border) !important; }
        .bento-card:hover { border-color: rgba(19, 236, 91, 0.55) !important; }
        .ticket-card { background: var(--surface-1) !important; border-color: var(--border) !important; }
        .ticket-card:hover { background: var(--surface-2) !important; }
        .ticket-card .ticket-subject { color: var(--text) !important; }
        .ticket-card .ticket-meta { color: var(--muted) !important; }
        .inbox-detail-body { background: var(--app-bg) !important; border-color: var(--border) !important; color: var(--text) !important; }
        .chip { border-color: var(--border) !important; }
        .chip.new, .chip.active { background: rgba(19, 236, 91, 0.14) !important; color: var(--accent) !important; }
        .chip.assigned, .chip.stagnating { background: rgba(245, 158, 11, 0.14) !important; color: #fbbf24 !important; }
        .chip.done { background: rgba(148, 163, 184, 0.14) !important; color: #cbd5e1 !important; }
        .chip.problem { background: rgba(239, 68, 68, 0.14) !important; color: #f87171 !important; }
        .stTextInput input, .stTextArea textarea { background: var(--surface-1) !important; border-color: var(--border) !important; color: var(--text) !important; }
        .stSelectbox > div > div { background: var(--surface-1) !important; border-color: var(--border) !important; }
        .stTabs [data-baseweb="tab-list"] { background: var(--surface-1) !important; }
        .stTabs [data-baseweb="tab"] { color: var(--muted) !important; }
        .stTabs [aria-selected="true"] { background: var(--surface-2) !important; color: var(--text) !important; }
        """
    return """
        :root {
            --app-bg: #f7fbf8;
            --surface-1: #ffffff;
            --surface-2: #f0f7f2;
            --shell-bg: #ffffff;
            --border: #d9eadf;
            --text: #0f172a;
            --muted: #456a55;
            --accent: #0fb54a;
            --accent-2: rgba(15, 181, 74, 0.12);
        }
        .stApp { background: var(--app-bg) !important; color: var(--text) !important; }
        .stMarkdown, .stMarkdown p { color: var(--text) !important; }
        h1, h2, h3, h4, h5, h6 { color: var(--text) !important; }
        [data-testid="stMetricValue"] { color: var(--text) !important; }
        [data-testid="stMetricLabel"] { color: var(--muted) !important; }
    """

# Custom CSS - Clean Professional Design
st.markdown("""
<style>
    /* ===== CLEAN PROFESSIONAL FOUNDATION ===== */
    @import url('https://fonts.googleapis.com/css2?family=Manrope:wght@400;500;600;700;800&display=swap');

    /* Hide Streamlit branding */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    [data-testid="stSidebar"],
    section[data-testid="stSidebar"],
    [data-testid="stSidebarNav"],
    [data-testid="collapsedControl"] { display: none !important; }
    section.main { margin-left: 0 !important; }
    [data-testid="stAppViewContainer"] { padding-left: 0 !important; }

    .stApp {
        background: var(--app-bg);
        font-family: 'Manrope', -apple-system, BlinkMacSystemFont, sans-serif;
        color: var(--text);
    }

    .main .block-container {
        padding: 0.9rem 1.1rem;
        max-width: 1600px;
    }

    .nav-rail {
        background: var(--surface-1);
        border: 1px solid var(--border);
        border-radius: 18px;
        padding: 0.9rem;
        height: calc(100vh - 2.0rem);
        position: sticky;
        top: 0.9rem;
        overflow: hidden;
    }

    /* Streamlit renders widgets in its own blocks; to avoid "empty blocks",
       style the exact VerticalBlock that contains our marker. */
    div[data-testid="stVerticalBlock"]:has(#nav-rail-marker) {
        background: var(--shell-bg);
        border: 1px solid var(--border);
        border-radius: 18px;
        padding: 0.9rem;
        height: calc(100vh - 2.0rem);
        position: sticky;
        top: 0.9rem;
        overflow: hidden;
    }

    div[data-testid="stVerticalBlock"]:has(#nav-rail-marker) div.stButton {
        width: 100% !important;
    }

    div[data-testid="stVerticalBlock"]:has(#nav-rail-marker) div.stButton > button {
        width: 100% !important;
        min-width: 100% !important;
        border-radius: 14px !important;
        border: 1px solid transparent !important;
        background: transparent !important;
        color: var(--muted) !important;
        padding: 0.72rem 0.85rem !important;
        font-weight: 700 !important;
        text-align: left !important;
        display: flex !important;
        align-items: center !important;
        justify-content: flex-start !important;
        white-space: nowrap !important;
        overflow: hidden !important;
        text-overflow: ellipsis !important;
    }

    div[data-testid="stVerticalBlock"]:has(#nav-rail-marker) div.stButton > button:hover {
        background: rgba(35, 72, 47, 0.55) !important;
        border-color: rgba(35, 72, 47, 0.9) !important;
        color: var(--text) !important;
    }

    div[data-testid="stVerticalBlock"]:has(#nav-rail-marker) div.stButton > button[kind="primary"] {
        background: var(--surface-1) !important;
        border-color: rgba(19, 236, 91, 0.22) !important;
        color: var(--text) !important;
        border-left: 4px solid var(--accent) !important;
        padding-left: 0.7rem !important;
    }

    .nav-user {
        display: flex;
        align-items: center;
        gap: 0.7rem;
        padding: 0.75rem 0.6rem;
        border-top: 1px solid rgba(35, 72, 47, 0.75);
        margin-top: 0.9rem;
    }

    .nav-user .uava {
        width: 40px;
        height: 40px;
        border-radius: 999px;
        border: 1px solid rgba(35, 72, 47, 0.9);
        overflow: hidden;
        background: rgba(35, 72, 47, 0.35);
        flex-shrink: 0;
    }

    .nav-user .uava img { width: 40px; height: 40px; display: block; }

    .nav-user .utxt { min-width: 0; }
    .nav-user .utxt .n { color: var(--text); font-weight: 900; font-size: 0.92rem; line-height: 1.1; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
    .nav-user .utxt .s { color: var(--muted); font-weight: 800; font-size: 0.75rem; margin-top: 0.1rem; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }

    .topbar-panel {
        background: var(--surface-1);
        border: 1px solid rgba(35, 72, 47, 0.9);
        border-radius: 18px;
        padding: 0.9rem 1.0rem;
        margin-top: 0.55rem;
        margin-bottom: 0.9rem;
    }

    .topbar-panel .ttl { color: var(--text); font-weight: 900; }
    .topbar-panel .sub { color: var(--muted); font-weight: 800; font-size: 0.85rem; margin-top: 0.15rem; }

    div[data-testid="stVerticalBlock"]:has(#clients-left-marker) {
        background: var(--surface-2);
        border: 1px solid rgba(35, 72, 47, 0.9);
        border-radius: 18px;
        padding: 1.0rem;
    }

    div[data-testid="stVerticalBlock"]:has(#clients-right-marker) {
        background: var(--app-bg);
        border: 1px solid rgba(35, 72, 47, 0.9);
        border-radius: 18px;
        padding: 1.0rem;
    }

    div[data-testid="stVerticalBlock"]:has(#clients-add-marker) div.stButton > button[kind="primary"] {
        height: 42px;
        border-radius: 14px !important;
        background: var(--accent) !important;
        color: var(--app-bg) !important;
        border: 1px solid rgba(19, 236, 91, 0.35) !important;
        font-weight: 900 !important;
    }

    div[data-testid="stVerticalBlock"]:has(#clients-chips-marker) div.stButton > button {
        height: 32px;
        border-radius: 999px !important;
        background: var(--surface-2) !important;
        border: 1px solid var(--border) !important;
        color: var(--muted) !important;
        font-weight: 800 !important;
        padding: 0 0.85rem !important;
        white-space: nowrap !important;
    }

    div[data-testid="stVerticalBlock"]:has(#clients-chips-marker) div.stButton > button[kind="primary"] {
        background: var(--surface-3) !important;
        color: var(--text) !important;
        border-color: var(--accent) !important;
    }

    div[data-testid="stVerticalBlock"]:has(#clients-chips-marker) div.stButton > button:hover {
        background: var(--surface-3) !important;
        border-color: var(--accent) !important;
        color: var(--text) !important;
    }

    div[data-testid="stVerticalBlock"]:has(#clients-list-marker) div[role="radiogroup"] {
        display: flex;
        flex-direction: column;
        gap: 0.55rem;
    }

    div[data-testid="stVerticalBlock"]:has(#clients-list-marker) div[role="radiogroup"] label {
        border-radius: 14px !important;
        background: rgba(35, 72, 47, 0.40) !important;
        border: 1px solid rgba(35, 72, 47, 0.75) !important;
        border-left: 4px solid transparent !important;
        color: var(--text) !important;
        padding: 0.75rem 0.85rem !important;
        font-weight: 800 !important;
        margin: 0 !important;
    }

    div[data-testid="stVerticalBlock"]:has(#clients-list-marker) div[role="radiogroup"] label:hover {
        background: rgba(35, 72, 47, 0.65) !important;
        border-color: rgba(35, 72, 47, 0.95) !important;
    }

    div[data-testid="stVerticalBlock"]:has(#clients-list-marker) div[role="radiogroup"] label span[data-testid="stMarkdownContainer"] p {
        margin: 0 !important;
        white-space: pre-line !important;
        line-height: 1.25 !important;
    }

    div[data-testid="stVerticalBlock"]:has(#clients-list-marker) div[role="radiogroup"] input[type="radio"] {
        display: none !important;
    }

    div[data-testid="stVerticalBlock"]:has(#clients-list-marker) div[role="radiogroup"] label:has(input[type="radio"]:checked) {
        background: rgba(35, 72, 47, 0.75) !important;
        border-color: rgba(35, 72, 47, 0.95) !important;
        border-left-color: var(--accent) !important;
    }

    .nav-brand {
        display: flex;
        align-items: center;
        justify-content: space-between;
        gap: 0.75rem;
        padding: 0.2rem 0.1rem 0.8rem 0.1rem;
        border-bottom: 1px solid var(--border);
        margin-bottom: 0.75rem;
    }

    .nav-brand .brand {
        font-size: 1.05rem;
        font-weight: 800;
        letter-spacing: -0.01em;
        color: var(--text);
    }

    .nav-brand .brand span {
        color: var(--accent);
    }

    .nav-rail div.stButton > button {
        width: 100%;
        border-radius: 14px !important;
        border: 1px solid transparent !important;
        background: transparent !important;
        color: var(--text) !important;
        padding: 0.7rem 0.8rem !important;
        font-weight: 600 !important;
        text-align: left !important;
    }

    .nav-rail div.stButton > button:hover {
        background: var(--surface-2) !important;
        border-color: var(--border) !important;
    }

    .nav-rail div.stButton > button[kind="primary"] {
        background: var(--accent-2) !important;
        border-color: rgba(19, 236, 91, 0.45) !important;
        color: var(--text) !important;
    }

    .topbar-row {
        background: var(--surface-1);
        border: 1px solid var(--border);
        border-radius: 18px;
        padding: 0.75rem 0.85rem;
        margin-bottom: 1.0rem;
        display: flex;
        align-items: center;
        justify-content: space-between;
        gap: 1rem;
    }

    .topbar-row .topbar-title {
        font-weight: 800;
        letter-spacing: -0.015em;
        color: var(--text);
        font-size: 1.1rem;
    }

    .topbar-icon {
        width: 38px;
        height: 38px;
        border-radius: 12px;
        border: 1px solid var(--border);
        background: var(--surface-2);
        display: flex;
        align-items: center;
        justify-content: center;
        color: var(--text);
        font-size: 1.05rem;
    }

    .topbar-avatar {
        width: 38px;
        height: 38px;
        border-radius: 14px;
        border: 1px solid var(--border);
        overflow: hidden;
        background: var(--surface-2);
    }

    .topbar-avatar img {
        display: block;
        width: 38px;
        height: 38px;
    }

    /* Topbar wrapper (same note: style by marker) */
    div[data-testid="stVerticalBlock"]:has(#topbar-marker) {
        background: var(--shell-bg);
        border: 1px solid var(--border);
        border-radius: 18px;
        padding: 0.75rem 0.85rem;
        margin-bottom: 1.0rem;
    }

    div[data-testid="stVerticalBlock"]:has(#topbar-marker) div[data-testid="stHorizontalBlock"] {
        align-items: center;
    }

    .topbar-title {
        font-weight: 900;
        letter-spacing: -0.02em;
        color: var(--text);
        font-size: 1.1rem;
        line-height: 1.1;
        margin-top: 0.1rem;
    }

    .topbar-sub {
        color: var(--muted);
        font-size: 0.86rem;
        margin-top: 0.1rem;
    }

    .stTextInput input {
        border-radius: 14px !important;
        border-color: var(--border) !important;
        background: var(--surface-2) !important;
        color: var(--text) !important;
    }

    .kpi-card {
        background: var(--surface-1);
        border: 1px solid var(--border);
        border-radius: 18px;
        padding: 1.0rem 1.0rem;
    }

    .kpi-label {
        font-size: 0.78rem;
        text-transform: uppercase;
        letter-spacing: 0.1em;
        color: var(--muted);
        font-weight: 700;
    }

    .kpi-value {
        font-size: 1.7rem;
        font-weight: 850;
        letter-spacing: -0.02em;
        margin-top: 0.25rem;
        color: var(--text);
    }

    .kpi-foot {
        margin-top: 0.25rem;
        color: var(--muted);
        font-size: 0.88rem;
    }

    .hero-h1 {
        font-size: 2.4rem;
        font-weight: 900;
        letter-spacing: -0.02em;
        line-height: 1.05;
        color: var(--text);
        margin: 0;
    }

    .hero-h1 .accent {
        color: var(--accent);
    }

    .stat-card {
        background: var(--surface-1);
        border: 1px solid transparent;
        border-radius: 18px;
        padding: 1.1rem 1.2rem;
        transition: border-color 0.15s ease, transform 0.15s ease;
    }

    .stat-card:hover {
        border-color: rgba(19, 236, 91, 0.28);
        transform: translateY(-1px);
    }

    .stat-top {
        display: flex;
        justify-content: space-between;
        align-items: flex-start;
        gap: 0.75rem;
    }

    .stat-label-sm {
        color: var(--muted);
        font-size: 0.78rem;
        font-weight: 800;
        text-transform: uppercase;
        letter-spacing: 0.12em;
    }

    .stat-ico {
        color: var(--accent);
        font-size: 1.05rem;
        margin-top: 0.1rem;
    }

    .stat-value-lg {
        color: var(--text);
        font-size: 1.9rem;
        font-weight: 900;
        line-height: 1.0;
        margin-top: 0.55rem;
    }

    .stat-chip {
        display: inline-flex;
        align-items: center;
        gap: 0.35rem;
        padding: 0.18rem 0.55rem;
        border-radius: 10px;
        font-size: 0.75rem;
        font-weight: 900;
        background: rgba(19, 236, 91, 0.12);
        color: var(--accent);
        margin-left: 0.6rem;
        border: 1px solid rgba(19, 236, 91, 0.18);
    }

    .stat-chip.warn {
        background: rgba(245, 158, 11, 0.14);
        color: #fbbf24;
        border-color: rgba(245, 158, 11, 0.25);
    }

    .schedule-head {
        display: flex;
        align-items: flex-end;
        justify-content: space-between;
        padding-bottom: 0.6rem;
        border-bottom: 1px solid var(--border);
        margin-bottom: 0.85rem;
    }

    .schedule-title {
        color: var(--text);
        font-size: 1.15rem;
        font-weight: 900;
        letter-spacing: -0.01em;
    }

    .schedule-link {
        color: var(--accent);
        font-size: 0.9rem;
        font-weight: 900;
    }

    .session-card {
        display: flex;
        align-items: center;
        justify-content: space-between;
        gap: 1rem;
        background: var(--surface-1);
        border-radius: 18px;
        padding: 1.05rem 1.15rem;
        border-left: 4px solid var(--accent);
        margin-bottom: 0.85rem;
    }

    .session-card:last-child { margin-bottom: 0; }
    .session-card.purple { border-left-color: #a855f7; }
    .session-card.slate { border-left-color: #64748b; opacity: 0.75; }

    .session-left {
        display: flex;
        align-items: center;
        gap: 1rem;
        min-width: 0;
        flex: 1;
    }

    .session-time {
        min-width: 92px;
        display: flex;
        flex-direction: column;
        gap: 0.1rem;
    }

    .session-time .t {
        color: var(--text);
        font-weight: 900;
        font-size: 1.05rem;
        line-height: 1.0;
    }

    .session-time .d {
        color: var(--muted);
        font-weight: 800;
        font-size: 0.75rem;
    }

    .session-avatar {
        width: 46px;
        height: 46px;
        border-radius: 999px;
        border: 1px solid rgba(255,255,255,0.10);
        background: rgba(255,255,255,0.04);
        display: flex;
        align-items: center;
        justify-content: center;
    }

    .session-meta { min-width: 0; }

    .session-meta .name {
        color: var(--text);
        font-weight: 900;
        line-height: 1.1;
        white-space: nowrap;
        overflow: hidden;
        text-overflow: ellipsis;
    }

    .session-tags { display: flex; align-items: center; gap: 0.5rem; margin-top: 0.25rem; flex-wrap: wrap; }

    .tag {
        font-size: 0.75rem;
        font-weight: 900;
        padding: 0.14rem 0.55rem;
        border-radius: 10px;
        color: var(--text);
        background: rgba(255,255,255,0.10);
    }

    .tag.purple { background: rgba(168, 85, 247, 0.14); color: #d8b4fe; }
    .tag.muted { background: transparent; color: var(--muted); font-weight: 800; padding: 0; }

    .session-cta {
        border-radius: 14px;
        padding: 0.55rem 0.95rem;
        font-weight: 900;
        font-size: 0.9rem;
        background: var(--accent);
        color: var(--app-bg);
        border: 1px solid rgba(19, 236, 91, 0.35);
        white-space: nowrap;
        user-select: none;
    }

    .session-cta.ghost {
        background: transparent;
        color: var(--text);
        border: 1px solid rgba(255,255,255,0.20);
    }

    .session-cta.disabled {
        background: transparent;
        border: 1px solid transparent;
        color: rgba(231, 243, 235, 0.45);
    }

    .compliance-wrap {
        background: var(--surface-1);
        border-radius: 18px;
        padding: 1.25rem;
        margin-top: 1.15rem;
    }

    .compliance-head {
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 0.85rem;
    }

    .compliance-head .ttl { color: var(--text); font-weight: 900; font-size: 1.05rem; }
    .compliance-head .pct { color: var(--accent); font-weight: 900; font-size: 1.4rem; }

    .progress-track {
        height: 14px;
        width: 100%;
        background: var(--app-bg);
        border-radius: 999px;
        overflow: hidden;
        border: 1px solid rgba(255,255,255,0.06);
    }

    .progress-fill {
        height: 100%;
        background: linear-gradient(90deg, rgba(19,236,91,0.45), rgba(19,236,91,1));
        border-radius: 999px;
        position: relative;
    }

    .progress-fill::after {
        content: "";
        position: absolute;
        right: 0;
        top: 0;
        bottom: 0;
        width: 4px;
        background: rgba(255,255,255,0.9);
        box-shadow: 0 0 10px rgba(255,255,255,0.8);
    }

    .week-labels {
        display: flex;
        justify-content: space-between;
        margin-top: 0.55rem;
        color: var(--muted);
        font-size: 0.75rem;
        font-weight: 800;
    }

    .bars {
        display: flex;
        align-items: flex-end;
        gap: 0.45rem;
        height: 84px;
        margin-top: 0.75rem;
    }

    .bar {
        flex: 1;
        background: rgba(19,236,91,0.18);
        border-radius: 6px 6px 2px 2px;
    }

    .bar.hot { background: rgba(19,236,91,1.0); box-shadow: 0 0 15px rgba(19,236,91,0.18); }
    .bar.empty { background: rgba(255,255,255,0.06); }

    div[data-testid="stVerticalBlock"]:has(#qa-marker) div.stButton > button {
        height: 86px;
        border-radius: 16px !important;
        background: var(--surface-2) !important;
        border: 1px solid transparent !important;
        color: var(--text) !important;
        font-weight: 900 !important;
        white-space: pre-wrap !important;
        line-height: 1.2 !important;
    }

    div[data-testid="stVerticalBlock"]:has(#qa-marker) div.stButton > button:hover {
        background: var(--surface-3) !important;
        border-color: rgba(19, 236, 91, 0.25) !important;
    }

    .activity-head {
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 0.7rem;
    }

    .activity-title {
        color: var(--text);
        font-weight: 900;
        font-size: 1.05rem;
    }

    .activity-meta {
        color: var(--muted);
        font-weight: 800;
        font-size: 0.75rem;
    }

    .activity-item {
        display: flex;
        gap: 0.75rem;
        align-items: flex-start;
        padding: 0.75rem;
        border-radius: 14px;
        background: rgba(35, 72, 47, 0.35);
        border-left: 3px solid transparent;
        margin-bottom: 0.65rem;
    }

    .activity-item:last-child { margin-bottom: 0; }
    .activity-item.highlight { border-left-color: var(--accent); background: rgba(35, 72, 47, 0.50); }
    .activity-item.danger { border-left-color: #ef4444; background: rgba(239, 68, 68, 0.10); }

    .activity-avatar {
        width: 34px;
        height: 34px;
        border-radius: 999px;
        background: rgba(255,255,255,0.06);
        border: 1px solid rgba(255,255,255,0.10);
        display: flex;
        align-items: center;
        justify-content: center;
    }

    .activity-body { min-width: 0; }

    .activity-body .line {
        color: var(--text);
        font-size: 0.92rem;
        line-height: 1.25;
    }

    .activity-body .line b { font-weight: 900; }

    .activity-body .time {
        margin-top: 0.35rem;
        color: var(--muted);
        font-size: 0.72rem;
        font-weight: 800;
    }

    .activity-cta {
        margin-top: 0.5rem;
        display: inline-block;
        font-size: 0.75rem;
        font-weight: 900;
        padding: 0.22rem 0.55rem;
        border-radius: 10px;
        color: var(--text);
        background: rgba(239, 68, 68, 0.18);
        border: 1px solid rgba(239, 68, 68, 0.25);
        width: fit-content;
    }

    .section-card {
        background: var(--surface-1);
        border: 1px solid var(--border);
        border-radius: 18px;
        padding: 1.0rem;
    }

    .section-head {
        display: flex;
        align-items: center;
        justify-content: space-between;
        margin-bottom: 0.8rem;
    }

    .section-head .title {
        font-weight: 800;
        letter-spacing: -0.01em;
        color: var(--text);
    }

    .section-head .meta {
        font-size: 0.85rem;
        color: var(--muted);
    }

    .list-row {
        display: flex;
        align-items: center;
        justify-content: space-between;
        gap: 0.75rem;
        padding: 0.65rem 0.75rem;
        border-radius: 14px;
        border: 1px solid var(--border);
        background: var(--surface-2);
        margin-bottom: 0.55rem;
    }

    .list-row:last-child { margin-bottom: 0; }

    .list-row .left {
        display: flex;
        flex-direction: column;
        gap: 0.1rem;
        min-width: 0;
    }

    .list-row .left .name {
        font-weight: 700;
        color: var(--text);
        line-height: 1.1;
        overflow: hidden;
        text-overflow: ellipsis;
        white-space: nowrap;
    }

    .list-row .left .sub {
        color: var(--muted);
        font-size: 0.85rem;
        overflow: hidden;
        text-overflow: ellipsis;
        white-space: nowrap;
    }

    .pill {
        border: 1px solid var(--border);
        background: rgba(19, 236, 91, 0.10);
        color: var(--accent);
        font-weight: 750;
        padding: 0.22rem 0.55rem;
        border-radius: 999px;
        font-size: 0.78rem;
        white-space: nowrap;
    }

    /* ===== BENTO GRID SYSTEM ===== */
    .bento-grid {
        display: grid;
        grid-template-columns: repeat(12, 1fr);
        gap: 1.5rem;
        margin-bottom: 2rem;
    }

    .bento-card {
        background: var(--surface-1);
        border: 1px solid var(--border);
        border-radius: 16px;
        padding: 1.25rem;
        box-shadow: none;
        transition: all 0.2s ease;
    }

    .bento-card:hover {
        box-shadow: none;
        border-color: rgba(19, 236, 91, 0.28);
    }

    /* Card sizes */
    .bento-sm { grid-column: span 3; }
    .bento-md { grid-column: span 4; }
    .bento-lg { grid-column: span 6; }
    .bento-xl { grid-column: span 8; }
    .bento-full { grid-column: span 12; }

    /* ===== TYPOGRAPHY ===== */
    .hero-title {
        font-size: 2rem;
        font-weight: 700;
        letter-spacing: -0.02em;
        color: var(--text);
        margin: 0;
        line-height: 1.2;
    }

    .hero-subtitle {
        font-size: 0.95rem;
        font-weight: 400;
        color: var(--muted);
        margin-top: 0.25rem;
    }

    .stat-value {
        font-size: 2.5rem;
        font-weight: 700;
        letter-spacing: -0.02em;
        line-height: 1;
        margin-bottom: 0.25rem;
        color: var(--text);
    }

    .stat-value.blue { color: var(--accent); }
    .stat-value.emerald { color: var(--accent); }
    .stat-value.slate { color: var(--text); }
    .stat-value.amber { color: #fbbf24; }

    .stat-label {
        font-size: 0.8rem;
        font-weight: 500;
        color: var(--muted);
        text-transform: uppercase;
        letter-spacing: 0.03em;
    }

    .stat-trend {
        display: inline-flex;
        align-items: center;
        gap: 0.25rem;
        font-size: 0.75rem;
        font-weight: 500;
        padding: 0.25rem 0.5rem;
        border-radius: 6px;
        margin-top: 0.5rem;
    }

    .trend-up {
        background: rgba(19, 236, 91, 0.14);
        color: var(--accent);
    }

    .trend-down {
        background: rgba(239, 68, 68, 0.14);
        color: #f87171;
    }

    .trend-neutral {
        background: rgba(148, 163, 184, 0.14);
        color: #cbd5e1;
    }

    /* ===== SECTION HEADERS ===== */
    .section-header {
        display: flex;
        align-items: center;
        gap: 0.75rem;
        margin-bottom: 1rem;
    }

    .section-icon {
        width: 36px;
        height: 36px;
        border-radius: 10px;
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 1rem;
    }

    .section-icon.blue { background: rgba(19, 236, 91, 0.12); color: var(--accent); }
    .section-icon.emerald { background: rgba(19, 236, 91, 0.12); color: var(--accent); }
    .section-icon.amber { background: rgba(245, 158, 11, 0.14); color: #fbbf24; }
    .section-icon.red { background: rgba(239, 68, 68, 0.14); color: #f87171; }

    .section-title {
        font-size: 0.95rem;
        font-weight: 600;
        color: var(--text);
        margin: 0;
    }

    /* ===== ACTIVITY LIST ===== */
    .activity-item {
        display: flex;
        align-items: center;
        gap: 0.875rem;
        padding: 0.75rem 0;
        border-bottom: 1px solid rgba(255,255,255,0.06);
    }

    .activity-item:last-child {
        border-bottom: none;
    }

    .activity-avatar {
        width: 40px;
        height: 40px;
        border-radius: 50%;
        display: flex;
        align-items: center;
        justify-content: center;
        font-weight: 600;
        font-size: 0.85rem;
        flex-shrink: 0;
    }

    .avatar-active {
        background: #ecfdf5;
        color: #059669;
    }

    .avatar-warning {
        background: #fffbeb;
        color: #d97706;
    }

    .avatar-danger {
        background: #fef2f2;
        color: #dc2626;
    }

    .activity-content {
        flex: 1;
        min-width: 0;
    }

    .activity-name {
        font-weight: 600;
        color: var(--text);
        font-size: 0.9rem;
        margin-bottom: 0.125rem;
    }

    .activity-meta {
        font-size: 0.8rem;
        color: var(--muted);
    }

    .activity-badge {
        font-size: 0.75rem;
        font-weight: 500;
        padding: 0.25rem 0.625rem;
        border-radius: 9999px;
    }

    .badge-success {
        background: rgba(19, 236, 91, 0.14);
        color: var(--accent);
    }

    .badge-warning {
        background: rgba(245, 158, 11, 0.14);
        color: #fbbf24;
    }

    .badge-danger {
        background: rgba(239, 68, 68, 0.14);
        color: #f87171;
    }

    /* ===== ALERT CARDS ===== */
    .alert-card {
        background: rgba(239, 68, 68, 0.10);
        border: 1px solid rgba(239, 68, 68, 0.22);
        border-radius: 12px;
        padding: 1rem 1.25rem;
        margin-bottom: 0.75rem;
        display: flex;
        align-items: center;
        gap: 0.875rem;
    }

    .alert-card.warning {
        background: rgba(245, 158, 11, 0.12);
        border-color: rgba(245, 158, 11, 0.22);
    }

    .alert-icon {
        font-size: 1.1rem;
    }

    .alert-text {
        flex: 1;
        color: var(--text);
        font-size: 0.875rem;
    }

    .alert-text strong {
        color: var(--text);
    }

    /* ===== STATS CARD ===== */
    .avatar-card {
        background: var(--surface-1);
        border: 1px solid var(--border);
        border-radius: 16px;
        padding: 1.05rem;
        text-align: center;
        position: relative;
        overflow: hidden;
        min-height: 210px;
        display: flex;
        flex-direction: column;
        justify-content: center;
        align-items: center;
    }

    .avatar-card::before {
        content: '';
        position: absolute;
        top: -50px;
        right: -50px;
        width: 150px;
        height: 150px;
        background: radial-gradient(circle, rgba(19, 236, 91, 0.10) 0%, transparent 70%);
        pointer-events: none;
    }

    .avatar-placeholder {
        width: 100px;
        height: 100px;
        background: rgba(35, 72, 47, 0.45);
        border-radius: 50%;
        margin: 0 auto 1rem;
        position: relative;
        border: 1px solid rgba(35, 72, 47, 0.95);
        display: flex;
        align-items: center;
        justify-content: center;
    }

    .avatar-placeholder::before {
        content: '💪';
        font-size: 2.5rem;
    }

    .avatar-stats {
        display: flex;
        justify-content: center;
        gap: 2rem;
        margin-top: 1rem;
    }

    .avatar-stat {
        text-align: center;
    }

    .avatar-stat-value {
        font-size: 1.25rem;
        font-weight: 700;
        color: var(--accent);
    }

    .avatar-stat-label {
        font-size: 0.7rem;
        color: var(--muted);
        text-transform: uppercase;
        letter-spacing: 0.03em;
    }

    /* ===== PROGRESS RINGS ===== */
    .ring-container {
        display: flex;
        flex-direction: column;
        align-items: center;
        justify-content: center;
        padding: 1rem;
    }

    .ring-value {
        font-size: 2rem;
        font-weight: 700;
        color: var(--accent);
        margin-bottom: 0.25rem;
    }

    .ring-label {
        font-size: 0.8rem;
        color: var(--muted);
    }

    /* ===== BUTTONS ===== */
    .stButton > button {
        background: var(--surface-2) !important;
        color: var(--text) !important;
        border: 1px solid var(--border) !important;
        border-radius: 14px !important;
        font-weight: 800 !important;
        padding: 0.625rem 1.25rem !important;
        transition: all 0.2s ease !important;
    }

    .stButton > button:hover {
        background: var(--surface-3) !important;
        box-shadow: none !important;
    }

    .stButton > button[kind="primary"] {
        background: var(--accent) !important;
        color: var(--app-bg) !important;
        border: 1px solid rgba(19, 236, 91, 0.35) !important;
        font-weight: 900 !important;
    }

    .stButton > button[kind="primary"]:hover {
        background: rgba(19, 236, 91, 0.92) !important;
        box-shadow: none !important;
    }

    .stButton > button[kind="secondary"] {
        background: var(--surface-2) !important;
        color: var(--text) !important;
        border: 1px solid var(--border) !important;
    }

    .stButton > button[kind="secondary"]:hover {
        background: var(--surface-3) !important;
        border-color: rgba(19, 236, 91, 0.18) !important;
        box-shadow: none !important;
    }

    /* Re-override for topbar icon buttons (must come after global .stButton rules) */
    div[data-testid="stVerticalBlock"]:has(#topbar-notif-marker) div.stButton,
    div[data-testid="stVerticalBlock"]:has(#topbar-user-marker) div.stButton {
        width: 38px !important;
        min-width: 38px !important;
        max-width: 38px !important;
    }

    div[data-testid="stVerticalBlock"]:has(#topbar-notif-marker) div.stButton > button,
    div[data-testid="stVerticalBlock"]:has(#topbar-user-marker) div.stButton > button {
        width: 38px !important;
        min-width: 38px !important;
        max-width: 38px !important;
        height: 38px !important;
        min-height: 38px !important;
        max-height: 38px !important;
        padding: 0 !important;
        border-radius: 12px !important;
        display: flex !important;
        align-items: center !important;
        justify-content: center !important;
        background: var(--surface-2) !important;
        color: var(--text) !important;
        border: 1px solid var(--border) !important;
        box-shadow: none !important;
        line-height: 1 !important;
    }

    /* ===== SIDEBAR ===== */
    [data-testid="stSidebar"] {
        background: var(--shell-bg);
        border-right: 1px solid var(--border);
        min-width: 216px;
        width: 216px;
        max-width: 216px;
    }

    [data-testid="stSidebar"] [data-testid="stSidebarContent"] {
        padding-top: 0.35rem;
    }

    [data-testid="stSidebar"] .block-container {
        padding-left: 0.75rem;
        padding-right: 0.75rem;
    }

    [data-testid="stSidebar"] [data-testid="stVerticalBlock"] {
        gap: 0.35rem;
    }

    [data-testid="stSidebar"] .stButton > button {
        padding: 0.45rem 0.75rem !important;
        font-size: 0.85rem !important;
        border-radius: 10px !important;
    }

    [data-testid="stSidebar"] .stToggleSwitch {
        transform: scale(0.92);
        transform-origin: left center;
    }

    [data-testid="stSidebar"] hr {
        margin: 0.55rem 0;
    }

    [data-testid="stSidebar"] .stMarkdown {
        color: var(--text);
    }

    /* ===== METRICS OVERRIDE ===== */
    [data-testid="stMetricValue"] {
        font-size: 2rem !important;
        font-weight: 700 !important;
        color: var(--text) !important;
    }

    [data-testid="stMetricDelta"] {
        color: var(--accent) !important;
    }

    [data-testid="stMetricLabel"] {
        color: var(--muted) !important;
    }

    /* ===== CHARTS ===== */
    .js-plotly-plot .plotly .modebar {
        display: none !important;
    }

    /* ===== TICKET CARDS ===== */
    .ticket-card {
        background: var(--surface-1);
        border: 1px solid var(--border);
        border-radius: 8px;
        padding: 0.75rem;
        margin-bottom: 0.5rem;
        transition: all 0.15s ease;
    }

    .ticket-card:hover {
        background: var(--surface-2);
        border-color: rgba(19, 236, 91, 0.18);
    }

    .ticket-card.priority-high {
        border-left: 3px solid #dc2626;
    }

    .ticket-card.priority-normal {
        border-left: 3px solid var(--accent);
    }

    .ticket-card .ticket-subject {
        color: var(--text);
        font-weight: 500;
        font-size: 0.85rem;
    }

    .ticket-card .ticket-meta {
        color: var(--muted);
        font-size: 0.7rem;
        margin-top: 0.25rem;
    }

    .chip {
        display: inline-flex;
        align-items: center;
        gap: 0.35rem;
        padding: 0.2rem 0.55rem;
        border-radius: 999px;
        border: 1px solid var(--border);
        font-size: 0.72rem;
        font-weight: 600;
        line-height: 1;
        white-space: nowrap;
    }

    .chip.new, .chip.active { background: rgba(19, 236, 91, 0.14); color: var(--accent); }
    .chip.assigned, .chip.stagnating { background: rgba(245, 158, 11, 0.14); color: #fbbf24; }
    .chip.done { background: rgba(148, 163, 184, 0.14); color: #cbd5e1; }
    .chip.problem { background: rgba(239, 68, 68, 0.14); color: #f87171; }

    .avatar-img {
        width: 44px;
        height: 44px;
        border-radius: 12px;
        border: 1px solid var(--border);
        background: var(--surface-2);
        display: block;
    }

    .inbox-detail-body {
        background: var(--app-bg);
        border: 1px solid var(--border);
        border-radius: 12px;
        padding: 0.85rem;
        max-height: 420px;
        overflow: auto;
        white-space: pre-wrap;
        font-size: 0.9rem;
        line-height: 1.35;
        color: var(--text);
    }

    .inbox-item {
        border: 1px solid var(--border);
        border-radius: 12px;
        padding: 0.65rem 0.75rem;
        background: var(--surface-1);
        margin-bottom: 0.5rem;
    }

    .inbox-item.selected {
        border-color: rgba(19, 236, 91, 0.28);
        background: var(--surface-2);
    }

    .inbox-item-title {
        font-weight: 700;
        font-size: 0.95rem;
        color: var(--text);
        line-height: 1.25;
    }

    .inbox-item-meta {
        display: flex;
        justify-content: space-between;
        gap: 0.75rem;
        margin-top: 0.25rem;
        color: var(--muted);
        font-size: 0.8rem;
    }

    .inbox-item-snippet {
        margin-top: 0.35rem;
        color: var(--muted);
        font-size: 0.82rem;
        line-height: 1.25;
    }

    /* ===== LEGACY OVERRIDES ===== */
    .main-header {
        font-size: 1.5rem;
        font-weight: 600;
        color: var(--text);
        letter-spacing: -0.01em;
        margin-bottom: 1rem;
    }

    hr {
        margin: 0.85rem 0;
        border: none;
        border-top: 1px solid var(--border);
    }

    .stTabs [data-baseweb="tab-list"] {
        background: var(--surface-2);
        border-radius: 8px;
        padding: 0.25rem;
        gap: 0.25rem;
    }

    .stTabs [data-baseweb="tab"] {
        background: transparent;
        color: var(--muted);
        border-radius: 6px;
    }

    .stTabs [aria-selected="true"] {
        background: var(--surface-1) !important;
        color: var(--text) !important;
        box-shadow: none;
    }

    /* Plan sections */
    .plan-section {
        background: var(--surface-1);
        border: 1px solid var(--border);
        border-radius: 12px;
        padding: 1.5rem;
    }

    .plan-header {
        color: var(--text);
        border-bottom: 1px solid var(--border);
        padding-bottom: 0.75rem;
        margin-bottom: 1rem;
    }

    /* Nutrition cards */
    .nutrition-card {
        background: var(--surface-1);
        border: 1px solid var(--border);
        border-radius: 12px;
        padding: 1rem;
    }

    .nutrition-value {
        color: var(--text) !important;
        font-weight: 700;
    }

    .nutrition-label {
        color: var(--muted) !important;
    }

    /* Text inputs */
    .stTextInput input, .stTextArea textarea {
        background: var(--surface-1) !important;
        border: 1px solid var(--border) !important;
        color: var(--text) !important;
        border-radius: 14px !important;
    }

    .stTextInput input:focus, .stTextArea textarea:focus {
        border-color: rgba(19, 236, 91, 0.28) !important;
        box-shadow: 0 0 0 3px rgba(19, 236, 91, 0.08) !important;
    }

/* Progress bars */
.stProgress > div > div {
    background: rgba(255,255,255,0.06) !important;
}

.stProgress > div > div > div {
    background: var(--accent) !important;
    border-radius: 9999px !important;
}

/* Streamlit markdown text */
.stMarkdown, .stMarkdown p {
    color: var(--text) !important;
}

h1, h2, h3, h4, h5, h6 {
    color: var(--text) !important;
}
</style>
""", unsafe_allow_html=True)


def get_api_key():
    """Get API key from secrets or environment"""
    try:
        key = st.secrets["gemini"]["api_key"]
        if key:
            return key
    except (KeyError, FileNotFoundError):
        pass
    return os.getenv('GEMINI_API_KEY', '')


def get_nutrition_api_key():
    """Get Nutrition API key from secrets or environment"""
    try:
        key = st.secrets.get("nutrition", {}).get("api_key", "")
        if key:
            return key
    except (KeyError, FileNotFoundError):
        pass
    return os.getenv('NUTRITION_API_KEY', '')


def fetch_nutrition_info(food_query: str) -> dict:
    """Fetch nutrition info from API Ninjas"""
    api_key = get_nutrition_api_key()
    if not api_key:
        return None

    try:
        response = requests.get(
            'https://api.api-ninjas.com/v1/nutrition',
            params={'query': food_query},
            headers={'X-Api-Key': api_key},
            timeout=5
        )
        if response.status_code == 200:
            data = response.json()
            if data:
                # Aggregate nutrition for all items
                totals = {
                    'calories': sum(item.get('calories', 0) for item in data),
                    'protein_g': sum(item.get('protein_g', 0) for item in data),
                    'carbs_g': sum(item.get('carbohydrates_total_g', 0) for item in data),
                    'fat_g': sum(item.get('fat_total_g', 0) for item in data),
                    'fiber_g': sum(item.get('fiber_g', 0) for item in data),
                    'sugar_g': sum(item.get('sugar_g', 0) for item in data),
                    'items': data
                }
                return totals
    except Exception:
        pass
    return None


def _initials(name: str) -> str:
    parts = [p for p in (name or "").strip().split() if p]
    if not parts:
        return "?"
    return "".join([p[0].upper() for p in parts[:2]])


def _avatar_data_uri(seed: str) -> str:
    digest = hashlib.sha256((seed or "").encode("utf-8")).hexdigest()
    palette = [
        ("#2563eb", "#60a5fa"),
        ("#7c3aed", "#a78bfa"),
        ("#059669", "#34d399"),
        ("#d97706", "#fbbf24"),
        ("#dc2626", "#f87171"),
        ("#0f172a", "#475569"),
    ]
    idx = int(digest[:2], 16) % len(palette)
    c1, c2 = palette[idx]
    initials = html.escape(_initials(seed))
    svg = f"""<svg xmlns='http://www.w3.org/2000/svg' width='88' height='88' viewBox='0 0 88 88'>
  <defs>
    <linearGradient id='g' x1='0' y1='0' x2='1' y2='1'>
      <stop offset='0' stop-color='{c1}'/>
      <stop offset='1' stop-color='{c2}'/>
    </linearGradient>
  </defs>
  <rect x='0' y='0' width='88' height='88' rx='18' fill='url(#g)'/>
  <text x='44' y='52' text-anchor='middle' font-family='Inter, Arial, sans-serif' font-size='30' font-weight='700' fill='white'>{initials}</text>
</svg>"""
    b64 = base64.b64encode(svg.encode("utf-8")).decode("ascii")
    return f"data:image/svg+xml;base64,{b64}"


def _portrait_data_uri(seed: str) -> str:
    h = hashlib.md5((seed or "").encode("utf-8")).hexdigest()
    bg = ["#eef2ff", "#ecfeff", "#fef3c7", "#ecfdf5", "#fce7f3", "#f1f5f9"][int(h[0], 16) % 6]
    hair = ["#0f172a", "#111827", "#1f2937", "#0b1320"][int(h[1], 16) % 4]
    skin = ["#f2c9ac", "#f6d3b8", "#eec3a5", "#f7d7c2"][int(h[2], 16) % 4]
    shirt = ["#2563eb", "#059669", "#7c3aed", "#d97706", "#0ea5e9"][int(h[3], 16) % 5]
    accent = ["#93c5fd", "#86efac", "#c4b5fd", "#fcd34d", "#67e8f9"][int(h[4], 16) % 5]

    svg = f"""<svg xmlns='http://www.w3.org/2000/svg' width='96' height='96' viewBox='0 0 96 96'>
    <defs>
      <linearGradient id='g' x1='0' y1='0' x2='1' y2='1'>
        <stop offset='0' stop-color='{bg}'/>
        <stop offset='1' stop-color='#ffffff'/>
      </linearGradient>
    </defs>
    <rect width='96' height='96' rx='48' fill='url(#g)'/>
    <circle cx='48' cy='42' r='18' fill='{skin}'/>
    <path d='M30 44c2-14 34-14 36 0v4c-6 6-30 6-36 0z' fill='{hair}' opacity='0.95'/>
    <path d='M22 92c4-20 18-28 26-28s22 8 26 28' fill='{shirt}'/>
    <path d='M30 76c6 4 30 4 36 0' stroke='{accent}' stroke-width='4' stroke-linecap='round' opacity='0.9'/>
    </svg>"""
    encoded = base64.b64encode(svg.encode("utf-8")).decode("utf-8")
    return f"data:image/svg+xml;base64,{encoded}"


def _icon_avatar_html(seed: str, size: int) -> str:
    h = hashlib.md5((seed or "").encode("utf-8")).hexdigest()
    bg = ["rgba(19,236,91,0.18)", "rgba(147,197,253,0.18)", "rgba(196,181,253,0.18)", "rgba(252,211,77,0.18)"][int(h[0], 16) % 4]
    bd = "rgba(35,72,47,0.85)"
    return (
        f"<div class='ui-ava' style='width:{size}px;height:{size}px;border-radius:999px;"
        f"border:1px solid {bd};background:{bg};display:flex;align-items:center;justify-content:center;'>"
        f"<span style='font-size:{max(12, int(size*0.45))}px; line-height:1;'>👤</span></div>"
    )


def init_session_state():
    """Initialize session state variables"""
    if 'page' not in st.session_state:
        st.session_state.page = 'dashboard'
    if 'selected_client' not in st.session_state:
        st.session_state.selected_client = None
    if 'clients' not in st.session_state:
        st.session_state.clients = get_mock_clients()
    if 'profile' not in st.session_state:
        st.session_state.profile = None
    if 'meal_plan' not in st.session_state:
        st.session_state.meal_plan = None
    if 'training_plan' not in st.session_state:
        st.session_state.training_plan = None
    if 'email_tickets' not in st.session_state:
        st.session_state.email_tickets = [
            {**t, "read": False, "source": "demo"}
            for t in DEMO_EMAILS.copy()
        ]
    if 'selected_ticket' not in st.session_state:
        st.session_state.selected_ticket = None
    if 'inbox_folder' not in st.session_state:
        st.session_state.inbox_folder = 'inbox'
    if 'inbox_page' not in st.session_state:
        st.session_state.inbox_page = 1
    if 'inbox_page_size' not in st.session_state:
        st.session_state.inbox_page_size = 25
    if 'clients_page' not in st.session_state:
        st.session_state.clients_page = 1
    if 'clients_page_size' not in st.session_state:
        st.session_state.clients_page_size = 25
    if 'clients_filter' not in st.session_state:
        st.session_state.clients_filter = 'all'
    if 'imap_settings' not in st.session_state:
        st.session_state.imap_settings = {
            "host": os.getenv("IMAP_HOST", "imap.gmail.com"),
            "port": int(os.getenv("IMAP_PORT", "993")),
            "username": os.getenv("EMAIL_USER", ""),
            "password": "",
            "use_ssl": True,
            "starttls": False,
            "mailbox": os.getenv("IMAP_MAILBOX", "INBOX"),
        }
    if 'imap_last_test' not in st.session_state:
        st.session_state.imap_last_test = {"ok": None, "error": None}
    if 'generation_mode' not in st.session_state:
        st.session_state.generation_mode = 'auto'
    if 'editable_meal_plan' not in st.session_state:
        st.session_state.editable_meal_plan = None
    if 'editable_training_plan' not in st.session_state:
        st.session_state.editable_training_plan = None
    if 'dark_mode' not in st.session_state:
        st.session_state.dark_mode = True
    if 'show_notifications' not in st.session_state:
        st.session_state.show_notifications = False
    if 'show_user_menu' not in st.session_state:
        st.session_state.show_user_menu = False


def render_sidebar():
    """Render navigation sidebar with dark mode toggle"""
    dm = st.session_state.dark_mode
    with st.sidebar:
        # Logo / Brand
        st.markdown(f"""
        <div style="padding: 0.65rem 0 0.75rem 0;">
            <span style="font-size: 1.25rem; font-weight: 800; color: #2563eb;">FIT</span>
            <span style="font-size: 1.25rem; font-weight: 500; color: {'#94a3b8' if dm else '#64748b'};">CRM</span>
        </div>
        """, unsafe_allow_html=True)

        # Dark mode toggle
        dark_mode = st.toggle("🌙 Tmavý režim", value=st.session_state.dark_mode, key="dark_toggle")
        if dark_mode != st.session_state.dark_mode:
            st.session_state.dark_mode = dark_mode
            st.rerun()

        st.markdown('<div style="height: 0.4rem;"></div>', unsafe_allow_html=True)

        # Navigation
        st.markdown(f'<p style="color: {"#94a3b8" if dm else "#64748b"}; font-size: 0.7rem; text-transform: uppercase; letter-spacing: 0.1em; margin-bottom: 0.5rem;">Nabídka</p>', unsafe_allow_html=True)

        if st.button("📊  Přehled", use_container_width=True,
                     type="primary" if st.session_state.page == 'dashboard' else "secondary"):
            st.session_state.page = 'dashboard'
            st.session_state.selected_client = None
            st.rerun()

        if st.button("📥  Inbox", use_container_width=True,
                     type="primary" if st.session_state.page == 'inbox' else "secondary"):
            st.session_state.page = 'inbox'
            st.session_state.selected_client = None
            st.rerun()

        if st.button("👥  Klienti", use_container_width=True,
                     type="primary" if st.session_state.page == 'clients' else "secondary"):
            st.session_state.page = 'clients'
            st.session_state.selected_client = None
            st.rerun()

        if st.button("➕  Nový klient", use_container_width=True,
                     type="primary" if st.session_state.page == 'new_client' else "secondary"):
            st.session_state.page = 'new_client'
            st.rerun()

        if st.button("⚙️  Email konektor", use_container_width=True,
                     type="primary" if st.session_state.page == 'email_connector' else "secondary"):
            st.session_state.page = 'email_connector'
            st.rerun()

        st.markdown('<div style="height: 0.35rem;"></div>', unsafe_allow_html=True)

        # Email Feed / Tickets
        new_tickets = [t for t in st.session_state.email_tickets if t.get("status") == "new"]
        st.markdown(f'<p style="color: {"#94a3b8" if dm else "#64748b"}; font-size: 0.7rem; text-transform: uppercase; letter-spacing: 0.1em; margin-bottom: 0.5rem;">Příchozí <span style="color: #2563eb; font-weight: 600;">({len(new_tickets)})</span></p>', unsafe_allow_html=True)

        for ticket in st.session_state.email_tickets[:3]:
            priority_class = f"priority-{ticket['priority']}"
            status_dot = {
                'new': '●',
                'assigned': '◐',
                'done': '✓'
            }.get(ticket['status'], '')
            status_color = {'new': '#059669', 'assigned': '#d97706', 'done': '#64748b'}.get(ticket['status'], '#64748b')

            st.markdown(f"""
            <div class="ticket-card {priority_class}">
                <div class="ticket-subject"><span style="color: {status_color};">{status_dot}</span> {ticket['subject'].split(': ')[-1]}</div>
                <div class="ticket-meta">{ticket['time']}</div>
            </div>
            """, unsafe_allow_html=True)

            if st.button("Přiřadit →", key=f"assign_{ticket['id']}", use_container_width=True):
                for t in st.session_state.email_tickets:
                    if t['id'] == ticket['id']:
                        t['status'] = 'assigned'
                        break
                st.session_state.selected_ticket = ticket
                st.session_state.page = 'new_client'
                st.session_state.profile = None
                st.session_state.meal_plan = None
                st.session_state.training_plan = None
                st.rerun()

        st.markdown('<div style="height: 0.35rem;"></div>', unsafe_allow_html=True)

        # API Status
        st.markdown(f'<p style="color: {"#94a3b8" if dm else "#64748b"}; font-size: 0.7rem; text-transform: uppercase; letter-spacing: 0.1em; margin-bottom: 0.5rem;">Stav</p>', unsafe_allow_html=True)

        api_key = get_api_key()
        nutrition_key = get_nutrition_api_key()

        status_html = f"""
        <div style="display: flex; gap: 0.5rem; flex-wrap: wrap;">
            <span style="background: {'#ecfdf5' if api_key else '#fef2f2'};
                         color: {'#059669' if api_key else '#dc2626'};
                         padding: 0.25rem 0.5rem; border-radius: 6px; font-size: 0.7rem; font-weight: 500;">
                {'✓' if api_key else '✗'} Gemini
            </span>
            <span style="background: {'#eff6ff' if nutrition_key else '#f1f5f9'};
                         color: {'#2563eb' if nutrition_key else '#64748b'};
                         padding: 0.25rem 0.5rem; border-radius: 6px; font-size: 0.7rem; font-weight: 500;">
                {'✓' if nutrition_key else '○'} Výživa
            </span>
        </div>
        """
        st.markdown(status_html, unsafe_allow_html=True)

        sha = _git_sha_short()
        sha_txt = f" · {sha}" if sha else ""
        st.markdown('<div style="height: 0.6rem;"></div>', unsafe_allow_html=True)
        st.markdown(f'<p style="color: #94a3b8; font-size: 0.65rem;">FIT CRM v{APP_VERSION}{sha_txt} · {"Tmavý" if dm else "Svetlý"}</p>', unsafe_allow_html=True)


def _relative_time(dt: datetime) -> str:
    now = datetime.now(dt.tzinfo) if dt.tzinfo else datetime.now()
    delta = now - dt
    seconds = int(delta.total_seconds())
    if seconds < 60:
        return "pred chvíľou"
    minutes = seconds // 60
    if minutes < 60:
        return f"pred {minutes} min"
    hours = minutes // 60
    if hours < 24:
        return f"pred {hours} hod"
    days = hours // 24
    return f"pred {days} dň"


def _imap_settings_to_account() -> ImapAccount:
    s = st.session_state.imap_settings
    return ImapAccount(
        host=s.get("host", ""),
        port=int(s.get("port", 993)),
        username=s.get("username", ""),
        password=s.get("password", ""),
        use_ssl=bool(s.get("use_ssl", True)),
        starttls=bool(s.get("starttls", False)),
    )


def _ingest_imap_messages(messages):
    existing_ids = {t.get("id") for t in st.session_state.email_tickets}
    for m in messages:
        uid = m.get("uid")
        ticket_id = f"imap_{uid}"
        if ticket_id in existing_ids:
            continue
        dt = m.get("date")
        st.session_state.email_tickets.insert(
            0,
            {
                "id": ticket_id,
                "subject": m.get("subject") or "(bez predmetu)",
                "from": m.get("from") or "",
                "time": _relative_time(dt) if dt else "",
                "priority": "normal",
                "status": "new",
                "content": m.get("body") or "",
                "read": False,
                "source": "imap",
            },
        )


def render_email_connector():
    st.markdown('<div class="main-header">⚙️ Email konektor</div>', unsafe_allow_html=True)

    st.caption("Nastav IMAP prístup pre načítanie emailov do Inboxu. Pre Gmail použi App Password.")

    s = st.session_state.imap_settings
    col1, col2 = st.columns([2, 1])
    with col1:
        s["host"] = st.text_input("IMAP host", value=s.get("host", "imap.gmail.com"))
        s["port"] = st.number_input("IMAP port", min_value=1, max_value=65535, value=int(s.get("port", 993)))
        s["mailbox"] = st.text_input("Mailbox", value=s.get("mailbox", "INBOX"))

    with col2:
        s["use_ssl"] = st.checkbox("Použiť SSL", value=bool(s.get("use_ssl", True)))
        s["starttls"] = st.checkbox("STARTTLS (ak bez SSL)", value=bool(s.get("starttls", False)))

    st.markdown("---")
    col1, col2 = st.columns(2)
    with col1:
        s["username"] = st.text_input("Používateľ", value=s.get("username", ""))
    with col2:
        s["password"] = st.text_input("Heslo / App Password", value=s.get("password", ""), type="password")

    st.markdown("---")
    col1, col2, col3 = st.columns([1, 1, 2])
    with col1:
        if st.button("✅ Test pripojenia", type="primary", use_container_width=True):
            ok, err = test_imap_connection(_imap_settings_to_account(), mailbox=s.get("mailbox", "INBOX"))
            st.session_state.imap_last_test = {"ok": ok, "error": err}
            st.rerun()

    with col2:
        if st.button("📥 Načítať emaily", use_container_width=True):
            try:
                msgs = fetch_imap_messages(
                    _imap_settings_to_account(),
                    mailbox=s.get("mailbox", "INBOX"),
                    limit=25,
                )
                _ingest_imap_messages(msgs)
                st.success(f"✅ Načítané: {len(msgs)}")
            except Exception as e:
                st.error(f"❌ Chyba: {e}")

    with col3:
        test = st.session_state.imap_last_test
        if test.get("ok") is True:
            st.success("Pripojenie OK")
        elif test.get("ok") is False:
            st.error(f"Chyba pripojenia: {test.get('error')}")
        else:
            st.info("Otestuj pripojenie a potom načítaj emaily do Inboxu.")


def render_inbox():
    st.markdown('<div class="main-header">📥 Inbox</div>', unsafe_allow_html=True)

    tickets = st.session_state.email_tickets

    st.markdown('<div class="bento-card" style="padding: 0.85rem 1rem; margin-bottom: 1rem;">', unsafe_allow_html=True)
    tcol1, tcol2, tcol3, tcol4, tcol5, tcol6 = st.columns([2.1, 1.1, 1.1, 1.0, 1.0, 1.0])
    with tcol1:
        query = st.text_input("", placeholder="Hľadať v inboxe…", label_visibility="collapsed")
    with tcol2:
        folder_label = st.selectbox(
            "",
            options=["Inbox", "Priradené", "Hotové", "Všetko"],
            index={"inbox": 0, "assigned": 1, "done": 2, "all": 3}.get(st.session_state.inbox_folder, 0),
            label_visibility="collapsed",
        )
        st.session_state.inbox_folder = {"Inbox": "inbox", "Priradené": "assigned", "Hotové": "done", "Všetko": "all"}.get(folder_label, "inbox")
    with tcol3:
        status_filter = st.selectbox("Stav", ["Všetko", "Nové", "Priradené", "Hotové"], label_visibility="collapsed")
    with tcol4:
        show_unread_only = st.checkbox("Len neprečítané", value=False)
    with tcol5:
        st.session_state.inbox_page_size = st.selectbox(
            "",
            options=[25, 50, 100],
            index=[25, 50, 100].index(st.session_state.inbox_page_size) if st.session_state.inbox_page_size in [25, 50, 100] else 0,
            label_visibility="collapsed",
            key="inbox_page_size_toolbar",
        )
    with tcol6:
        if st.button("🔄 Obnoviť", use_container_width=True):
            st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)

    col_list, col_detail = st.columns([1.55, 2.45])

    filtered = tickets
    if st.session_state.inbox_folder == "inbox":
        filtered = [t for t in filtered if t.get("status") == "new"]
    elif st.session_state.inbox_folder == "assigned":
        filtered = [t for t in filtered if t.get("status") == "assigned"]
    elif st.session_state.inbox_folder == "done":
        filtered = [t for t in filtered if t.get("status") == "done"]

    if status_filter == "Nové":
        filtered = [t for t in filtered if t.get("status") == "new"]
    elif status_filter == "Priradené":
        filtered = [t for t in filtered if t.get("status") == "assigned"]
    elif status_filter == "Hotové":
        filtered = [t for t in filtered if t.get("status") == "done"]

    if show_unread_only:
        filtered = [t for t in filtered if not t.get("read")]

    if query:
        q = query.lower().strip()
        filtered = [
            t for t in filtered
            if q in (t.get("subject") or "").lower()
            or q in (t.get("from") or "").lower()
            or q in (t.get("content") or "").lower()
        ]

    with col_list:
        st.markdown('<div class="bento-card" style="padding: 0.9rem;">', unsafe_allow_html=True)
        total = len(filtered)
        unread = len([t for t in filtered if not t.get("read")])

        st.caption(f"Správy: {total} · Neprečítané: {unread}")

        if not filtered:
            st.info("Inbox je prázdny (alebo nič nezodpovedá filtru).")
        else:
            page_size = int(st.session_state.inbox_page_size)
            page_count = max(1, (total + page_size - 1) // page_size)
            if st.session_state.inbox_page > page_count:
                st.session_state.inbox_page = page_count
            if st.session_state.inbox_page < 1:
                st.session_state.inbox_page = 1

            nav1, nav2, nav3 = st.columns([1, 1, 2])
            with nav1:
                if st.button("←", use_container_width=True, disabled=st.session_state.inbox_page <= 1, key="inbox_prev"):
                    st.session_state.inbox_page -= 1
                    st.rerun()
            with nav2:
                if st.button("→", use_container_width=True, disabled=st.session_state.inbox_page >= page_count, key="inbox_next"):
                    st.session_state.inbox_page += 1
                    st.rerun()
            with nav3:
                st.caption(f"Strana {st.session_state.inbox_page} / {page_count}")

            start = (st.session_state.inbox_page - 1) * page_size
            end = start + page_size
            visible = filtered[start:end]

            for t in visible:
                tid = t.get("id")
                subject = (t.get("subject") or "(bez predmetu)").strip()
                from_ = (t.get("from") or "").strip()
                time_ = (t.get("time") or "").strip()
                content = (t.get("content") or "").replace("\n", " ").strip()
                snippet = content[:120] + ("…" if len(content) > 120 else "")
                status_raw = (t.get("status") or "").strip().lower()
                status_label = {"new": "Nové", "assigned": "Priradené", "done": "Hotové"}.get(status_raw, status_raw)

                selected_now = bool(st.session_state.selected_ticket and st.session_state.selected_ticket.get("id") == tid)
                unread_dot = "● " if not t.get("read") else ""
                wrap_cls = "inbox-item selected" if selected_now else "inbox-item"

                st.markdown(
                    f"""
                    <div class="{wrap_cls}">
                        <div class="inbox-item-title">{html.escape(unread_dot + subject)}</div>
                        <div class="inbox-item-meta">
                            <span>{html.escape(from_)}</span>
                            <span>{html.escape(time_)} · {html.escape(status_label)}</span>
                        </div>
                        <div class="inbox-item-snippet">{html.escape(snippet)}</div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

                if st.button("Otvoriť", key=f"open_ticket_{tid}", use_container_width=True, type="secondary"):
                    st.session_state.selected_ticket = t
                    t["read"] = True
                    st.rerun()

        st.markdown('</div>', unsafe_allow_html=True)

    with col_detail:
        st.markdown('<div class="bento-card" style="padding: 0.9rem;">', unsafe_allow_html=True)
        sel = st.session_state.selected_ticket
        if not sel:
            st.markdown(
                """
                <div style="text-align:center; padding: 2.25rem 1rem;">
                    <div style="font-size: 2.1rem; margin-bottom: 0.35rem;">📨</div>
                    <div style="font-weight: 700; color: #0f172a;">Vyber správu</div>
                    <div style="margin-top: 0.35rem; color: #64748b; font-size: 0.9rem;">Klikni na správu vľavo pre náhľad a akcie.</div>
                </div>
                """,
                unsafe_allow_html=True,
            )
        else:
            subject = (sel.get("subject") or "").strip()
            from_ = (sel.get("from") or "").strip()
            time_ = (sel.get("time") or "").strip()
            source_ = (sel.get("source") or "").strip()
            status_raw = (sel.get("status") or "").strip().lower()
            status_label = {
                "new": "Nové",
                "assigned": "Priradené",
                "done": "Hotové",
            }.get(status_raw, status_raw)

            chips = []
            chips.append(f'<span class="chip {status_raw}">{status_label}</span>')
            if source_:
                chips.append(f'<span class="chip">{html.escape(source_)}</span>')
            if not sel.get("read"):
                chips.append('<span class="chip new">Neprečítané</span>')
            chips_html = "".join(chips)

            st.markdown(
                f"""
                <div style="display:flex; justify-content: space-between; gap: 1rem; align-items: flex-start;">
                    <div style="min-width: 0;">
                        <div style="font-size: 1.05rem; font-weight: 700; color: {'#f1f5f9' if st.session_state.dark_mode else '#0f172a'}; line-height: 1.25; overflow-wrap: anywhere;">{html.escape(subject)}</div>
                        <div style="margin-top: 0.25rem; display:flex; gap: 0.5rem; flex-wrap: wrap;">{chips_html}</div>
                        <div style="margin-top: 0.45rem; color: {'#94a3b8' if st.session_state.dark_mode else '#64748b'}; font-size: 0.82rem;">Od: {html.escape(from_)}{' · ' + html.escape(time_) if time_ else ''}</div>
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )

            a1, a2, a3, a4 = st.columns([1, 1, 1, 1])
            with a1:
                if st.button("🟠 Priradiť", use_container_width=True):
                    sel["status"] = "assigned"
                    st.rerun()
            with a2:
                if st.button("✅ Hotové", use_container_width=True):
                    sel["status"] = "done"
                    st.rerun()
            with a3:
                if st.button("👤 Vytvoriť klienta", type="primary", use_container_width=True):
                    st.session_state.page = 'new_client'
                    st.rerun()
            with a4:
                if st.button("✉️ Označiť ako neprečítané", use_container_width=True):
                    sel["read"] = False
                    st.rerun()

            st.markdown(
                f'<div class="inbox-detail-body">{html.escape(sel.get("content", "") or "")}</div>',
                unsafe_allow_html=True,
            )
        st.markdown('</div>', unsafe_allow_html=True)


def render_dashboard():
    """Render clean professional dashboard with Bento grid"""
    clients = st.session_state.clients
    stats = get_dashboard_stats(clients)
    today = datetime.now()

    # Czech day/month names
    cz_days = ['Pondělí', 'Úterý', 'Středa', 'Čtvrtek', 'Pátek', 'Sobota', 'Neděle']
    cz_months = ['ledna', 'února', 'března', 'dubna', 'května', 'června', 'července', 'srpna', 'září', 'října', 'listopadu', 'prosince']
    date_str = f"{cz_days[today.weekday()]}, {today.day}. {cz_months[today.month-1]} {today.year}"

    active_clients = [c for c in clients if c.status in ["active", "stagnating"]]
    pending_checkins = len([c for c in active_clients if c.days_since_checkin >= 7])
    sessions_today = min(4, len(active_clients))

    st.markdown(
        f"""
        <div style="margin-top: 0.35rem; margin-bottom: 1.1rem;">
            <h1 class="hero-h1">Dobré ráno, tréner.<br/><span class="accent">Dnes máš {sessions_today} tréningy.</span></h1>
        </div>
        """,
        unsafe_allow_html=True,
    )

    s1, s2, s3, s4 = st.columns(4)
    with s1:
        st.markdown(
            f"""
            <div class="stat-card">
                <div class="stat-top">
                    <div class="stat-label-sm">AKTÍVNI KLIENTI</div>
                    <div class="stat-ico">👥</div>
                </div>
                <div class="stat-value-lg">{len(active_clients)}<span class="stat-chip">+{stats['new_this_week']}</span></div>
            </div>
            """,
            unsafe_allow_html=True,
        )
    with s2:
        st.markdown(
            f"""
            <div class="stat-card">
                <div class="stat-top">
                    <div class="stat-label-sm">TRÉNINGY DNES</div>
                    <div class="stat-ico">🏋️</div>
                </div>
                <div class="stat-value-lg">{sessions_today}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
    with s3:
        st.markdown(
            f"""
            <div class="stat-card">
                <div class="stat-top">
                    <div class="stat-label-sm">ČAKAJÚCE CHECK-INY</div>
                    <div class="stat-ico">⏳</div>
                </div>
                <div class="stat-value-lg">{pending_checkins}<span class="stat-chip warn">Vysoké</span></div>
            </div>
            """,
            unsafe_allow_html=True,
        )
    with s4:
        st.markdown(
            f"""
            <div class="stat-card">
                <div class="stat-top">
                    <div class="stat-label-sm">PRÍJEM (MESIAC)</div>
                    <div class="stat-ico">💳</div>
                </div>
                <div class="stat-value-lg">€{stats['mrr_eur']}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    st.markdown('<div style="height: 0.9rem;"></div>', unsafe_allow_html=True)

    col_main, col_side = st.columns([1.65, 1.0], gap="large")

    with col_main:
        st.markdown(
            """
            <div class="schedule-head">
                <div class="schedule-title">Dnešný rozpis</div>
                <div class="schedule-link">Kalendár</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        base_sessions = [
            ("10:00 AM", "60 min", "HIIT", "In-Person", "accent", "Start Session"),
            ("11:30 AM", "45 min", "Hypertrophy", "Virtual", "purple", "Join Call"),
            ("02:00 PM", "60 min", "Strength", "In-Person", "slate", "Upcoming"),
        ]

        picked = sorted(active_clients, key=lambda c: c.last_checkin, reverse=True)[:3]
        if len(picked) < 3:
            picked = (picked + sorted(clients, key=lambda c: c.last_checkin, reverse=True))[:3]

        for i, c in enumerate(picked[:3]):
            t, dur, plan, mode, tone, cta = base_sessions[i]
            cls = "session-card" + (" purple" if tone == "purple" else " slate" if tone == "slate" else "")
            avatar = _icon_avatar_html(c.name, 46)
            tag2 = '<span class="tag purple">🎥 Virtual</span>' if mode == "Virtual" else '<span class="tag muted">In-Person</span>'
            cta_cls = "session-cta" + (" ghost" if cta == "Join Call" else " disabled" if cta == "Upcoming" else "")
            st.markdown(
                f"""
                <div class="{cls}">
                    <div class="session-left">
                        <div class="session-time"><div class="t">{html.escape(t)}</div><div class="d">{html.escape(dur)}</div></div>
                        <div class="session-avatar">{avatar}</div>
                        <div class="session-meta">
                            <div class="name">{html.escape(c.name)}</div>
                            <div class="session-tags">
                                <span class="tag">{html.escape(plan)}</span>
                                {tag2}
                            </div>
                        </div>
                    </div>
                    <div class="{cta_cls}">{html.escape(cta)}</div>
                </div>
                """,
                unsafe_allow_html=True,
            )

        def _adherence_at_day(c: ClientData, day: datetime) -> int | None:
            if not c.checkins:
                return None
            latest = None
            for ch in sorted(c.checkins, key=lambda x: x.date):
                if ch.date <= day:
                    latest = ch
            if not latest:
                return None
            return int(latest.adherence_percent)

        days = [today - timedelta(days=i) for i in range(6, -1, -1)]
        vals = []
        for d in days:
            per = [v for v in (_adherence_at_day(c, d) for c in active_clients) if v is not None]
            vals.append(round(sum(per) / len(per)) if per else 0)

        compliance_pct = round(sum(vals) / len(vals)) if vals else 0
        pct_width = max(0, min(100, compliance_pct))
        labels = [d.strftime("%a") for d in days]
        max_v = max(vals) if vals else 1
        bars_html = []
        for i, v in enumerate(vals):
            h = 20 + int((v / max_v) * 70) if max_v else 20
            hot = " hot" if i == len(vals) - 2 else ""
            empty = " empty" if v == 0 else ""
            bars_html.append(f'<div class="bar{hot}{empty}" style="height:{h}%"></div>')

        st.markdown(
            f"""
            <div class="compliance-wrap">
                <div class="compliance-head">
                    <div class="ttl">Compliance klientov</div>
                    <div class="pct">{pct_width}%</div>
                </div>
                <div class="progress-track"><div class="progress-fill" style="width:{pct_width}%"></div></div>
                <div class="week-labels">{''.join([f'<span>{html.escape(x)}</span>' for x in labels])}</div>
                <div class="bars">{''.join(bars_html)}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with col_side:
        st.markdown(
            """
            <div class="section-card">
                <div class="section-head">
                    <div class="title">Rýchle akcie</div>
                    <div class="meta">Najčastejšie</div>
                </div>
            """,
            unsafe_allow_html=True,
        )

        st.markdown('<div id="qa-marker"></div>', unsafe_allow_html=True)
        qa1, qa2 = st.columns(2)
        with qa1:
            b1 = st.button("➕\nNew Client", use_container_width=True, key="qa_new_client")
            b3 = st.button("📣\nBroadcast", use_container_width=True, key="qa_broadcast")
        with qa2:
            b2 = st.button("🗓️\nCreate Plan", use_container_width=True, key="qa_create_plan")
            b4 = st.button("📈\nReports", use_container_width=True, key="qa_reports")
        if b1:
            st.session_state.page = "new_client"
            st.rerun()
        if b2:
            st.session_state.page = "new_client"
            st.rerun()
        if b3:
            st.session_state.page = "inbox"
            st.rerun()
        if b4:
            st.session_state.page = "dashboard"
            st.rerun()
        st.markdown("</div>", unsafe_allow_html=True)

        st.markdown('<div style="height: 0.9rem;"></div>', unsafe_allow_html=True)

        st.markdown(
            """
            <div class="section-card">
                <div class="activity-head">
                    <div class="activity-title">Aktivita klientov</div>
                    <div class="activity-meta">Naživo</div>
                </div>
            """,
            unsafe_allow_html=True,
        )

        act_clients = sorted(active_clients, key=lambda x: x.last_checkin, reverse=True)[:3]
        if len(act_clients) < 3:
            act_clients = (act_clients + sorted(clients, key=lambda x: x.last_checkin, reverse=True))[:3]

        if act_clients:
            a0 = act_clients[0]
            st.markdown(
                f"""
                <div class="activity-item highlight">
                    <div class="activity-avatar">{_icon_avatar_html(a0.name, 34)}</div>
                    <div class="activity-body">
                        <div class="line"><b>{html.escape(a0.name.split(' ')[0])}.</b> zaznamenal tréning: <span style="color: var(--accent); font-weight: 900;">Leg Day</span></div>
                        <div class="line" style="color: var(--accent); font-weight: 900; font-size: 0.82rem; margin-top: 0.2rem;">🏆 Personal Record!</div>
                        <div class="time">10 mins ago</div>
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )

        if len(act_clients) > 1:
            a1c = act_clients[1]
            st.markdown(
                f"""
                <div class="activity-item">
                    <div class="activity-avatar">{_icon_avatar_html(a1c.name, 34)}</div>
                    <div class="activity-body">
                        <div class="line"><b>{html.escape(a1c.name.split(' ')[0])}.</b> nahral progres fotky.</div>
                        <div class="time">45 mins ago</div>
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )

        if len(act_clients) > 2:
            a2c = act_clients[2]
            st.markdown(
                f"""
                <div class="activity-item danger">
                    <div class="activity-avatar">{_icon_avatar_html(a2c.name, 34)}</div>
                    <div class="activity-body">
                        <div class="line"><b>{html.escape(a2c.name.split(' ')[0])}.</b> vynechal nutričný log.</div>
                        <div class="activity-cta">Poslať reminder</div>
                        <div class="time">1 hour ago</div>
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )

        st.markdown("</div>", unsafe_allow_html=True)


def render_app_shell():
    dm = st.session_state.dark_mode
    nav_col, content_col = st.columns([0.24, 0.76], gap="large")

    with nav_col:
        nav = st.container()
        with nav:
            st.markdown('<div id="nav-rail-marker"></div>', unsafe_allow_html=True)
            st.markdown(
                """
                <div class="nav-brand">
                    <div class="brand">Fit<span>CRM</span></div>
                </div>
                """,
                unsafe_allow_html=True,
            )

            if st.button("📊  Prehľad", use_container_width=True, type="primary" if st.session_state.page == "dashboard" else "secondary"):
                st.session_state.page = "dashboard"
                st.session_state.selected_client = None
                st.rerun()

            if st.button("👥  Klienti", use_container_width=True, type="primary" if st.session_state.page == "clients" else "secondary"):
                st.session_state.page = "clients"
                st.session_state.selected_client = None
                st.rerun()

            if st.button("📥  Inbox", use_container_width=True, type="primary" if st.session_state.page == "inbox" else "secondary"):
                st.session_state.page = "inbox"
                st.session_state.selected_client = None
                st.rerun()

            if st.button("➕  Nový klient", use_container_width=True, type="primary" if st.session_state.page == "new_client" else "secondary"):
                st.session_state.page = "new_client"
                st.rerun()

            if st.button("⚙️  Email konektor", use_container_width=True, type="primary" if st.session_state.page == "email_connector" else "secondary"):
                st.session_state.page = "email_connector"
                st.rerun()

            trainer_avatar = _icon_avatar_html("Alex Trainer", 40)
            st.markdown(
                f"""
                <div class="nav-user">
                    <div class="uava" style="display:flex; align-items:center; justify-content:center;">{trainer_avatar}</div>
                    <div class="utxt">
                        <div class="n">Alex Trainer</div>
                        <div class="s">Pro Account</div>
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )

            st.markdown('<div style="height: 0.7rem;"></div>', unsafe_allow_html=True)
            sha = _git_sha_short()
            sha_txt = f" · {sha}" if sha else ""
            st.markdown(
                f'<div style="color: var(--muted); font-size: 0.75rem;">v{APP_VERSION}{sha_txt} · {"Tmavý" if dm else "Svetlý"}</div>',
                unsafe_allow_html=True,
            )

    with content_col:
        top = st.container()
        with top:
            st.markdown('<div id="topbar-marker"></div>', unsafe_allow_html=True)

            page_label = {
                "dashboard": "Prehľad",
                "clients": "Klienti",
                "client_detail": "Klient",
                "inbox": "Inbox",
                "new_client": "Nový klient",
                "email_connector": "Email konektor",
            }.get(st.session_state.page, "FitCRM")

            c0, c1, c2, c3, c4, c5 = st.columns([1.25, 2.35, 0.20, 0.85, 0.50, 0.50])
            with c0:
                st.markdown(f'<div class="topbar-title">{html.escape(page_label)}</div>', unsafe_allow_html=True)
                sha = _git_sha_short()
                if sha:
                    st.markdown(f'<div class="topbar-sub">{html.escape(sha)}</div>', unsafe_allow_html=True)
            with c1:
                st.text_input("", placeholder="Hľadať klientov, emaily…", label_visibility="collapsed", key="global_search")
            with c3:
                next_dm = st.toggle("Dark", value=dm, key="top_dark_toggle")
                if next_dm != dm:
                    st.session_state.dark_mode = next_dm
                    st.rerun()
            with c4:
                st.markdown('<div id="topbar-notif-marker"></div>', unsafe_allow_html=True)
                if st.button("🔔", key="top_notif_btn"):
                    st.session_state.show_notifications = not st.session_state.show_notifications
                    if st.session_state.show_notifications:
                        st.session_state.show_user_menu = False
            with c5:
                st.markdown('<div id="topbar-user-marker"></div>', unsafe_allow_html=True)
                if st.button("👤", key="top_user_btn"):
                    st.session_state.show_user_menu = not st.session_state.show_user_menu
                    if st.session_state.show_user_menu:
                        st.session_state.show_notifications = False

        if st.session_state.show_notifications:
            st.markdown(
                """
                <div class="topbar-panel">
                    <div class="ttl">Notifikácie</div>
                    <div class="sub">Demo – posledné udalosti</div>
                </div>
                """,
                unsafe_allow_html=True,
            )
            st.info("Žiadne nové notifikácie (demo).")

        if st.session_state.show_user_menu:
            st.markdown(
                """
                <div class="topbar-panel">
                    <div class="ttl">Účet</div>
                    <div class="sub">Rýchle nastavenia</div>
                </div>
                """,
                unsafe_allow_html=True,
            )
            a1, a2, a3 = st.columns(3)
            with a1:
                st.button("Profil", use_container_width=True, key="user_profile_btn")
            with a2:
                st.button("Nastavenia", use_container_width=True, key="user_settings_btn")
            with a3:
                if st.button("Odhlásiť", use_container_width=True, key="user_logout_btn"):
                    st.session_state.show_user_menu = False
                    st.success("Demo: odhlásenie")

        page = st.session_state.page
        if page == 'dashboard':
            render_dashboard()
        elif page == 'inbox':
            render_inbox()
        elif page == 'clients':
            render_clients_list()
        elif page == 'client_detail':
            render_client_detail()
        elif page == 'new_client':
            render_new_client()
        elif page == 'email_connector':
            render_email_connector()


def render_clients_list():
    """Render client split view (list + detail)"""
    clients = st.session_state.clients
    if not clients:
        st.info("Zatiaľ nemáš žiadnych klientov.")
        return

    if not st.session_state.selected_client:
        st.session_state.selected_client = clients[0].id

    active_count = len([c for c in clients if c.status == "active"])
    risk_count = len([c for c in clients if c.status in ["stagnating", "problem"]])

    left, right = st.columns([0.38, 0.62], gap="large")
    with left:
        st.markdown('<div id="clients-left-marker"></div>', unsafe_allow_html=True)
        q = st.text_input("", placeholder="Hľadať klientov…", label_visibility="collapsed", key="clients_search")

        st.markdown('<div id="clients-add-marker"></div>', unsafe_allow_html=True)
        if st.button("➕  Pridať nového klienta", use_container_width=True, type="primary", key="clients_add_btn"):
            st.session_state.page = "new_client"
            st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)

        st.markdown('<div style="height: 0.6rem;"></div>', unsafe_allow_html=True)

        st.markdown('<div id="clients-chips-marker"></div>', unsafe_allow_html=True)
        ch1, ch2, ch3 = st.columns(3)
        with ch1:
            if st.button("Všetci", use_container_width=True, type="primary" if st.session_state.clients_filter == "all" else "secondary", key="clients_chip_all"):
                st.session_state.clients_filter = "all"
                st.rerun()
        with ch2:
            if st.button(f"Aktívni ({active_count})", use_container_width=True, type="primary" if st.session_state.clients_filter == "active" else "secondary", key="clients_chip_active"):
                st.session_state.clients_filter = "active"
                st.rerun()
        with ch3:
            if st.button(f"Riziko ({risk_count})", use_container_width=True, type="primary" if st.session_state.clients_filter == "risk" else "secondary", key="clients_chip_risk"):
                st.session_state.clients_filter = "risk"
                st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)

        st.markdown('<div style="height: 0.6rem;"></div>', unsafe_allow_html=True)

        filtered = clients
        if q:
            ql = q.lower().strip()
            filtered = [c for c in filtered if ql in (c.name or "").lower() or ql in (c.email or "").lower()]
        if st.session_state.clients_filter == "active":
            filtered = [c for c in filtered if c.status == "active"]
        elif st.session_state.clients_filter == "risk":
            filtered = [c for c in filtered if c.status in ["stagnating", "problem"]]

        filtered = sorted(filtered, key=lambda c: c.last_checkin, reverse=True)

        st.markdown('<div id="clients-list-marker"></div>', unsafe_allow_html=True)
        if not filtered:
            st.caption("Žiadne výsledky.")
        visible = filtered[:60]
        by_id = {c.id: c for c in visible}

        def _fmt(client_id: str) -> str:
            c = by_id.get(client_id)
            if not c:
                return client_id
            dot = {"active": "🟢", "stagnating": "🟡", "problem": "🔴"}.get(c.status, "⚪")
            sub = f"Progres: {c.progress_percent:.0f}% · check-in {c.days_since_checkin}d"
            return f"{dot}  {c.name}\n{sub}"

        sel = st.radio(
            "",
            options=[c.id for c in visible],
            format_func=_fmt,
            label_visibility="collapsed",
            key="clients_left_radio",
        )
        if sel and sel != st.session_state.selected_client:
            st.session_state.selected_client = sel
            st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)

    with right:
        st.markdown('<div id="clients-right-marker"></div>', unsafe_allow_html=True)
        client = next((c for c in clients if c.id == st.session_state.selected_client), None)
        if not client:
            st.info("Vyber klienta zo zoznamu.")
            st.markdown('</div>', unsafe_allow_html=True)
            return

        def _client_upcoming_slots(seed: str):
            h = hashlib.md5((seed or "").encode("utf-8")).hexdigest()
            base = datetime.now().replace(minute=0, second=0, microsecond=0)
            offsets = [1, 3, 6]
            hours = [8, 10, 17, 18, 19]
            out = []
            for i, d in enumerate(offsets):
                dt = base + timedelta(days=d)
                dt = dt.replace(hour=hours[int(h[i], 16) % len(hours)])
                mode = ["Osobne", "Online"][int(h[6 + i], 16) % 2]
                plan = ["Silový tréning", "Hypertrofia", "HIIT", "Mobilita"][int(h[10 + i], 16) % 4]
                mins = [45, 60, 75][int(h[14 + i], 16) % 3]
                out.append((dt, mins, plan, mode))
            return out

        status_raw = (client.status or "").strip().lower()
        status_label = {"active": "Aktívny", "stagnating": "Stagnuje", "problem": "Problém"}.get(status_raw, status_raw)
        avatar = _icon_avatar_html(client.name, 64)

        h1, h2 = st.columns([0.72, 0.28])
        with h1:
            st.markdown(
                f"""
                <div style="display:flex; gap: 0.9rem; align-items: center;">
                    <div style="width:64px; height:64px; border-radius: 18px; border: 1px solid rgba(35,72,47,0.9); overflow:hidden; display:flex; align-items:center; justify-content:center; background: rgba(35,72,47,0.35);">{avatar}</div>
                    <div style="min-width:0;">
                        <div style="font-size: 1.55rem; font-weight: 900; line-height: 1.1; color: var(--text);">{html.escape(client.name)}</div>
                        <div style="margin-top: 0.3rem; display:flex; gap: 0.5rem; flex-wrap: wrap;">
                            <span class="chip {status_raw}">{html.escape(status_label)}</span>
                            <span class="chip">{html.escape(client.email)}</span>
                        </div>
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )
        with h2:
            b1, b2, b3 = st.columns([1, 1, 2])
            with b1:
                st.button("💬", use_container_width=True, key="client_chat_demo")
            with b2:
                st.button("✏️", use_container_width=True, key="client_edit_demo")
            with b3:
                st.button("▶️  Spustiť tréning", use_container_width=True, key="client_start_demo")

        m1, m2, m3 = st.columns(3)
        with m1:
            st.metric("Váha", f"{client.current_weight_kg} kg", delta=f"{client.weight_change:+.1f} kg")
        with m2:
            st.metric("BMI", f"{client.bmi:.1f}")
        with m3:
            st.metric("Check-in", f"{client.days_since_checkin} dní")

        tabs = st.tabs(["Prehľad", "Tréningový plán", "Výživa", "Fotky", "História"])
        with tabs[0]:
            c1, c2 = st.columns([0.42, 0.58], gap="large")
            with c1:
                st.markdown('<div class="section-card">', unsafe_allow_html=True)
                st.markdown('<div class="section-head"><div class="title">Osobné údaje</div><div class="meta">Edit</div></div>', unsafe_allow_html=True)
                st.markdown(f"<div style='color: var(--muted); font-weight: 800; font-size: 0.8rem;'>Email</div><div style='color: var(--text); font-weight: 900; margin-bottom: 0.65rem;'>{html.escape(client.email)}</div>", unsafe_allow_html=True)
                st.markdown(f"<div style='color: var(--muted); font-weight: 800; font-size: 0.8rem;'>Vek</div><div style='color: var(--text); font-weight: 900; margin-bottom: 0.65rem;'>{client.age} rokov</div>", unsafe_allow_html=True)
                st.markdown(f"<div style='color: var(--muted); font-weight: 800; font-size: 0.8rem;'>Výška</div><div style='color: var(--text); font-weight: 900;'>{client.height_cm} cm</div>", unsafe_allow_html=True)
                st.markdown('</div>', unsafe_allow_html=True)
            with c2:
                st.markdown('<div class="section-card">', unsafe_allow_html=True)
                st.markdown('<div class="section-head"><div class="title">Vývoj váhy</div><div class="meta">Posledné check-iny</div></div>', unsafe_allow_html=True)
                if client.checkins:
                    dates = [c.date for c in client.checkins]
                    weights = [c.weight_kg for c in client.checkins]
                    fig = go.Figure()
                    fig.add_trace(go.Scatter(x=dates, y=weights, mode='lines+markers', line=dict(color='#13ec5b', width=3), marker=dict(size=7, color='#13ec5b')))
                    fig.update_layout(height=260, margin=dict(t=10, b=20, l=10, r=10), paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', showlegend=False)
                    st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})
                else:
                    st.caption("Zatiaľ bez check-inov.")
                st.markdown('</div>', unsafe_allow_html=True)

            st.markdown('<div style="height: 0.9rem;"></div>', unsafe_allow_html=True)
            st.markdown('<div class="section-card">', unsafe_allow_html=True)
            st.markdown('<div class="section-head"><div class="title">Nadchádzajúci rozpis</div><div class="meta">7 dní</div></div>', unsafe_allow_html=True)
            slots = _client_upcoming_slots(client.id + client.name)
            for dt, mins, plan, mode in slots:
                when = dt.strftime("%a %d.%m %H:%M")
                st.markdown(
                    f"""
                    <div style="display:flex; align-items:center; justify-content:space-between; gap: 1rem; padding: 0.7rem 0.75rem; border: 1px solid rgba(35,72,47,0.75); border-radius: 14px; background: rgba(35,72,47,0.38); margin-bottom: 0.55rem;">
                        <div style="min-width:0;">
                            <div style="color: var(--text); font-weight: 900;">{html.escape(plan)}</div>
                            <div style="color: var(--muted); font-weight: 800; font-size: 0.85rem; margin-top: 0.1rem;">{html.escape(when)} · {mins} min · {html.escape(mode)}</div>
                        </div>
                        <div style="color: var(--accent); font-weight: 900;">Pripraviť</div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )
            st.markdown('</div>', unsafe_allow_html=True)
        with tabs[1]:
            st.info("Tréningový plán – demo (príde ďalej).")
        with tabs[2]:
            st.info("Výživa – demo (príde ďalej).")
        with tabs[3]:
            st.info("Fotky – demo (príde ďalej).")
        with tabs[4]:
            st.markdown('<div class="section-card">', unsafe_allow_html=True)
            st.markdown('<div class="section-head"><div class="title">História tréningov</div><div class="meta">z check-inov</div></div>', unsafe_allow_html=True)
            if not client.checkins:
                st.caption("Zatiaľ bez záznamov.")
                st.markdown('</div>', unsafe_allow_html=True)
            else:
                hist = sorted(client.checkins, key=lambda x: x.date, reverse=True)[:10]
                st.markdown(
                    """
                    <div style="overflow:auto; border: 1px solid rgba(35,72,47,0.75); border-radius: 14px;">
                    <table style="width:100%; border-collapse: collapse;">
                        <thead>
                            <tr style="background: rgba(35,72,47,0.55);">
                                <th style="text-align:left; padding: 0.65rem 0.7rem; color: var(--muted); font-size: 0.78rem; letter-spacing: 0.08em; text-transform: uppercase;">Dátum</th>
                                <th style="text-align:left; padding: 0.65rem 0.7rem; color: var(--muted); font-size: 0.78rem; letter-spacing: 0.08em; text-transform: uppercase;">Váha</th>
                                <th style="text-align:left; padding: 0.65rem 0.7rem; color: var(--muted); font-size: 0.78rem; letter-spacing: 0.08em; text-transform: uppercase;">Adherence</th>
                                <th style="text-align:left; padding: 0.65rem 0.7rem; color: var(--muted); font-size: 0.78rem; letter-spacing: 0.08em; text-transform: uppercase;">Tréningy</th>
                            </tr>
                        </thead>
                        <tbody>
                    """,
                    unsafe_allow_html=True,
                )
                for r in hist:
                    d = r.date.strftime("%d.%m.%Y")
                    w = f"{r.weight_kg:.1f} kg"
                    adh = f"{r.adherence_percent}%"
                    wo = f"{r.workouts_completed}/{r.workouts_planned}"
                    st.markdown(
                        f"""
                        <tr>
                            <td style="padding: 0.65rem 0.7rem; border-top: 1px solid rgba(35,72,47,0.65); color: var(--text); font-weight: 900;">{html.escape(d)}</td>
                            <td style="padding: 0.65rem 0.7rem; border-top: 1px solid rgba(35,72,47,0.65); color: var(--text); font-weight: 900;">{html.escape(w)}</td>
                            <td style="padding: 0.65rem 0.7rem; border-top: 1px solid rgba(35,72,47,0.65); color: var(--text); font-weight: 900;">{html.escape(adh)}</td>
                            <td style="padding: 0.65rem 0.7rem; border-top: 1px solid rgba(35,72,47,0.65); color: var(--text); font-weight: 900;">{html.escape(wo)}</td>
                        </tr>
                        """,
                        unsafe_allow_html=True,
                    )
                st.markdown("</tbody></table></div>", unsafe_allow_html=True)
                st.markdown('</div>', unsafe_allow_html=True)

        st.markdown('</div>', unsafe_allow_html=True)


def render_client_detail():
    """Render detailed client view"""
    client_id = st.session_state.selected_client
    client = next((c for c in st.session_state.clients if c.id == client_id), None)

    if not client:
        st.error("Klient nenájdený")
        return

    # Back button
    if st.button("← Späť na zoznam"):
        st.session_state.page = 'clients'
        st.session_state.selected_client = None
        st.rerun()

    status_raw = (client.status or "").strip().lower()
    status_label = {"active": "Aktívny", "stagnating": "Stagnuje", "problem": "Problém"}.get(status_raw, status_raw)
    avatar = _icon_avatar_html(client.name, 44)
    chips = [f'<span class="chip {status_raw}">{html.escape(status_label)}</span>']
    chips.append(f'<span class="chip">{html.escape(client.email)}</span>')
    st.markdown(
        f"""
        <div class="bento-card" style="padding: 0.95rem; margin-bottom: 1rem;">
            <div style="display:flex; gap: 0.9rem; align-items: center;">
                <div style="width:44px; height:44px; border-radius: 12px; border: 1px solid rgba(35,72,47,0.9); overflow:hidden; display:flex; align-items:center; justify-content:center; background: rgba(35,72,47,0.35);">{avatar}</div>
                <div style="min-width: 0;">
                    <div style="font-size: 1.25rem; font-weight: 800; line-height: 1.15; color: {'#f1f5f9' if st.session_state.dark_mode else '#0f172a'};">{html.escape(client.name)}</div>
                    <div style="margin-top: 0.35rem; display:flex; gap: 0.5rem; flex-wrap: wrap;">{''.join(chips)}</div>
                </div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # Client Info Row
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Vek", f"{client.age} rokov")
    with col2:
        st.metric("Výška", f"{client.height_cm} cm")
    with col3:
        st.metric("BMI", f"{client.bmi:.1f}")
    with col4:
        status_text = {"active": "✅ Aktívny", "stagnating": "⚠️ Stagnuje", "problem": "🔴 Problém"}.get(client.status)
        st.metric("Status", status_text)

    st.markdown("---")

    # Weight Progress Section
    col1, col2 = st.columns([2, 1])

    with col1:
        st.markdown("### 📈 Vývoj váhy")

        if client.checkins:
            dates = [c.date for c in client.checkins]
            weights = [c.weight_kg for c in client.checkins]

            fig = go.Figure()
            fig.add_trace(go.Scatter(
                x=dates, y=weights,
                mode='lines+markers',
                name='Váha',
                line=dict(color='#3498db', width=3),
                marker=dict(size=8)
            ))

            # Add goal line
            fig.add_hline(y=client.goal_weight_kg, line_dash="dash",
                          line_color="#27ae60", annotation_text="Cieľ")

            fig.update_layout(
                height=300,
                margin=dict(t=10, b=30, l=10, r=10),
                yaxis_title="Váha (kg)",
                showlegend=False
            )
            st.plotly_chart(fig, use_container_width=True)

    with col2:
        st.markdown("### 🎯 Progres k cieľu")

        st.metric("Štart", f"{client.initial_weight_kg} kg")
        st.metric("Teraz", f"{client.current_weight_kg} kg", delta=f"{client.weight_change:+.1f} kg")
        st.metric("Cieľ", f"{client.goal_weight_kg} kg")

        st.markdown("---")
        progress = client.progress_percent
        st.write(f"**Progres: {progress:.0f}%**")
        st.progress(progress / 100)

        remaining = abs(client.current_weight_kg - client.goal_weight_kg)
        st.caption(f"Zostáva: {remaining:.1f} kg")

    st.markdown("---")

    # Exercise Progress Section
    col1, col2 = st.columns(2)

    with col1:
        st.markdown("### 💪 Progres v cvikoch")

        if client.exercises:
            exercise_names = [e.name for e in client.exercises]
            initial = [e.initial_weight_kg for e in client.exercises]
            current = [e.current_weight_kg for e in client.exercises]

            fig = go.Figure()
            fig.add_trace(go.Bar(
                name='Štart',
                x=exercise_names,
                y=initial,
                marker_color='#bdc3c7'
            ))
            fig.add_trace(go.Bar(
                name='Teraz',
                x=exercise_names,
                y=current,
                marker_color='#3498db'
            ))

            fig.update_layout(
                barmode='group',
                height=350,
                margin=dict(t=10, b=30, l=30, r=10),
                yaxis_title="Váha (kg)",
                legend=dict(orientation="h", yanchor="bottom", y=1.02)
            )
            st.plotly_chart(fig, use_container_width=True)

    with col2:
        st.markdown("### 📊 Adherencia k plánu")

        if client.checkins:
            adherence_data = [c.adherence_percent for c in client.checkins]
            dates = [c.date for c in client.checkins]

            fig = go.Figure()
            fig.add_trace(go.Scatter(
                x=dates, y=adherence_data,
                mode='lines+markers',
                name='Adherencia %',
                line=dict(color='#27ae60', width=2),
                fill='tozeroy',
                fillcolor='rgba(39, 174, 96, 0.2)'
            ))

            fig.update_layout(
                height=350,
                margin=dict(t=10, b=30, l=30, r=10),
                yaxis_title="Adherencia (%)",
                yaxis=dict(range=[0, 100])
            )
            st.plotly_chart(fig, use_container_width=True)

    st.markdown("---")

    # Check-in History
    st.markdown("### 📅 História check-inov")

    if client.checkins:
        for checkin in reversed(client.checkins[-5:]):
            mood_emoji = {"excellent": "😊", "good": "🙂", "ok": "😐", "bad": "😕"}.get(checkin.mood, "😐")
            col1, col2, col3, col4 = st.columns([2, 2, 2, 2])

            with col1:
                st.write(f"**{checkin.date.strftime('%d.%m.%Y')}**")
            with col2:
                st.write(f"⚖️ {checkin.weight_kg} kg")
            with col3:
                st.write(f"{mood_emoji} {checkin.adherence_percent}% adherencia")
            with col4:
                st.write(f"🏋️ {checkin.workouts_completed}/{checkin.workouts_planned} tréningov")

    st.markdown("---")

    # Actions
    st.markdown("### ⚡ Akcie")
    col1, col2, col3 = st.columns(3)

    with col1:
        if st.button("📧 Odoslať správu", use_container_width=True):
            st.info("Funkcia bude dostupná v ďalšej verzii")

    with col2:
        if st.button("📝 Upraviť plán", use_container_width=True):
            st.info("Funkcia bude dostupná v ďalšej verzii")

    with col3:
        if st.button("🔄 Vygenerovať nový plán", use_container_width=True):
            st.session_state.page = 'new_client'
            st.session_state.profile = ClientProfile(
                name=client.name,
                email=client.email,
                age=client.age,
                gender=client.gender,
                weight=client.current_weight_kg,
                height=client.height_cm,
                goal=client.goal,
                experience_level=client.experience_level
            )
            st.rerun()


def render_new_client():
    """Render new client / plan generator page"""
    st.markdown('<div class="main-header">➕ Nový klient / Generovať plán</div>', unsafe_allow_html=True)

    # Show selected ticket info if any
    selected_ticket = st.session_state.get('selected_ticket')
    if selected_ticket:
        st.info(f"📬 **Ticket:** {selected_ticket['subject']} ({selected_ticket['from']})")

    profile = st.session_state.get('profile')

    if st.session_state.get('meal_plan') and st.session_state.get('training_plan'):
        render_generated_plans()
        return

    if profile:
        st.success(f"✅ Klient: **{profile.name}** ({profile.email})")

        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Vek", f"{profile.age} rokov")
        with col2:
            st.metric("Váha", f"{profile.weight} kg")
        with col3:
            st.metric("Výška", f"{profile.height} cm")
        with col4:
            st.metric("Pohlavie", "Muž" if profile.gender == "male" else "Žena")

        st.info(f"**Cieľ:** {profile.goal}")

        st.markdown("---")

        # Mode selection
        st.markdown("### ⚙️ Režim generovania")
        col1, col2 = st.columns(2)
        with col1:
            mode = st.radio(
                "Vyber režim:",
                ["🤖 Plne automatický", "✏️ Polo-automatický"],
                index=0 if st.session_state.generation_mode == 'auto' else 1,
                help="Polo-automatický režim ti umožní upraviť vygenerované plány pred finalizáciou"
            )
            st.session_state.generation_mode = 'auto' if mode == "🤖 Plne automatický" else 'semi'

        with col2:
            st.markdown("""
            **Plne automatický:** AI vygeneruje kompletné plány

            **Polo-automatický:** AI vygeneruje návrh, ktorý môžeš upraviť
            """)

        st.markdown("---")

        col1, col2 = st.columns(2)
        with col1:
            if st.button("🚀 Generovať plány", type="primary", use_container_width=True):
                api_key = get_api_key()
                if not api_key:
                    st.error("❌ Gemini API kľúč nie je nastavený")
                else:
                    generate_plans(profile, api_key)

        with col2:
            if st.button("🔄 Zmeniť údaje", use_container_width=True):
                st.session_state.profile = None
                st.session_state.selected_ticket = None
                st.rerun()
    else:
        render_client_form()


def render_client_form():
    """Render client input form"""
    tab1, tab2 = st.tabs(["📧 Vložiť email", "✍️ Manuálne zadanie"])

    with tab1:
        # Pre-fill with selected ticket content if available
        default_email = ""
        selected_ticket = st.session_state.get('selected_ticket')
        if selected_ticket:
            default_email = selected_ticket.get('content', '')

        email_text = st.text_area(
            "Email od klienta",
            value=default_email,
            height=250,
            placeholder="Vlož email od klienta..."
        )

        if st.button("📋 Parsovať email", type="primary", use_container_width=True):
            if email_text.strip():
                try:
                    parser = EmailParser()
                    profile = parser.parse_email(email_text)
                    st.session_state.profile = profile
                    st.rerun()
                except Exception as e:
                    st.error(f"❌ Chyba: {e}")

    with tab2:
        col1, col2 = st.columns(2)

        with col1:
            name = st.text_input("Meno a priezvisko*")
            email = st.text_input("Email*")
            age = st.number_input("Vek*", min_value=15, max_value=100, value=30)
            gender = st.selectbox("Pohlavie*", ["Muž", "Žena"])

        with col2:
            weight = st.number_input("Váha (kg)*", min_value=30.0, max_value=250.0, value=80.0)
            height = st.number_input("Výška (cm)*", min_value=100.0, max_value=250.0, value=175.0)
            goal = st.text_area("Cieľ*", placeholder="Napr: Schudnúť 10 kg")
            experience = st.selectbox("Skúsenosti", ["Začiatočník", "Mierne pokročilý", "Pokročilý"])

        if st.button("💾 Uložiť a pokračovať", type="primary", use_container_width=True):
            if name and email and goal:
                exp_map = {"Začiatočník": "beginner", "Mierne pokročilý": "intermediate", "Pokročilý": "advanced"}
                profile = ClientProfile(
                    name=name, email=email, age=age,
                    gender="male" if gender == "Muž" else "female",
                    weight=weight, height=height, goal=goal,
                    experience_level=exp_map.get(experience, "beginner")
                )
                st.session_state.profile = profile
                st.rerun()
            else:
                st.error("❌ Vyplň všetky povinné polia")


def generate_plans(profile: ClientProfile, api_key: str):
    """Generate meal and training plans - sequential with delays"""
    import time
    
    progress = st.progress(0)
    status = st.empty()
    error_container = st.empty()

    try:
        status.text("🔄 Pripájam sa k Gemini API...")
        progress.progress(10)

        ai = FitAIGenerator(api_key=api_key)

        # Step 1: Segment client (1 API request)
        status.text("📊 Analyzujem profil... (1/3)")
        progress.progress(20)
        segment = ai.segment_client(profile)
        st.session_state.segment = segment
        progress.progress(33)

        # Step 2: Generate meal plan (1 API request)
        status.text("🍽️ Generujem jedálniček... (2/3)")
        progress.progress(45)
        meal_plan = ai.generate_meal_plan(profile, segment)
        st.session_state.meal_plan = meal_plan
        progress.progress(66)

        # Step 3: Generate training plan (1 API request)
        status.text("💪 Generujem tréningový plán... (3/3)")
        progress.progress(80)
        training_plan = ai.generate_training_plan(profile, segment)
        st.session_state.training_plan = training_plan

        # For semi-auto mode, also store editable versions
        if st.session_state.generation_mode == 'semi':
            st.session_state.editable_meal_plan = meal_plan
            st.session_state.editable_training_plan = training_plan

        progress.progress(100)
        status.text("✅ Hotovo!")
        st.balloons()
        st.rerun()

    except Exception as e:
        error_msg = str(e)
        if "429" in error_msg or "quota" in error_msg.lower():
            error_container.error(f"❌ Rate limit - počkajte 60 sekúnd a skúste znova")
        else:
            error_container.error(f"❌ Chyba: {e}")


def render_generated_plans():
    """Render generated plans with improved formatting"""
    profile = st.session_state.profile
    segment = st.session_state.segment
    meal_plan = st.session_state.meal_plan
    training_plan = st.session_state.training_plan
    is_semi_mode = st.session_state.generation_mode == 'semi'

    st.success(f"✅ Plány vygenerované pre: **{profile.name}**")

    # Macro overview in styled cards
    st.markdown("### 📊 Denné makrá")
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.markdown(f"""
        <div class="nutrition-card" style="text-align: center;">
            <div class="nutrition-value">{segment.calorie_target}</div>
            <div class="nutrition-label">kcal / deň</div>
        </div>
        """, unsafe_allow_html=True)
    with col2:
        st.markdown(f"""
        <div class="nutrition-card" style="text-align: center; background: linear-gradient(135deg, #ffebee 0%, #ffcdd2 100%);">
            <div class="nutrition-value" style="color: #c62828;">{segment.protein_grams}g</div>
            <div class="nutrition-label" style="color: #c62828;">Bielkoviny</div>
        </div>
        """, unsafe_allow_html=True)
    with col3:
        st.markdown(f"""
        <div class="nutrition-card" style="text-align: center; background: linear-gradient(135deg, #fff3e0 0%, #ffe0b2 100%);">
            <div class="nutrition-value" style="color: #ef6c00;">{segment.carbs_grams}g</div>
            <div class="nutrition-label" style="color: #ef6c00;">Sacharidy</div>
        </div>
        """, unsafe_allow_html=True)
    with col4:
        st.markdown(f"""
        <div class="nutrition-card" style="text-align: center; background: linear-gradient(135deg, #e3f2fd 0%, #bbdefb 100%);">
            <div class="nutrition-value" style="color: #1565c0;">{segment.fat_grams}g</div>
            <div class="nutrition-label" style="color: #1565c0;">Tuky</div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("---")

    # Mode indicator
    if is_semi_mode:
        st.info("✏️ **Polo-automatický režim** - Môžeš upraviť plány pred uložením")

    tab1, tab2, tab3 = st.tabs(["🍽️ Jedálniček", "💪 Tréningový plán", "📊 Nutričná analýza"])

    with tab1:
        st.markdown('<div class="plan-section">', unsafe_allow_html=True)
        st.markdown('<div class="plan-header">🍽️ Týždenný jedálniček</div>', unsafe_allow_html=True)

        if is_semi_mode:
            # Editable text area for semi-auto mode
            edited_meal = st.text_area(
                "Uprav jedálniček:",
                value=st.session_state.editable_meal_plan or meal_plan,
                height=400,
                key="meal_editor"
            )
            st.session_state.editable_meal_plan = edited_meal
            display_meal = edited_meal
        else:
            display_meal = meal_plan

        # Render the plan with better formatting
        render_formatted_plan(display_meal, "meal")
        st.markdown('</div>', unsafe_allow_html=True)

        # PDF download
        col1, col2 = st.columns(2)
        with col1:
            try:
                pdf_gen = PDFGenerator()
                with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as tmp:
                    if pdf_gen.generate_pdf(display_meal, tmp.name, f"Jedálniček - {profile.name}"):
                        with open(tmp.name, "rb") as f:
                            st.download_button("📥 Stiahnuť PDF", f.read(),
                                               f"jedalnicky_{profile.name.replace(' ', '_')}.pdf",
                                               "application/pdf", use_container_width=True)
                    else:
                        st.warning("⚠️ PDF sa nepodarilo vygenerovať")
            except Exception as e:
                st.error(f"❌ Chyba PDF: {e}")

    with tab2:
        st.markdown('<div class="plan-section">', unsafe_allow_html=True)
        st.markdown('<div class="plan-header">💪 Tréningový plán</div>', unsafe_allow_html=True)

        if is_semi_mode:
            edited_training = st.text_area(
                "Uprav tréningový plán:",
                value=st.session_state.editable_training_plan or training_plan,
                height=400,
                key="training_editor"
            )
            st.session_state.editable_training_plan = edited_training
            display_training = edited_training
        else:
            display_training = training_plan

        render_formatted_plan(display_training, "training")
        st.markdown('</div>', unsafe_allow_html=True)

        col1, col2 = st.columns(2)
        with col1:
            try:
                pdf_gen = PDFGenerator()
                with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as tmp:
                    if pdf_gen.generate_pdf(display_training, tmp.name, f"Tréning - {profile.name}"):
                        with open(tmp.name, "rb") as f:
                            st.download_button("📥 Stiahnuť PDF", f.read(),
                                               f"trening_{profile.name.replace(' ', '_')}.pdf",
                                               "application/pdf", use_container_width=True)
                    else:
                        st.warning("⚠️ PDF sa nepodarilo vygenerovať")
            except Exception as e:
                st.error(f"❌ Chyba PDF: {e}")

    with tab3:
        render_nutrition_analysis(segment)

    st.markdown("---")

    # Action buttons
    col1, col2, col3 = st.columns(3)
    with col1:
        if st.button("✅ Uložiť a dokončiť", type="primary", use_container_width=True):
            # Mark ticket as done
            if st.session_state.get('selected_ticket'):
                for t in st.session_state.email_tickets:
                    if t['id'] == st.session_state.selected_ticket['id']:
                        t['status'] = 'done'
                        break
            st.success("✅ Plány uložené!")

    with col2:
        if st.button("📧 Odoslať klientovi", use_container_width=True):
            email_user = os.getenv('EMAIL_USER', '')
            email_pass = os.getenv('EMAIL_PASS', '')
            
            if not email_user or not email_pass:
                st.error("❌ Email credentials nie sú nastavené v .env súbore")
            else:
                try:
                    from src.email_sender import EmailSender
                    sender = EmailSender(
                        smtp_host=os.getenv('SMTP_HOST', 'smtp.gmail.com'),
                        smtp_port=int(os.getenv('SMTP_PORT', '587')),
                        username=email_user,
                        password=email_pass
                    )
                    
                    # Generate PDFs to temp files
                    pdf_gen = PDFGenerator()
                    meal_pdf_path = None
                    training_pdf_path = None
                    
                    with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as tmp:
                        if pdf_gen.generate_pdf(meal_plan, tmp.name, f"Jedálniček - {profile.name}"):
                            meal_pdf_path = Path(tmp.name)
                    
                    with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as tmp:
                        if pdf_gen.generate_pdf(training_plan, tmp.name, f"Tréning - {profile.name}"):
                            training_pdf_path = Path(tmp.name)
                    
                    trainer_name = os.getenv('TRAINER_NAME', 'Tvoj Tréner')
                    
                    with st.spinner("📧 Odosielam email..."):
                        success = sender.send_welcome_email(
                            to_email=profile.email,
                            client_name=profile.name,
                            meal_plan_pdf=meal_pdf_path,
                            training_plan_pdf=training_pdf_path,
                            trainer_name=trainer_name
                        )
                    
                    if success:
                        st.success(f"✅ Email odoslaný na: {profile.email}")
                    else:
                        st.error("❌ Nepodarilo sa odoslať email")
                        
                except Exception as e:
                    st.error(f"❌ Chyba pri odosielaní: {e}")

    with col3:
        if st.button("🔄 Nový klient", use_container_width=True):
            st.session_state.profile = None
            st.session_state.segment = None
            st.session_state.meal_plan = None
            st.session_state.training_plan = None
            st.session_state.selected_ticket = None
            st.session_state.editable_meal_plan = None
            st.session_state.editable_training_plan = None
            st.rerun()


def render_formatted_plan(plan_text: str, plan_type: str):
    """Render plan with better visual formatting"""
    # Display the markdown content in a styled container
    st.markdown(plan_text)


def render_nutrition_analysis(segment):
    """Render nutrition analysis tab"""
    st.markdown("### 📊 Nutričná analýza")

    # Macro distribution pie chart
    col1, col2 = st.columns(2)

    with col1:
        st.markdown("#### Rozloženie makroživín")
        protein_cal = segment.protein_grams * 4
        carbs_cal = segment.carbs_grams * 4
        fat_cal = segment.fat_grams * 9

        fig = go.Figure(data=[go.Pie(
            labels=['Bielkoviny', 'Sacharidy', 'Tuky'],
            values=[protein_cal, carbs_cal, fat_cal],
            hole=.4,
            marker_colors=['#c62828', '#ef6c00', '#1565c0'],
            textinfo='label+percent'
        )])
        fig.update_layout(
            showlegend=True,
            height=300,
            margin=dict(t=20, b=20, l=20, r=20)
        )
        st.plotly_chart(fig, use_container_width=True)

    with col2:
        st.markdown("#### Denný prehľad")
        st.markdown(f"""
        | Makroživina | Množstvo | Kalórie |
        |-------------|----------|---------|
        | 🥩 Bielkoviny | {segment.protein_grams}g | {segment.protein_grams * 4} kcal |
        | 🍞 Sacharidy | {segment.carbs_grams}g | {segment.carbs_grams * 4} kcal |
        | 🥑 Tuky | {segment.fat_grams}g | {segment.fat_grams * 9} kcal |
        | **Celkom** | - | **{segment.calorie_target} kcal** |
        """)

    # Nutrition lookup
    st.markdown("---")
    st.markdown("#### 🔍 Vyhľadať nutričné hodnoty")
    st.caption("Zadaj jedlo pre získanie nutričných hodnôt z API")

    col1, col2 = st.columns([3, 1])
    with col1:
        food_query = st.text_input("Jedlo", placeholder="napr. 100g chicken breast", label_visibility="collapsed")
    with col2:
        search_clicked = st.button("🔍 Hľadať", use_container_width=True)

    if search_clicked and food_query:
        with st.spinner("Načítavam nutričné údaje..."):
            nutrition_data = fetch_nutrition_info(food_query)

        if nutrition_data:
            st.success(f"✅ Výsledky pre: **{food_query}**")

            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric("Kalórie", f"{nutrition_data['calories']:.0f} kcal")
            with col2:
                st.metric("Bielkoviny", f"{nutrition_data['protein_g']:.1f}g")
            with col3:
                st.metric("Sacharidy", f"{nutrition_data['carbs_g']:.1f}g")
            with col4:
                st.metric("Tuky", f"{nutrition_data['fat_g']:.1f}g")

            # Show detailed items
            if nutrition_data.get('items'):
                with st.expander("📋 Detailný rozpis"):
                    for item in nutrition_data['items']:
                        st.markdown(f"""
                        **{item.get('name', 'N/A')}** ({item.get('serving_size_g', 'N/A')}g)
                        - Kalórie: {item.get('calories', 0)} | Bielkoviny: {item.get('protein_g', 0)}g
                        - Sacharidy: {item.get('carbohydrates_total_g', 0)}g | Tuky: {item.get('fat_total_g', 0)}g
                        """)
        else:
            nutrition_api_key = get_nutrition_api_key()
            if not nutrition_api_key:
                st.warning("⚠️ Nutrition API kľúč nie je nastavený. Pridaj NUTRITION_API_KEY do secrets.")
            else:
                st.warning("⚠️ Nepodarilo sa nájsť nutričné údaje")


def main():
    """Main application"""
    init_session_state()

    # Apply dark mode CSS if enabled
    dark_css = get_theme_css(st.session_state.dark_mode)
    if dark_css:
        st.markdown(f"<style>{dark_css}</style>", unsafe_allow_html=True)

    render_app_shell()


if __name__ == "__main__":
    main()

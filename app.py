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
            --surface-1: #112217;
            --surface-2: #172d20;
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
        background: var(--surface-1);
        border: 1px solid var(--border);
        border-radius: 18px;
        padding: 0.9rem;
        height: calc(100vh - 2.0rem);
        position: sticky;
        top: 0.9rem;
        overflow: hidden;
    }

    div[data-testid="stVerticalBlock"]:has(#nav-rail-marker) div.stButton > button {
        width: 100%;
        border-radius: 14px !important;
        border: 1px solid transparent !important;
        background: transparent !important;
        color: var(--text) !important;
        padding: 0.7rem 0.8rem !important;
        font-weight: 600 !important;
        text-align: left !important;
    }

    div[data-testid="stVerticalBlock"]:has(#nav-rail-marker) div.stButton > button:hover {
        background: var(--surface-2) !important;
        border-color: var(--border) !important;
    }

    div[data-testid="stVerticalBlock"]:has(#nav-rail-marker) div.stButton > button[kind="primary"] {
        background: var(--accent-2) !important;
        border-color: rgba(19, 236, 91, 0.45) !important;
        color: var(--text) !important;
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
        background: var(--surface-1);
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
        background: #ffffff;
        border: 1px solid #e2e8f0;
        border-radius: 16px;
        padding: 1.25rem;
        box-shadow: 0 1px 3px rgba(0, 0, 0, 0.05);
        transition: all 0.2s ease;
    }

    .bento-card:hover {
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.08);
        border-color: #cbd5e1;
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
        color: #0f172a;
        margin: 0;
        line-height: 1.2;
    }

    .hero-subtitle {
        font-size: 0.95rem;
        font-weight: 400;
        color: #64748b;
        margin-top: 0.25rem;
    }

    .stat-value {
        font-size: 2.5rem;
        font-weight: 700;
        letter-spacing: -0.02em;
        line-height: 1;
        margin-bottom: 0.25rem;
        color: #0f172a;
    }

    .stat-value.blue { color: #2563eb; }
    .stat-value.emerald { color: #059669; }
    .stat-value.slate { color: #0f172a; }
    .stat-value.amber { color: #d97706; }

    .stat-label {
        font-size: 0.8rem;
        font-weight: 500;
        color: #64748b;
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
        background: #ecfdf5;
        color: #059669;
    }

    .trend-down {
        background: #fef2f2;
        color: #dc2626;
    }

    .trend-neutral {
        background: #f1f5f9;
        color: #64748b;
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

    .section-icon.blue { background: #eff6ff; color: #2563eb; }
    .section-icon.emerald { background: #ecfdf5; color: #059669; }
    .section-icon.amber { background: #fffbeb; color: #d97706; }
    .section-icon.red { background: #fef2f2; color: #dc2626; }

    .section-title {
        font-size: 0.95rem;
        font-weight: 600;
        color: #0f172a;
        margin: 0;
    }

    /* ===== ACTIVITY LIST ===== */
    .activity-item {
        display: flex;
        align-items: center;
        gap: 0.875rem;
        padding: 0.75rem 0;
        border-bottom: 1px solid #f1f5f9;
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
        color: #0f172a;
        font-size: 0.9rem;
        margin-bottom: 0.125rem;
    }

    .activity-meta {
        font-size: 0.8rem;
        color: #64748b;
    }

    .activity-badge {
        font-size: 0.75rem;
        font-weight: 500;
        padding: 0.25rem 0.625rem;
        border-radius: 9999px;
    }

    .badge-success {
        background: #ecfdf5;
        color: #059669;
    }

    .badge-warning {
        background: #fffbeb;
        color: #d97706;
    }

    .badge-danger {
        background: #fef2f2;
        color: #dc2626;
    }

    /* ===== ALERT CARDS ===== */
    .alert-card {
        background: #fef2f2;
        border: 1px solid #fecaca;
        border-radius: 12px;
        padding: 1rem 1.25rem;
        margin-bottom: 0.75rem;
        display: flex;
        align-items: center;
        gap: 0.875rem;
    }

    .alert-card.warning {
        background: #fffbeb;
        border-color: #fde68a;
    }

    .alert-icon {
        font-size: 1.1rem;
    }

    .alert-text {
        flex: 1;
        color: #374151;
        font-size: 0.875rem;
    }

    .alert-text strong {
        color: #0f172a;
    }

    /* ===== STATS CARD ===== */
    .avatar-card {
        background: linear-gradient(135deg, #eff6ff 0%, #f8fafc 100%);
        border: 1px solid #e2e8f0;
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
        background: radial-gradient(circle, rgba(37, 99, 235, 0.08) 0%, transparent 70%);
        pointer-events: none;
    }

    .avatar-placeholder {
        width: 100px;
        height: 100px;
        background: linear-gradient(135deg, #eff6ff 0%, #dbeafe 100%);
        border-radius: 50%;
        margin: 0 auto 1rem;
        position: relative;
        border: 3px solid #bfdbfe;
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
        color: #059669;
    }

    .avatar-stat-label {
        font-size: 0.7rem;
        color: #64748b;
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
        color: #2563eb;
        margin-bottom: 0.25rem;
    }

    .ring-label {
        font-size: 0.8rem;
        color: #64748b;
    }

    /* ===== BUTTONS ===== */
    .stButton > button {
        background: #2563eb !important;
        color: #ffffff !important;
        border: none !important;
        border-radius: 8px !important;
        font-weight: 500 !important;
        padding: 0.625rem 1.25rem !important;
        transition: all 0.2s ease !important;
    }

    .stButton > button:hover {
        background: #1d4ed8 !important;
        box-shadow: 0 4px 12px rgba(37, 99, 235, 0.25) !important;
    }

    .stButton > button[kind="secondary"] {
        background: #ffffff !important;
        color: #374151 !important;
        border: 1px solid #e5e7eb !important;
    }

    .stButton > button[kind="secondary"]:hover {
        background: #f9fafb !important;
        border-color: #d1d5db !important;
        box-shadow: none !important;
    }

    /* ===== SIDEBAR ===== */
    [data-testid="stSidebar"] {
        background: #ffffff;
        border-right: 1px solid #e2e8f0;
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
        color: #374151;
    }

    /* ===== METRICS OVERRIDE ===== */
    [data-testid="stMetricValue"] {
        font-size: 2rem !important;
        font-weight: 700 !important;
        color: #0f172a !important;
    }

    [data-testid="stMetricDelta"] {
        color: #059669 !important;
    }

    [data-testid="stMetricLabel"] {
        color: #64748b !important;
    }

    /* ===== CHARTS ===== */
    .js-plotly-plot .plotly .modebar {
        display: none !important;
    }

    /* ===== TICKET CARDS ===== */
    .ticket-card {
        background: #ffffff;
        border: 1px solid #e2e8f0;
        border-radius: 8px;
        padding: 0.75rem;
        margin-bottom: 0.5rem;
        transition: all 0.15s ease;
    }

    .ticket-card:hover {
        background: #f8fafc;
        border-color: #cbd5e1;
    }

    .ticket-card.priority-high {
        border-left: 3px solid #dc2626;
    }

    .ticket-card.priority-normal {
        border-left: 3px solid #2563eb;
    }

    .ticket-card .ticket-subject {
        color: #0f172a;
        font-weight: 500;
        font-size: 0.85rem;
    }

    .ticket-card .ticket-meta {
        color: #64748b;
        font-size: 0.7rem;
        margin-top: 0.25rem;
    }

    .chip {
        display: inline-flex;
        align-items: center;
        gap: 0.35rem;
        padding: 0.2rem 0.55rem;
        border-radius: 999px;
        border: 1px solid #e2e8f0;
        font-size: 0.72rem;
        font-weight: 600;
        line-height: 1;
        white-space: nowrap;
    }

    .chip.new { background: #ecfdf5; color: #059669; }
    .chip.assigned { background: #fff7ed; color: #d97706; }
    .chip.done { background: #f1f5f9; color: #475569; }

    .chip.active { background: #ecfdf5; color: #059669; }
    .chip.stagnating { background: #fffbeb; color: #d97706; }
    .chip.problem { background: #fef2f2; color: #dc2626; }

    .avatar-img {
        width: 44px;
        height: 44px;
        border-radius: 12px;
        border: 1px solid #e2e8f0;
        background: #ffffff;
        display: block;
    }

    .inbox-detail-body {
        background: #f8fafc;
        border: 1px solid #e2e8f0;
        border-radius: 12px;
        padding: 0.85rem;
        max-height: 420px;
        overflow: auto;
        white-space: pre-wrap;
        font-size: 0.9rem;
        line-height: 1.35;
        color: #0f172a;
    }

    .inbox-item {
        border: 1px solid #e2e8f0;
        border-radius: 12px;
        padding: 0.65rem 0.75rem;
        background: #ffffff;
        margin-bottom: 0.5rem;
    }

    .inbox-item.selected {
        border-color: #93c5fd;
        background: #eff6ff;
    }

    .inbox-item-title {
        font-weight: 700;
        font-size: 0.95rem;
        color: #0f172a;
        line-height: 1.25;
    }

    .inbox-item-meta {
        display: flex;
        justify-content: space-between;
        gap: 0.75rem;
        margin-top: 0.25rem;
        color: #64748b;
        font-size: 0.8rem;
    }

    .inbox-item-snippet {
        margin-top: 0.35rem;
        color: #475569;
        font-size: 0.82rem;
        line-height: 1.25;
    }

    /* ===== LEGACY OVERRIDES ===== */
    .main-header {
        font-size: 1.5rem;
        font-weight: 600;
        color: #0f172a;
        letter-spacing: -0.01em;
        margin-bottom: 1rem;
    }

    hr {
        margin: 0.85rem 0;
        border: none;
        border-top: 1px solid #e2e8f0;
    }

    .stTabs [data-baseweb="tab-list"] {
        background: #f1f5f9;
        border-radius: 8px;
        padding: 0.25rem;
        gap: 0.25rem;
    }

    .stTabs [data-baseweb="tab"] {
        background: transparent;
        color: #64748b;
        border-radius: 6px;
    }

    .stTabs [aria-selected="true"] {
        background: #ffffff !important;
        color: #0f172a !important;
        box-shadow: 0 1px 2px rgba(0, 0, 0, 0.05);
    }

    /* Plan sections */
    .plan-section {
        background: #ffffff;
        border: 1px solid #e2e8f0;
        border-radius: 12px;
        padding: 1.5rem;
    }

    .plan-header {
        color: #0f172a;
        border-bottom: 1px solid #e2e8f0;
        padding-bottom: 0.75rem;
        margin-bottom: 1rem;
    }

    /* Nutrition cards */
    .nutrition-card {
        background: #ffffff;
        border: 1px solid #e2e8f0;
        border-radius: 12px;
        padding: 1rem;
    }

    .nutrition-value {
        color: #0f172a !important;
        font-weight: 700;
    }

    .nutrition-label {
        color: #64748b !important;
    }

    /* Text inputs */
    .stTextInput input, .stTextArea textarea {
        background: #ffffff !important;
        border: 1px solid #e2e8f0 !important;
        color: #0f172a !important;
        border-radius: 8px !important;
    }

    .stTextInput input:focus, .stTextArea textarea:focus {
        border-color: #2563eb !important;
        box-shadow: 0 0 0 3px rgba(37, 99, 235, 0.1) !important;
    }

    /* Select boxes */
    .stSelectbox > div > div {
        background: #ffffff !important;
        border: 1px solid #e2e8f0 !important;
        border-radius: 8px !important;
    }

    /* Progress bars */
    .stProgress > div > div {
        background: #e2e8f0 !important;
        border-radius: 9999px !important;
    }

    .stProgress > div > div > div {
        background: #2563eb !important;
        border-radius: 9999px !important;
    }

    /* Streamlit markdown text */
    .stMarkdown, .stMarkdown p {
        color: #374151;
    }

    h1, h2, h3, h4, h5, h6 {
        color: #0f172a !important;
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
        st.session_state.dark_mode = False


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
        st.markdown(f'<p style="color: #94a3b8; font-size: 0.65rem;">FIT CRM v{APP_VERSION}{sha_txt} · {"Tmavý" if dm else "Světlý"}</p>', unsafe_allow_html=True)


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

    st.markdown(
        f"""
        <div style="margin-bottom: 1rem;">
            <div style="font-size: 1.35rem; font-weight: 900; letter-spacing: -0.02em; color: var(--text);">Dashboard</div>
            <div style="margin-top: 0.1rem; color: var(--muted); font-size: 0.95rem;">{date_str}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    k1, k2, k3, k4 = st.columns(4)
    with k1:
        st.markdown(
            f"""
            <div class="kpi-card">
                <div class="kpi-label">Aktívni klienti</div>
                <div class="kpi-value">{stats['active_clients']}</div>
                <div class="kpi-foot">+{stats['new_this_week']} tento týždeň</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
    with k2:
        st.markdown(
            f"""
            <div class="kpi-card">
                <div class="kpi-label">Retencia</div>
                <div class="kpi-value">{stats['retention_percent']}%</div>
                <div class="kpi-foot">stabilná</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
    with k3:
        st.markdown(
            f"""
            <div class="kpi-card">
                <div class="kpi-label">Adherencia</div>
                <div class="kpi-value">{stats['avg_adherence']:.0f}%</div>
                <div class="kpi-foot">{'výborná' if stats['avg_adherence'] > 75 else 'treba zlepšiť'}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
    with k4:
        st.markdown(
            f"""
            <div class="kpi-card">
                <div class="kpi-label">Príjem / mesiac</div>
                <div class="kpi-value">€{stats['mrr_eur']}</div>
                <div class="kpi-foot">trend ↑</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    st.markdown('<div style="height: 0.9rem;"></div>', unsafe_allow_html=True)

    col_main, col_side = st.columns([1.65, 1.0], gap="large")

    with col_main:
        st.markdown(
            """
            <div class="section-card">
                <div class="section-head">
                    <div class="title">Dnešný plán</div>
                    <div class="meta">Najbližšie check-iny</div>
                </div>
            """,
            unsafe_allow_html=True,
        )

        recent = sorted(clients, key=lambda c: c.last_checkin, reverse=True)[:4]
        schedule_items = []
        for c in recent:
            schedule_items.append(
                {
                    "name": c.name,
                    "sub": f"Check-in · {c.days_since_checkin}d · {c.current_weight_kg}kg",
                    "pill": f"{c.progress_percent:.0f}%",
                }
            )

        for it in schedule_items:
            st.markdown(
                f"""
                <div class="list-row">
                    <div class="left">
                        <div class="name">{html.escape(it['name'])}</div>
                        <div class="sub">{html.escape(it['sub'])}</div>
                    </div>
                    <span class="pill">{html.escape(it['pill'])}</span>
                </div>
                """,
                unsafe_allow_html=True,
            )

        st.markdown("</div>", unsafe_allow_html=True)

        st.markdown('<div style="height: 0.9rem;"></div>', unsafe_allow_html=True)

        dm = st.session_state.dark_mode
        font_color = "#e7f3eb" if dm else "#0f172a"
        grid_color = "rgba(35, 72, 47, 0.35)" if dm else "rgba(217, 234, 223, 0.9)"
        muted_color = "#92c9a4" if dm else "#456a55"

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

        active_clients = [c for c in clients if c.status in ["active", "stagnating"]]
        days = [today - timedelta(days=i) for i in range(6, -1, -1)]
        vals = []
        for d in days:
            per = [v for v in (_adherence_at_day(c, d) for c in active_clients) if v is not None]
            vals.append(round(sum(per) / len(per)) if per else 0)

        ch1, ch2 = st.columns(2)
        with ch1:
            st.markdown(
                """
                <div class="section-card">
                    <div class="section-head">
                        <div class="title">Zdravie & progres</div>
                        <div class="meta">Rozdelenie klientov</div>
                    </div>
                """,
                unsafe_allow_html=True,
            )
            fig = go.Figure(
                data=[
                    go.Pie(
                        labels=["Progres", "Stagnácia", "Problém"],
                        values=[stats["progressing"], stats["stagnating"], stats["regressing"]],
                        hole=0.72,
                        marker_colors=["#13ec5b", "#fbbf24", "#f87171"],
                        textinfo="none",
                    )
                ]
            )
            fig.update_layout(
                showlegend=True,
                height=280,
                margin=dict(t=10, b=10, l=10, r=10),
                font=dict(color=font_color),
                paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="rgba(0,0,0,0)",
                legend=dict(orientation="h", yanchor="bottom", y=-0.15, xanchor="center", x=0.5),
            )
            st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})
            st.markdown("</div>", unsafe_allow_html=True)

        with ch2:
            st.markdown(
                """
                <div class="section-card">
                    <div class="section-head">
                        <div class="title">Compliance</div>
                        <div class="meta">Posledných 7 dní</div>
                    </div>
                """,
                unsafe_allow_html=True,
            )
            x = [d.strftime("%a") for d in days]
            fig2 = go.Figure(
                data=[
                    go.Scatter(
                        x=x,
                        y=vals,
                        mode="lines+markers",
                        line=dict(color="#13ec5b", width=3),
                        marker=dict(size=7, color="#13ec5b"),
                        fill="tozeroy",
                        fillcolor="rgba(19, 236, 91, 0.12)",
                        hovertemplate="%{x}<br>%{y}%<extra></extra>",
                    )
                ]
            )
            fig2.update_layout(
                height=280,
                margin=dict(t=10, b=10, l=10, r=10),
                font=dict(color=font_color),
                paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="rgba(0,0,0,0)",
                xaxis=dict(showgrid=False, tickfont=dict(color=muted_color)),
                yaxis=dict(range=[0, 100], gridcolor=grid_color, tickfont=dict(color=muted_color), zeroline=False),
                showlegend=False,
            )
            st.plotly_chart(fig2, use_container_width=True, config={"displayModeBar": False})
            st.markdown("</div>", unsafe_allow_html=True)

    with col_side:
        st.markdown(
            """
            <div class="section-card">
                <div class="section-head">
                    <div class="title">Quick actions</div>
                    <div class="meta">Najčastejšie</div>
                </div>
            """,
            unsafe_allow_html=True,
        )
        a1 = st.button("➕ Nový klient", use_container_width=True, type="primary", key="dash_new_client")
        a2 = st.button("📥 Inbox", use_container_width=True, key="dash_inbox")
        a3 = st.button("👥 Klienti", use_container_width=True, key="dash_clients")
        if a1:
            st.session_state.page = "new_client"
            st.rerun()
        if a2:
            st.session_state.page = "inbox"
            st.rerun()
        if a3:
            st.session_state.page = "clients"
            st.rerun()
        st.markdown("</div>", unsafe_allow_html=True)

        st.markdown('<div style="height: 0.9rem;"></div>', unsafe_allow_html=True)

        st.markdown(
            """
            <div class="section-card">
                <div class="section-head">
                    <div class="title">Aktivita</div>
                    <div class="meta">Posledné check-iny</div>
                </div>
            """,
            unsafe_allow_html=True,
        )
        for c in sorted(clients, key=lambda x: x.last_checkin, reverse=True)[:5]:
            status = {"active": "Aktívny", "stagnating": "Stagnuje", "problem": "Problém"}.get(c.status, c.status)
            st.markdown(
                f"""
                <div class="list-row">
                    <div class="left">
                        <div class="name">{html.escape(c.name)}</div>
                        <div class="sub">{html.escape(status)} · {c.current_weight_kg}kg · {c.days_since_checkin}d</div>
                    </div>
                    <span class="pill">{c.weight_change:+.1f}kg</span>
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

            if st.button("📊  Dashboard", use_container_width=True, type="primary" if st.session_state.page == "dashboard" else "secondary"):
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

            st.markdown('<div style="height: 0.7rem;"></div>', unsafe_allow_html=True)
            sha = _git_sha_short()
            sha_txt = f" · {sha}" if sha else ""
            st.markdown(
                f'<div style="color: var(--muted); font-size: 0.75rem;">v{APP_VERSION}{sha_txt} · {"Dark" if dm else "Light"}</div>',
                unsafe_allow_html=True,
            )

    with content_col:
        top = st.container()
        with top:
            st.markdown('<div id="topbar-marker"></div>', unsafe_allow_html=True)

            page_label = {
                "dashboard": "Dashboard",
                "clients": "Klienti",
                "client_detail": "Klient",
                "inbox": "Inbox",
                "new_client": "Nový klient",
                "email_connector": "Email konektor",
            }.get(st.session_state.page, "FitCRM")

            c0, c1, c2, c3, c4, c5 = st.columns([1.25, 2.35, 0.20, 0.85, 0.45, 0.65])
            with c0:
                st.markdown(f'<div class="topbar-title">{html.escape(page_label)}</div>', unsafe_allow_html=True)
                sha = _git_sha_short()
                if sha:
                    st.markdown(f'<div class="topbar-sub">{html.escape(sha)}</div>', unsafe_allow_html=True)
            with c1:
                st.text_input("", placeholder="Search clients, emails…", label_visibility="collapsed", key="global_search")
            with c3:
                next_dm = st.toggle("Dark", value=dm, key="top_dark_toggle")
                if next_dm != dm:
                    st.session_state.dark_mode = next_dm
                    st.rerun()
            with c4:
                st.markdown('<div class="topbar-icon">🔔</div>', unsafe_allow_html=True)
            with c5:
                avatar = _portrait_data_uri("trainer")
                st.markdown(f'<div class="topbar-avatar"><img src="{avatar}" alt="avatar" /></div>', unsafe_allow_html=True)

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
    """Render client list view"""
    st.markdown('<div class="main-header">👥 Klienti</div>', unsafe_allow_html=True)

    clients = st.session_state.clients

    st.markdown('<div class="bento-card" style="padding: 0.85rem 1rem; margin-bottom: 1rem;">', unsafe_allow_html=True)
    col1, col2, col3, col4 = st.columns([2.2, 1.25, 1.25, 1.1])
    with col1:
        search = st.text_input("", placeholder="Hľadať klienta (meno/email)…", label_visibility="collapsed")
    with col2:
        status_filter = st.selectbox("Stav", ["Všetko", "Aktívny", "Stagnuje", "Problém"], label_visibility="collapsed")
    with col3:
        sort_by = st.selectbox("Zoradiť", ["Posledný check-in", "Meno", "Progres"], label_visibility="collapsed")
    with col4:
        if st.button("➕", use_container_width=True):
            st.session_state.page = 'new_client'
            st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)

    # Filter clients
    filtered = clients
    if search:
        search_lower = search.lower()
        filtered = [c for c in filtered if search_lower in c.name.lower() or search_lower in c.email.lower()]

    if status_filter == "Aktívny":
        filtered = [c for c in filtered if c.status == "active"]
    elif status_filter == "Stagnuje":
        filtered = [c for c in filtered if c.status == "stagnating"]
    elif status_filter == "Problém":
        filtered = [c for c in filtered if c.status == "problem"]

    # Sort
    if sort_by == "Posledný check-in":
        filtered = sorted(filtered, key=lambda c: c.last_checkin, reverse=True)
    elif sort_by == "Meno":
        filtered = sorted(filtered, key=lambda c: c.name)
    elif sort_by == "Progres":
        filtered = sorted(filtered, key=lambda c: c.progress_percent, reverse=True)

    st.markdown('<div class="bento-card" style="padding: 0.9rem;">', unsafe_allow_html=True)
    total = len(filtered)
    st.caption(f"Klienti: {total}")

    if not filtered:
        st.info("Žiadni klienti (alebo nič nezodpovedá filtru).")
        st.markdown('</div>', unsafe_allow_html=True)
        return

    page_size = int(st.session_state.clients_page_size)
    page_count = max(1, (total + page_size - 1) // page_size)
    if st.session_state.clients_page > page_count:
        st.session_state.clients_page = page_count
    if st.session_state.clients_page < 1:
        st.session_state.clients_page = 1

    nav1, nav2, nav3, nav4 = st.columns([1, 1, 1.2, 1.8])
    with nav1:
        if st.button("←", use_container_width=True, disabled=st.session_state.clients_page <= 1, key="clients_prev"):
            st.session_state.clients_page -= 1
            st.rerun()
    with nav2:
        if st.button("→", use_container_width=True, disabled=st.session_state.clients_page >= page_count, key="clients_next"):
            st.session_state.clients_page += 1
            st.rerun()
    with nav3:
        st.session_state.clients_page_size = st.selectbox(
            "",
            options=[25, 50, 100],
            index=[25, 50, 100].index(st.session_state.clients_page_size) if st.session_state.clients_page_size in [25, 50, 100] else 0,
            label_visibility="collapsed",
            key="clients_page_size_select",
        )
    with nav4:
        st.caption(f"Strana {st.session_state.clients_page} / {page_count}")

    start = (st.session_state.clients_page - 1) * page_size
    end = start + page_size
    visible = filtered[start:end]

    rows = []
    for c in visible:
        status_raw = (c.status or "").strip().lower()
        status_label = {"active": "Aktívny", "stagnating": "Stagnuje", "problem": "Problém"}.get(status_raw, status_raw)
        status_symbol = {"active": "●", "stagnating": "◐", "problem": "!"}.get(status_raw, "")
        rows.append(
            {
                "_id": c.id,
                "Foto": _portrait_data_uri(c.name),
                "Meno": c.name,
                "Email": c.email,
                "Stav": f"{status_symbol} {status_label}".strip(),
                "Progres": f"{c.progress_percent:.0f}%",
                "Check-in": f"{c.days_since_checkin}d",
            }
        )

    df = pd.DataFrame(rows)
    display = df.drop(columns=["_id"], errors="ignore")

    try:
        event = st.dataframe(
            display,
            use_container_width=True,
            hide_index=True,
            height=620,
            selection_mode="single-row",
            on_select="rerun",
            column_config={
                "Foto": st.column_config.ImageColumn("", width="small"),
                "Meno": st.column_config.TextColumn("Meno", width="medium"),
                "Email": st.column_config.TextColumn("Email", width="medium"),
                "Stav": st.column_config.TextColumn("Stav", width="small"),
                "Progres": st.column_config.TextColumn("Progres", width="small"),
                "Check-in": st.column_config.TextColumn("Check-in", width="small"),
            },
        )

        selection_obj = getattr(event, "selection", None)
        sel_rows = None
        if isinstance(selection_obj, dict):
            sel_rows = selection_obj.get("rows")
        else:
            sel_rows = getattr(selection_obj, "rows", None)

        if sel_rows:
            selected_idx = sel_rows[0]
            selected_id = df.iloc[int(selected_idx)]["_id"]
            st.session_state.selected_client = selected_id
            st.session_state.page = 'client_detail'
            st.rerun()
    except TypeError:
        by_id = {c.id: c for c in visible}
        options = [c.id for c in visible]

        def _fmt(client_id: str) -> str:
            c = by_id.get(client_id)
            if not c:
                return client_id
            status_label = {"active": "Aktívny", "stagnating": "Stagnuje", "problem": "Problém"}.get(c.status, c.status)
            return f"{c.name} · {status_label} · {c.progress_percent:.0f}%"

        selected_id = st.radio(
            "",
            options=options,
            format_func=_fmt,
            label_visibility="collapsed",
            key="clients_radio",
        )
        st.session_state.selected_client = selected_id
        st.session_state.page = 'client_detail'
        st.rerun()

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
    avatar = _portrait_data_uri(client.name)
    chips = [f'<span class="chip {status_raw}">{html.escape(status_label)}</span>']
    chips.append(f'<span class="chip">{html.escape(client.email)}</span>')
    st.markdown(
        f"""
        <div class="bento-card" style="padding: 0.95rem; margin-bottom: 1rem;">
            <div style="display:flex; gap: 0.9rem; align-items: center;">
                <img class="avatar-img" src="{avatar}" alt="avatar" />
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

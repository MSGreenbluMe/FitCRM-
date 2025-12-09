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

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

from src.email_parser import EmailParser, ClientProfile
from src.ai_generator import FitAIGenerator, ClientSegment
from src.pdf_generator import PDFGenerator
from src.mock_data import get_mock_clients, get_dashboard_stats, ClientData

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

# Page config
st.set_page_config(
    page_title="FIT CRM",
    page_icon="💪",
    layout="wide",
    initial_sidebar_state="expanded"
)

def get_theme_css(dark_mode: bool) -> str:
    """Generate CSS based on theme mode"""
    if dark_mode:
        return """
        /* Dark Mode Colors */
        :root {
            --bg-primary: #0f172a;
            --bg-secondary: #1e293b;
            --bg-card: #1e293b;
            --border-color: #334155;
            --text-primary: #f1f5f9;
            --text-secondary: #94a3b8;
            --text-muted: #64748b;
        }
        .stApp { background: #0f172a !important; }
        .bento-card { background: #1e293b !important; border-color: #334155 !important; }
        .bento-card:hover { border-color: #475569 !important; }
        .hero-title { color: #f1f5f9 !important; }
        .hero-subtitle { color: #94a3b8 !important; }
        .stat-value { color: #f1f5f9 !important; }
        .stat-label { color: #94a3b8 !important; }
        .section-title { color: #f1f5f9 !important; }
        .activity-name { color: #f1f5f9 !important; }
        .activity-meta { color: #94a3b8 !important; }
        .alert-text { color: #e2e8f0 !important; }
        .alert-text strong { color: #f1f5f9 !important; }
        .avatar-card { background: linear-gradient(135deg, #1e293b 0%, #0f172a 100%) !important; border-color: #334155 !important; }
        .avatar-placeholder { background: linear-gradient(135deg, #334155 0%, #1e293b 100%) !important; border-color: #475569 !important; }
        .ticket-card { background: #1e293b !important; border-color: #334155 !important; }
        .ticket-card:hover { background: #334155 !important; }
        .ticket-card .ticket-subject { color: #f1f5f9 !important; }
        .ticket-card .ticket-meta { color: #94a3b8 !important; }
        [data-testid="stSidebar"] { background: #1e293b !important; border-color: #334155 !important; }
        [data-testid="stMetricValue"] { color: #f1f5f9 !important; }
        [data-testid="stMetricLabel"] { color: #94a3b8 !important; }
        .stMarkdown, .stMarkdown p { color: #e2e8f0 !important; }
        h1, h2, h3, h4, h5, h6 { color: #f1f5f9 !important; }
        .main-header { color: #f1f5f9 !important; }
        .stTextInput input, .stTextArea textarea { background: #1e293b !important; border-color: #334155 !important; color: #f1f5f9 !important; }
        .stSelectbox > div > div { background: #1e293b !important; border-color: #334155 !important; }
        .stTabs [data-baseweb="tab-list"] { background: #1e293b !important; }
        .stTabs [data-baseweb="tab"] { color: #94a3b8 !important; }
        .stTabs [aria-selected="true"] { background: #334155 !important; color: #f1f5f9 !important; }
        .plan-section { background: #1e293b !important; border-color: #334155 !important; }
        .plan-header { color: #f1f5f9 !important; border-color: #334155 !important; }
        .nutrition-card { background: #1e293b !important; border-color: #334155 !important; }
        .nutrition-value { color: #f1f5f9 !important; }
        .nutrition-label { color: #94a3b8 !important; }
        """
    return ""

# Custom CSS - Clean Professional Design
st.markdown("""
<style>
    /* ===== CLEAN PROFESSIONAL FOUNDATION ===== */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');

    /* Hide Streamlit branding */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}

    .stApp {
        background: #f8fafc;
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
    }

    .main .block-container {
        padding: 2rem 3rem;
        max-width: 1400px;
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
        padding: 1.5rem;
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
        padding: 1.5rem;
        text-align: center;
        position: relative;
        overflow: hidden;
        min-height: 280px;
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

    /* ===== LEGACY OVERRIDES ===== */
    .main-header {
        font-size: 1.5rem;
        font-weight: 600;
        color: #0f172a;
        letter-spacing: -0.01em;
        margin-bottom: 1.25rem;
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
    # Email ticket system
    if 'email_tickets' not in st.session_state:
        st.session_state.email_tickets = DEMO_EMAILS.copy()
    if 'selected_ticket' not in st.session_state:
        st.session_state.selected_ticket = None
    # Generation mode: 'auto' or 'semi'
    if 'generation_mode' not in st.session_state:
        st.session_state.generation_mode = 'auto'
    # Editable plans for semi-auto mode
    if 'editable_meal_plan' not in st.session_state:
        st.session_state.editable_meal_plan = None
    if 'editable_training_plan' not in st.session_state:
        st.session_state.editable_training_plan = None
    # Dark mode
    if 'dark_mode' not in st.session_state:
        st.session_state.dark_mode = False


def render_sidebar():
    """Render navigation sidebar with dark mode toggle"""
    dm = st.session_state.dark_mode
    with st.sidebar:
        # Logo / Brand
        st.markdown(f"""
        <div style="padding: 1rem 0 1.5rem 0;">
            <span style="font-size: 1.5rem; font-weight: 700; color: #2563eb;">FIT</span>
            <span style="font-size: 1.5rem; font-weight: 400; color: {'#94a3b8' if dm else '#64748b'};">CRM</span>
        </div>
        """, unsafe_allow_html=True)

        # Dark mode toggle
        dark_mode = st.toggle("🌙 Tmavý režim", value=st.session_state.dark_mode, key="dark_toggle")
        if dark_mode != st.session_state.dark_mode:
            st.session_state.dark_mode = dark_mode
            st.rerun()

        st.markdown("<br>", unsafe_allow_html=True)

        # Navigation
        st.markdown(f'<p style="color: {"#94a3b8" if dm else "#64748b"}; font-size: 0.7rem; text-transform: uppercase; letter-spacing: 0.1em; margin-bottom: 0.5rem;">Nabídka</p>', unsafe_allow_html=True)

        if st.button("📊  Přehled", use_container_width=True,
                     type="primary" if st.session_state.page == 'dashboard' else "secondary"):
            st.session_state.page = 'dashboard'
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

        st.markdown("<br>", unsafe_allow_html=True)

        # Email Feed / Tickets
        new_tickets = [t for t in st.session_state.email_tickets if t['status'] == 'new']
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

        st.markdown("<br>", unsafe_allow_html=True)

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

        st.markdown("<br><br>", unsafe_allow_html=True)
        st.markdown(f'<p style="color: #94a3b8; font-size: 0.65rem;">FIT CRM v3.0 · {"Tmavý" if dm else "Světlý"}</p>', unsafe_allow_html=True)


def render_dashboard():
    """Render clean professional dashboard with Bento grid"""
    clients = st.session_state.clients
    stats = get_dashboard_stats(clients)
    today = datetime.now()

    # Czech day/month names
    cz_days = ['Pondělí', 'Úterý', 'Středa', 'Čtvrtek', 'Pátek', 'Sobota', 'Neděle']
    cz_months = ['ledna', 'února', 'března', 'dubna', 'května', 'června', 'července', 'srpna', 'září', 'října', 'listopadu', 'prosince']
    date_str = f"{cz_days[today.weekday()]}, {today.day}. {cz_months[today.month-1]} {today.year}"

    # Hero Header
    st.markdown(f"""
    <div style="margin-bottom: 1.5rem;">
        <h1 class="hero-title">Vítejte zpět</h1>
        <p class="hero-subtitle">{date_str}</p>
    </div>
    """, unsafe_allow_html=True)

    # Bento Grid - Row 1: KPIs
    st.markdown(f"""
    <div class="bento-grid">
        <div class="bento-card bento-sm">
            <div class="stat-label">Klienti</div>
            <div class="stat-value blue">{stats["active_clients"]}</div>
            <div class="stat-trend trend-up">↑ +{stats['new_this_week']} tento týden</div>
        </div>
        <div class="bento-card bento-sm">
            <div class="stat-label">Retence</div>
            <div class="stat-value emerald">{stats['retention_percent']}%</div>
            <div class="stat-trend trend-neutral">→ stabilní</div>
        </div>
        <div class="bento-card bento-sm">
            <div class="stat-label">Adherence</div>
            <div class="stat-value slate">{stats['avg_adherence']:.0f}%</div>
            <div class="stat-trend {'trend-up' if stats['avg_adherence'] > 75 else 'trend-down'}">{'↑ výborná' if stats['avg_adherence'] > 75 else '↓ zlepšit'}</div>
        </div>
        <div class="bento-card bento-sm">
            <div class="stat-label">Příjem / měsíc</div>
            <div class="stat-value amber">€{stats['mrr_eur']}</div>
            <div class="stat-trend trend-up">↑ +12%</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # Main Content Grid
    col_main, col_side = st.columns([2, 1])

    with col_main:
        # Charts in Bento cards
        chart_col1, chart_col2 = st.columns(2)

        with chart_col1:
            st.markdown("""
            <div class="bento-card" style="margin-bottom: 1rem;">
                <div class="section-header">
                    <div class="section-icon emerald">📈</div>
                    <span class="section-title">Progres klientů</span>
                </div>
            """, unsafe_allow_html=True)

            # Light mode donut chart
            fig = go.Figure(data=[go.Pie(
                labels=['Progres', 'Stagnace', 'Regres'],
                values=[stats['progressing'], stats['stagnating'], stats['regressing']],
                hole=.7,
                marker_colors=['#059669', '#d97706', '#dc2626'],
                textinfo='none',
                hovertemplate='%{label}<br>%{value} klientů<br>%{percent}<extra></extra>'
            )])
            fig.update_layout(
                showlegend=True,
                legend=dict(
                    orientation="h",
                    yanchor="bottom",
                    y=-0.15,
                    xanchor="center",
                    x=0.5,
                    font=dict(color='#64748b', size=11)
                ),
                height=240,
                margin=dict(t=10, b=30, l=10, r=10),
                paper_bgcolor='rgba(0,0,0,0)',
                plot_bgcolor='rgba(0,0,0,0)',
                annotations=[dict(
                    text=f'<b>{stats["progressing"]}</b><br><span style="font-size:10px;color:#64748b">úspěšných</span>',
                    x=0.5, y=0.5,
                    font=dict(size=24, color='#059669'),
                    showarrow=False
                )]
            )
            st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})
            st.markdown('</div>', unsafe_allow_html=True)

        with chart_col2:
            st.markdown("""
            <div class="bento-card" style="margin-bottom: 1rem;">
                <div class="section-header">
                    <div class="section-icon blue">📊</div>
                    <span class="section-title">Změny váhy</span>
                </div>
            """, unsafe_allow_html=True)

            recent_clients = sorted(clients, key=lambda c: c.last_checkin, reverse=True)[:5]
            names = [c.name.split()[0] for c in recent_clients]
            changes = [c.weight_change for c in recent_clients]
            colors = ['#059669' if c < 0 else '#dc2626' if c > 0 else '#64748b' for c in changes]

            fig = go.Figure(data=[go.Bar(
                x=names,
                y=changes,
                marker_color=colors,
                marker_line_width=0,
                text=[f"{c:+.1f}" for c in changes],
                textposition='outside',
                textfont=dict(size=10, color='#64748b'),
                hovertemplate='%{x}<br>%{y:+.1f} kg<extra></extra>'
            )])
            fig.update_layout(
                height=240,
                margin=dict(t=10, b=30, l=30, r=10),
                yaxis=dict(
                    gridcolor='#f1f5f9',
                    zerolinecolor='#e2e8f0',
                    tickfont=dict(color='#64748b'),
                    title=None
                ),
                xaxis=dict(tickfont=dict(size=10, color='#64748b')),
                showlegend=False,
                paper_bgcolor='rgba(0,0,0,0)',
                plot_bgcolor='rgba(0,0,0,0)',
                bargap=0.5
            )
            st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})
            st.markdown('</div>', unsafe_allow_html=True)

        # Alerts Section
        if stats["problem_clients"]:
            st.markdown("""
            <div class="bento-card">
                <div class="section-header">
                    <div class="section-icon red">⚠️</div>
                    <span class="section-title">Vyžaduje pozornost</span>
                </div>
            """, unsafe_allow_html=True)

            for client in stats["problem_clients"][:3]:
                is_critical = client.days_since_checkin > 14
                alert_class = "" if is_critical else "warning"
                icon = "🚨" if is_critical else "⚠️"
                message = f"{client.days_since_checkin} dní bez check-inu" if is_critical else "váha stagnuje"

                st.markdown(f"""
                <div class="alert-card {alert_class}">
                    <span class="alert-icon">{icon}</span>
                    <span class="alert-text"><strong>{client.name}</strong> — {message}</span>
                </div>
                """, unsafe_allow_html=True)

            st.markdown('</div>', unsafe_allow_html=True)

            # Action buttons for alerts
            for client in stats["problem_clients"][:3]:
                if st.button(f"→ {client.name}", key=f"alert_{client.id}"):
                    st.session_state.selected_client = client.id
                    st.session_state.page = 'client_detail'
                    st.rerun()

    with col_side:
        # Stats Card
        st.markdown(f"""
        <div class="avatar-card">
            <div class="avatar-placeholder"></div>
            <div style="color: #0f172a; font-weight: 600; margin-bottom: 0.5rem;">Složení těla</div>
            <div style="color: #64748b; font-size: 0.8rem;">Průměrná změna klientů</div>
            <div class="avatar-stats">
                <div class="avatar-stat">
                    <div class="avatar-stat-value">-2.3</div>
                    <div class="avatar-stat-label">kg tuku</div>
                </div>
                <div class="avatar-stat">
                    <div class="avatar-stat-value">+1.1</div>
                    <div class="avatar-stat-label">kg svalů</div>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)

        # Activity Timeline
        st.markdown("""
        <div class="bento-card" style="margin-top: 1rem;">
            <div class="section-header">
                <div class="section-icon amber">🕐</div>
                <span class="section-title">Aktivita</span>
            </div>
        """, unsafe_allow_html=True)

        recent = sorted(clients, key=lambda c: c.last_checkin, reverse=True)[:4]
        for client in recent:
            avatar_class = {"active": "avatar-active", "stagnating": "avatar-warning", "problem": "avatar-danger"}.get(client.status, "avatar-active")
            initials = "".join([n[0].upper() for n in client.name.split()[:2]])
            days = client.days_since_checkin
            time_text = "Dnes" if days == 0 else "Včera" if days == 1 else f"před {days}d"
            badge_class = "badge-success" if client.weight_change < 0 else "badge-danger" if client.weight_change > 0 else "badge-warning"
            change_text = f"{client.weight_change:+.1f}kg"

            st.markdown(f"""
            <div class="activity-item">
                <div class="activity-avatar {avatar_class}">{initials}</div>
                <div class="activity-content">
                    <div class="activity-name">{client.name}</div>
                    <div class="activity-meta">{client.current_weight_kg}kg · {time_text}</div>
                </div>
                <span class="activity-badge {badge_class}">{change_text}</span>
            </div>
            """, unsafe_allow_html=True)

        st.markdown('</div>', unsafe_allow_html=True)

        # Quick Actions
        st.markdown("---")
        if st.button("➕ Nový klient", key="qa_new", use_container_width=True, type="primary"):
            st.session_state.page = 'new_client'
            st.rerun()

        if st.button("👥 Všichni klienti", key="qa_clients", use_container_width=True, type="secondary"):
            st.session_state.page = 'clients'
            st.rerun()


def render_clients_list():
    """Render client list view"""
    st.markdown('<div class="main-header">👥 Klienti</div>', unsafe_allow_html=True)

    clients = st.session_state.clients

    # Filters
    col1, col2, col3 = st.columns([2, 2, 2])
    with col1:
        search = st.text_input("🔍 Hledat", placeholder="Jméno nebo email...")
    with col2:
        status_filter = st.selectbox("Stav", ["Všichni", "Aktivní", "Stagnující", "Problém"])
    with col3:
        sort_by = st.selectbox("Seřadit podle", ["Poslední check-in", "Jméno", "Progres"])

    st.markdown("---")

    # Filter clients
    filtered = clients
    if search:
        search_lower = search.lower()
        filtered = [c for c in filtered if search_lower in c.name.lower() or search_lower in c.email.lower()]

    if status_filter == "Aktivní":
        filtered = [c for c in filtered if c.status == "active"]
    elif status_filter == "Stagnující":
        filtered = [c for c in filtered if c.status == "stagnating"]
    elif status_filter == "Problém":
        filtered = [c for c in filtered if c.status == "problem"]

    # Sort
    if sort_by == "Poslední check-in":
        filtered = sorted(filtered, key=lambda c: c.last_checkin, reverse=True)
    elif sort_by == "Jméno":
        filtered = sorted(filtered, key=lambda c: c.name)
    elif sort_by == "Progres":
        filtered = sorted(filtered, key=lambda c: c.progress_percent, reverse=True)

    # Display clients
    for client in filtered:
        status_emoji = {"active": "🟢", "stagnating": "🟡", "problem": "🔴"}.get(client.status, "⚪")

        with st.container():
            col1, col2, col3, col4 = st.columns([3, 2, 3, 1])

            with col1:
                st.markdown(f"### {status_emoji} {client.name}")
                st.caption(f"{client.age} let, {'Muž' if client.gender == 'male' else 'Žena'}")

            with col2:
                st.write(f"**Cíl:** {client.goal}")
                weight_change = client.weight_change
                change_emoji = "↓" if weight_change < 0 else "↑" if weight_change > 0 else "→"
                st.write(f"**Váha:** {client.current_weight_kg}kg ({change_emoji}{abs(weight_change):.1f}kg)")

            with col3:
                progress = client.progress_percent
                st.write(f"**Progres:** {progress:.0f}%")
                st.progress(progress / 100)

                days = client.days_since_checkin
                if days > 7:
                    st.caption(f"⚠️ Check-in před {days} dny")
                else:
                    st.caption(f"✅ Check-in před {days} dny")

            with col4:
                if st.button("Detail", key=f"client_{client.id}", use_container_width=True):
                    st.session_state.selected_client = client.id
                    st.session_state.page = 'client_detail'
                    st.rerun()

            st.markdown("---")


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

    st.markdown(f'<div class="main-header">👤 {client.name}</div>', unsafe_allow_html=True)

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
                margin=dict(t=20, b=20, l=20, r=20),
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
                margin=dict(t=20, b=20, l=20, r=20),
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
                margin=dict(t=20, b=20, l=20, r=20),
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

        # Wait before next request
        status.text("⏳ Čakám pred ďalším requestom...")
        time.sleep(3)

        # Step 2: Generate meal plan (1 API request)
        status.text("🍽️ Generujem jedálniček... (2/3)")
        progress.progress(45)
        meal_plan = ai.generate_meal_plan(profile, segment)
        st.session_state.meal_plan = meal_plan
        progress.progress(66)

        # Wait before next request
        status.text("⏳ Čakám pred ďalším requestom...")
        time.sleep(3)

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

    render_sidebar()

    page = st.session_state.page

    if page == 'dashboard':
        render_dashboard()
    elif page == 'clients':
        render_clients_list()
    elif page == 'client_detail':
        render_client_detail()
    elif page == 'new_client':
        render_new_client()


if __name__ == "__main__":
    main()

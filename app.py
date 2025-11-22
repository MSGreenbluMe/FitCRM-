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

# Custom CSS - Professional dashboard styling
st.markdown("""
<style>
    /* Global styles */
    .main { background-color: #f5f7fa; }

    /* Header styling */
    .main-header {
        font-size: 2rem;
        font-weight: 700;
        color: #1e3a5f;
        padding: 0.5rem 0;
        border-bottom: 3px solid #4a90d9;
        margin-bottom: 1.5rem;
        letter-spacing: -0.5px;
    }

    /* Metric cards styling */
    [data-testid="stMetricValue"] {
        font-size: 1.8rem;
        font-weight: 700;
        color: #1e3a5f;
    }
    [data-testid="stMetricDelta"] {
        font-size: 0.85rem;
    }

    /* Ticket/Email feed styling */
    .ticket-item {
        background: white;
        border-radius: 8px;
        padding: 0.75rem;
        margin: 0.5rem 0;
        border-left: 4px solid #4a90d9;
        box-shadow: 0 1px 3px rgba(0,0,0,0.1);
        cursor: pointer;
        transition: all 0.2s ease;
    }
    .ticket-item:hover {
        box-shadow: 0 3px 6px rgba(0,0,0,0.15);
        transform: translateX(2px);
    }
    .ticket-item.priority-high { border-left-color: #e74c3c; }
    .ticket-item.priority-normal { border-left-color: #4a90d9; }
    .ticket-item.priority-low { border-left-color: #95a5a6; }
    .ticket-subject {
        font-weight: 600;
        font-size: 0.9rem;
        color: #1e3a5f;
        margin-bottom: 0.25rem;
    }
    .ticket-meta {
        font-size: 0.75rem;
        color: #7f8c8d;
    }
    .ticket-badge {
        display: inline-block;
        padding: 0.15rem 0.5rem;
        border-radius: 10px;
        font-size: 0.65rem;
        font-weight: 600;
        text-transform: uppercase;
    }
    .badge-new { background: #e8f6ff; color: #2980b9; }
    .badge-assigned { background: #fef5e7; color: #f39c12; }
    .badge-done { background: #e8f8f5; color: #27ae60; }

    /* Plan section styling */
    .plan-section {
        background: white;
        border-radius: 12px;
        padding: 1.5rem;
        margin: 1rem 0;
        box-shadow: 0 2px 8px rgba(0,0,0,0.08);
    }
    .plan-header {
        font-size: 1.2rem;
        font-weight: 700;
        color: #1e3a5f;
        padding-bottom: 0.75rem;
        border-bottom: 2px solid #4a90d9;
        margin-bottom: 1rem;
    }
    .meal-card {
        background: linear-gradient(135deg, #f8f9fa 0%, #e9ecef 100%);
        border-radius: 10px;
        padding: 1rem;
        margin: 0.75rem 0;
        border-left: 4px solid #27ae60;
    }
    .meal-title {
        font-weight: 700;
        color: #1e3a5f;
        font-size: 1rem;
        margin-bottom: 0.5rem;
    }
    .meal-macros {
        display: flex;
        gap: 1rem;
        margin-top: 0.5rem;
    }
    .macro-badge {
        display: inline-block;
        padding: 0.25rem 0.5rem;
        border-radius: 6px;
        font-size: 0.75rem;
        font-weight: 600;
    }
    .macro-protein { background: #ffebee; color: #c62828; }
    .macro-carbs { background: #fff3e0; color: #ef6c00; }
    .macro-fat { background: #e3f2fd; color: #1565c0; }
    .macro-cal { background: #e8f5e9; color: #2e7d32; }

    /* Training day card */
    .training-day {
        background: linear-gradient(135deg, #f8f9fa 0%, #e9ecef 100%);
        border-radius: 10px;
        padding: 1rem;
        margin: 0.75rem 0;
        border-left: 4px solid #4a90d9;
    }
    .training-title {
        font-weight: 700;
        color: #1e3a5f;
        font-size: 1rem;
        margin-bottom: 0.75rem;
    }
    .exercise-item {
        padding: 0.5rem 0;
        border-bottom: 1px solid #dee2e6;
        font-size: 0.9rem;
    }
    .exercise-item:last-child { border-bottom: none; }

    /* Client cards */
    .client-card {
        background: white;
        border-radius: 10px;
        padding: 1rem;
        margin: 0.5rem 0;
        border-left: 4px solid #3498db;
        box-shadow: 0 1px 4px rgba(0,0,0,0.08);
    }
    .client-card.active { border-left-color: #27ae60; }
    .client-card.stagnating { border-left-color: #f39c12; }
    .client-card.problem { border-left-color: #e74c3c; }

    /* Status badges */
    .status-badge {
        display: inline-block;
        padding: 0.25rem 0.75rem;
        border-radius: 20px;
        font-size: 0.8rem;
        font-weight: 600;
    }
    .status-active { background: #d5f5e3; color: #27ae60; }
    .status-stagnating { background: #fdebd0; color: #f39c12; }
    .status-problem { background: #fadbd8; color: #e74c3c; }

    /* Alert styling */
    .alert-box {
        background: linear-gradient(135deg, #fff3cd 0%, #ffe9a0 100%);
        border: 1px solid #ffc107;
        border-radius: 8px;
        padding: 1rem;
        margin: 0.5rem 0;
    }

    /* Mode selector */
    .mode-selector {
        background: white;
        border-radius: 8px;
        padding: 0.75rem;
        margin: 1rem 0;
        box-shadow: 0 1px 3px rgba(0,0,0,0.08);
    }

    /* Nutrition info */
    .nutrition-card {
        background: linear-gradient(135deg, #e8f5e9 0%, #c8e6c9 100%);
        border-radius: 10px;
        padding: 1rem;
        margin: 0.5rem 0;
    }
    .nutrition-value {
        font-size: 1.5rem;
        font-weight: 700;
        color: #2e7d32;
    }
    .nutrition-label {
        font-size: 0.8rem;
        color: #558b2f;
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


def render_sidebar():
    """Render navigation sidebar"""
    with st.sidebar:
        st.markdown("## 💪 FIT CRM")
        st.markdown("---")

        # Navigation
        st.markdown("### Navigácia")

        if st.button("📊 Dashboard", use_container_width=True,
                     type="primary" if st.session_state.page == 'dashboard' else "secondary"):
            st.session_state.page = 'dashboard'
            st.session_state.selected_client = None
            st.rerun()

        if st.button("👥 Klienti", use_container_width=True,
                     type="primary" if st.session_state.page == 'clients' else "secondary"):
            st.session_state.page = 'clients'
            st.session_state.selected_client = None
            st.rerun()

        if st.button("➕ Nový klient", use_container_width=True,
                     type="primary" if st.session_state.page == 'new_client' else "secondary"):
            st.session_state.page = 'new_client'
            st.rerun()

        st.markdown("---")

        # Email Feed / Tickets
        st.markdown("### 📬 Prichádzajúce emaily")

        new_tickets = [t for t in st.session_state.email_tickets if t['status'] == 'new']
        if new_tickets:
            st.caption(f"{len(new_tickets)} nových žiadostí")

        for ticket in st.session_state.email_tickets[:4]:
            priority_class = f"priority-{ticket['priority']}"
            status_badge = {
                'new': '<span class="ticket-badge badge-new">Nový</span>',
                'assigned': '<span class="ticket-badge badge-assigned">Priradený</span>',
                'done': '<span class="ticket-badge badge-done">Hotový</span>'
            }.get(ticket['status'], '')

            # Ticket card
            st.markdown(f"""
            <div class="ticket-item {priority_class}">
                <div class="ticket-subject">{ticket['subject']}</div>
                <div class="ticket-meta">{ticket['from']} · {ticket['time']} {status_badge}</div>
            </div>
            """, unsafe_allow_html=True)

            if st.button("📋 Priradiť", key=f"assign_{ticket['id']}", use_container_width=True):
                # Mark as assigned and load into parser
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

        st.markdown("---")

        # API Status
        api_key = get_api_key()
        nutrition_key = get_nutrition_api_key()

        col1, col2 = st.columns(2)
        with col1:
            if api_key:
                st.success("✅ Gemini")
            else:
                st.error("❌ Gemini")
        with col2:
            if nutrition_key:
                st.success("✅ Nutri API")
            else:
                st.caption("⚪ Nutri API")

        st.markdown("---")
        st.caption("FIT CRM v1.1 Demo")


def render_dashboard():
    """Render main dashboard with stats"""
    st.markdown('<div class="main-header">📊 Dashboard</div>', unsafe_allow_html=True)

    clients = st.session_state.clients
    stats = get_dashboard_stats(clients)

    # Quick Stats Row
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric(
            label="Aktívni klienti",
            value=stats["active_clients"],
            delta=f"+{stats['new_this_week']} tento týždeň"
        )

    with col2:
        st.metric(
            label="Retencia",
            value=f"{stats['retention_percent']}%",
            delta="stabilná"
        )

    with col3:
        st.metric(
            label="Priem. adherencia",
            value=f"{stats['avg_adherence']:.0f}%"
        )

    with col4:
        st.metric(
            label="MRR",
            value=f"€{stats['mrr_eur']}",
            delta="+12%"
        )

    st.markdown("---")

    # Alerts Section
    if stats["problem_clients"]:
        st.markdown("### ⚠️ Vyžaduje pozornosť")
        for client in stats["problem_clients"]:
            with st.container():
                col1, col2 = st.columns([4, 1])
                with col1:
                    if client.days_since_checkin > 14:
                        st.warning(f"🚨 **{client.name}** - {client.days_since_checkin} dní bez check-inu")
                    elif client.status == "problem":
                        st.warning(f"⚠️ **{client.name}** - váha stagnuje/rastie")
                with col2:
                    if st.button("Detail", key=f"alert_{client.id}"):
                        st.session_state.selected_client = client.id
                        st.session_state.page = 'client_detail'
                        st.rerun()

    st.markdown("---")

    # Progress Overview
    col1, col2 = st.columns(2)

    with col1:
        st.markdown("### 📈 Progres klientov")

        # Pie chart of progress status
        fig = go.Figure(data=[go.Pie(
            labels=['Progres ✅', 'Stagnácia ⚠️', 'Regres 🔴'],
            values=[stats['progressing'], stats['stagnating'], stats['regressing']],
            hole=.4,
            marker_colors=['#27ae60', '#f39c12', '#e74c3c']
        )])
        fig.update_layout(
            showlegend=True,
            height=300,
            margin=dict(t=20, b=20, l=20, r=20)
        )
        st.plotly_chart(fig, use_container_width=True)

    with col2:
        st.markdown("### 📊 Váhové zmeny (posledných 7 dní)")

        # Bar chart of weight changes
        recent_clients = sorted(clients, key=lambda c: c.last_checkin, reverse=True)[:5]
        names = [c.name.split()[0] for c in recent_clients]
        changes = [c.weight_change for c in recent_clients]
        colors = ['#27ae60' if c < 0 else '#e74c3c' if c > 0 else '#95a5a6' for c in changes]

        fig = go.Figure(data=[go.Bar(
            x=names,
            y=changes,
            marker_color=colors,
            text=[f"{c:+.1f}kg" for c in changes],
            textposition='outside'
        )])
        fig.update_layout(
            height=300,
            margin=dict(t=20, b=20, l=20, r=20),
            yaxis_title="Zmena (kg)",
            showlegend=False
        )
        st.plotly_chart(fig, use_container_width=True)

    st.markdown("---")

    # Recent Activity
    st.markdown("### 🕐 Posledná aktivita")

    recent = sorted(clients, key=lambda c: c.last_checkin, reverse=True)[:5]
    for client in recent:
        col1, col2, col3, col4 = st.columns([3, 2, 2, 1])
        with col1:
            status_emoji = {"active": "🟢", "stagnating": "🟡", "problem": "🔴"}.get(client.status, "⚪")
            st.write(f"{status_emoji} **{client.name}**")
        with col2:
            st.write(f"{client.current_weight_kg}kg ({client.weight_change:+.1f})")
        with col3:
            days = client.days_since_checkin
            if days == 0:
                st.write("Dnes")
            elif days == 1:
                st.write("Včera")
            else:
                st.write(f"Pred {days} dňami")
        with col4:
            if st.button("→", key=f"recent_{client.id}"):
                st.session_state.selected_client = client.id
                st.session_state.page = 'client_detail'
                st.rerun()


def render_clients_list():
    """Render client list view"""
    st.markdown('<div class="main-header">👥 Klienti</div>', unsafe_allow_html=True)

    clients = st.session_state.clients

    # Filters
    col1, col2, col3 = st.columns([2, 2, 2])
    with col1:
        search = st.text_input("🔍 Hľadať", placeholder="Meno alebo email...")
    with col2:
        status_filter = st.selectbox("Status", ["Všetci", "Aktívni", "Stagnujúci", "Problém"])
    with col3:
        sort_by = st.selectbox("Zoradiť podľa", ["Posledný check-in", "Meno", "Progres"])

    st.markdown("---")

    # Filter clients
    filtered = clients
    if search:
        search_lower = search.lower()
        filtered = [c for c in filtered if search_lower in c.name.lower() or search_lower in c.email.lower()]

    if status_filter == "Aktívni":
        filtered = [c for c in filtered if c.status == "active"]
    elif status_filter == "Stagnujúci":
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

    # Display clients
    for client in filtered:
        status_emoji = {"active": "🟢", "stagnating": "🟡", "problem": "🔴"}.get(client.status, "⚪")

        with st.container():
            col1, col2, col3, col4 = st.columns([3, 2, 3, 1])

            with col1:
                st.markdown(f"### {status_emoji} {client.name}")
                st.caption(f"{client.age} rokov, {'Muž' if client.gender == 'male' else 'Žena'}")

            with col2:
                st.write(f"**Cieľ:** {client.goal}")
                weight_change = client.weight_change
                change_emoji = "↓" if weight_change < 0 else "↑" if weight_change > 0 else "→"
                st.write(f"**Váha:** {client.current_weight_kg}kg ({change_emoji}{abs(weight_change):.1f}kg)")

            with col3:
                progress = client.progress_percent
                st.write(f"**Progres:** {progress:.0f}%")
                st.progress(progress / 100)

                days = client.days_since_checkin
                if days > 7:
                    st.caption(f"⚠️ Check-in pred {days} dňami")
                else:
                    st.caption(f"✅ Check-in pred {days} dňami")

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
    """Generate meal and training plans"""
    progress = st.progress(0)
    status = st.empty()

    try:
        status.text("🔄 Pripájam sa k Gemini 2.5 Pro...")
        progress.progress(10)

        ai = FitAIGenerator(api_key=api_key)

        status.text("📊 Analyzujem profil...")
        progress.progress(25)
        segment = ai.segment_client(profile)
        st.session_state.segment = segment

        status.text("🍽️ Generujem jedálniček...")
        progress.progress(50)
        meal_plan = ai.generate_meal_plan(profile, segment)

        status.text("💪 Generujem tréningový plán...")
        progress.progress(75)
        training_plan = ai.generate_training_plan(profile, segment)

        # Store plans
        st.session_state.meal_plan = meal_plan
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
        st.error(f"❌ Chyba: {e}")


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
                    pdf_gen.generate_pdf(display_meal, tmp.name, f"Jedálniček - {profile.name}")
                    with open(tmp.name, "rb") as f:
                        st.download_button("📥 Stiahnuť PDF", f.read(),
                                           f"jedalnicky_{profile.name.replace(' ', '_')}.pdf",
                                           "application/pdf", use_container_width=True)
            except:
                pass

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
                    pdf_gen.generate_pdf(display_training, tmp.name, f"Tréning - {profile.name}")
                    with open(tmp.name, "rb") as f:
                        st.download_button("📥 Stiahnuť PDF", f.read(),
                                           f"trening_{profile.name.replace(' ', '_')}.pdf",
                                           "application/pdf", use_container_width=True)
            except:
                pass

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
            st.info("📧 Funkcia odosielania emailu bude dostupná v ďalšej verzii")

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

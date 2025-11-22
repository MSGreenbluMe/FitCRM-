"""
FIT CRM - Streamlit Application with Dashboard
Webove rozhranie pre fitness trenerov
"""
import streamlit as st
import sys
import os
from pathlib import Path
from datetime import datetime
import tempfile
import plotly.express as px
import plotly.graph_objects as go

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

from src.email_parser import EmailParser, ClientProfile
from src.ai_generator import FitAIGenerator, ClientSegment
from src.pdf_generator import PDFGenerator
from src.mock_data import get_mock_clients, get_dashboard_stats, ClientData

# Page config
st.set_page_config(
    page_title="FIT CRM",
    page_icon="💪",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
    .main-header {
        font-size: 2rem;
        font-weight: 700;
        color: #1a5276;
        padding: 0.5rem 0;
        border-bottom: 3px solid #3498db;
        margin-bottom: 1.5rem;
    }
    .stat-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        padding: 1.5rem;
        border-radius: 10px;
        text-align: center;
    }
    .stat-value {
        font-size: 2rem;
        font-weight: 700;
    }
    .stat-label {
        font-size: 0.9rem;
        opacity: 0.9;
    }
    .client-card {
        background: #f8f9fa;
        border-radius: 10px;
        padding: 1rem;
        margin: 0.5rem 0;
        border-left: 4px solid #3498db;
    }
    .client-card.active { border-left-color: #27ae60; }
    .client-card.stagnating { border-left-color: #f39c12; }
    .client-card.problem { border-left-color: #e74c3c; }
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
    .alert-box {
        background: #fff3cd;
        border: 1px solid #ffc107;
        border-radius: 8px;
        padding: 1rem;
        margin: 0.5rem 0;
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

        # API Status
        api_key = get_api_key()
        if api_key:
            st.success("✅ Gemini API")
        else:
            st.error("❌ API chýba")

        st.markdown("---")
        st.caption("FIT CRM v1.0 Demo")


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
                st.rerun()
    else:
        render_client_form()


def render_client_form():
    """Render client input form"""
    tab1, tab2 = st.tabs(["📧 Vložiť email", "✍️ Manuálne zadanie"])

    with tab1:
        email_text = st.text_area(
            "Email od klienta",
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
        st.session_state.meal_plan = ai.generate_meal_plan(profile, segment)

        status.text("💪 Generujem tréningový plán...")
        progress.progress(75)
        st.session_state.training_plan = ai.generate_training_plan(profile, segment)

        progress.progress(100)
        status.text("✅ Hotovo!")
        st.balloons()
        st.rerun()

    except Exception as e:
        st.error(f"❌ Chyba: {e}")


def render_generated_plans():
    """Render generated plans"""
    profile = st.session_state.profile
    segment = st.session_state.segment
    meal_plan = st.session_state.meal_plan
    training_plan = st.session_state.training_plan

    st.success(f"✅ Plány vygenerované pre: **{profile.name}**")

    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Kalórie", f"{segment.calorie_target} kcal")
    with col2:
        st.metric("Bielkoviny", f"{segment.protein_grams}g")
    with col3:
        st.metric("Sacharidy", f"{segment.carbs_grams}g")
    with col4:
        st.metric("Tuky", f"{segment.fat_grams}g")

    tab1, tab2 = st.tabs(["🍽️ Jedálniček", "💪 Tréningový plán"])

    with tab1:
        st.markdown(meal_plan)
        try:
            pdf_gen = PDFGenerator()
            with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as tmp:
                pdf_gen.generate_pdf(meal_plan, tmp.name, f"Jedálniček - {profile.name}")
                with open(tmp.name, "rb") as f:
                    st.download_button("📥 Stiahnuť PDF", f.read(),
                                       f"jedalnicky_{profile.name.replace(' ', '_')}.pdf",
                                       "application/pdf", use_container_width=True)
        except:
            pass

    with tab2:
        st.markdown(training_plan)
        try:
            pdf_gen = PDFGenerator()
            with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as tmp:
                pdf_gen.generate_pdf(training_plan, tmp.name, f"Tréning - {profile.name}")
                with open(tmp.name, "rb") as f:
                    st.download_button("📥 Stiahnuť PDF", f.read(),
                                       f"trening_{profile.name.replace(' ', '_')}.pdf",
                                       "application/pdf", use_container_width=True)
        except:
            pass

    if st.button("🔄 Nový klient", use_container_width=True):
        st.session_state.profile = None
        st.session_state.segment = None
        st.session_state.meal_plan = None
        st.session_state.training_plan = None
        st.rerun()


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

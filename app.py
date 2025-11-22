"""
FIT CRM - Streamlit Demo Application
Webove rozhranie pre generovanie fitness planov
"""
import streamlit as st
import sys
import os
from pathlib import Path
from datetime import datetime
import tempfile

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

from src.email_parser import EmailParser, ClientProfile
from src.ai_generator import FitAIGenerator, ClientSegment
from src.pdf_generator import PDFGenerator

# Page config
st.set_page_config(
    page_title="FIT CRM - Fitness Plan Generator",
    page_icon="💪",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: 700;
        color: #1a5276;
        text-align: center;
        padding: 1rem 0;
        border-bottom: 3px solid #3498db;
        margin-bottom: 2rem;
    }
    .sub-header {
        font-size: 1.2rem;
        color: #5d6d7e;
        text-align: center;
        margin-bottom: 2rem;
    }
    .stTabs [data-baseweb="tab-list"] {
        gap: 24px;
    }
    .stTabs [data-baseweb="tab"] {
        padding: 10px 20px;
    }
</style>
""", unsafe_allow_html=True)


def get_api_key():
    """Get API key from secrets or environment"""
    # Try Streamlit secrets first (for cloud deployment)
    try:
        key = st.secrets["gemini"]["api_key"]
        if key:
            return key
    except (KeyError, FileNotFoundError):
        pass

    # Fall back to environment variable
    return os.getenv('GEMINI_API_KEY', '')


def init_session_state():
    """Initialize session state variables"""
    if 'profile' not in st.session_state:
        st.session_state.profile = None
    if 'segment' not in st.session_state:
        st.session_state.segment = None
    if 'meal_plan' not in st.session_state:
        st.session_state.meal_plan = None
    if 'training_plan' not in st.session_state:
        st.session_state.training_plan = None
    if 'email_text' not in st.session_state:
        st.session_state.email_text = ''


def render_sidebar():
    """Render sidebar with sample data loader"""
    with st.sidebar:
        st.markdown("## ⚙️ Stav systemu")

        # Check API key
        api_key = get_api_key()
        if api_key:
            st.success("✅ Gemini API pripojene")
            st.caption("Model: gemini-2.5-pro")
        else:
            st.error("❌ Gemini API kluc chyba")
            st.caption("Nastav GEMINI_API_KEY v environment alebo Streamlit secrets")
            return

        st.markdown("---")

        # Sample data loader
        st.markdown("## 📧 Vzorove emaily")
        sample_dir = Path(__file__).parent / "tests" / "sample_emails"

        if sample_dir.exists():
            sample_files = list(sample_dir.glob("*.txt"))
            if sample_files:
                selected_sample = st.selectbox(
                    "Vyber vzorovy email",
                    options=["-- Vyber --"] + [f.stem for f in sample_files],
                    help="Nacitaj a automaticky parsuj vzorovy email"
                )

                if selected_sample != "-- Vyber --":
                    sample_path = sample_dir / f"{selected_sample}.txt"
                    if st.button("📥 Nacitat a parsovat", use_container_width=True):
                        try:
                            email_content = sample_path.read_text(encoding="utf-8")
                            st.session_state.email_text = email_content
                            parser = EmailParser()
                            profile = parser.parse_email(email_content)
                            st.session_state.profile = profile
                            # Reset generated plans
                            st.session_state.segment = None
                            st.session_state.meal_plan = None
                            st.session_state.training_plan = None
                            st.success(f"✅ Parsovane: {profile.name}")
                            st.rerun()
                        except Exception as e:
                            st.error(f"❌ Chyba: {e}")

        st.markdown("---")
        st.markdown("### 📊 O aplikacii")
        st.markdown("""
        **FIT CRM** automatizuje:
        - Parsovanie klientskych emailov
        - Generovanie jedalnicky (AI)
        - Generovanie treningovych planov (AI)
        - Export do PDF
        """)

        st.markdown("---")
        st.markdown("Made with ❤️ for fitness trainers")


def render_client_form():
    """Render client input form"""
    profile = st.session_state.profile

    st.markdown("### 📝 Udaje klienta")

    # If profile is already parsed, show it
    if profile:
        st.success(f"✅ Klient: **{profile.name}** ({profile.email})")

        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Vek", f"{profile.age} rokov")
        with col2:
            st.metric("Pohlavie", "Muz" if profile.gender == "male" else "Zena")
        with col3:
            st.metric("Vaha", f"{profile.weight} kg")
        with col4:
            st.metric("Vyska", f"{profile.height} cm")

        st.info(f"**Ciel:** {profile.goal}")

        col1, col2 = st.columns(2)
        with col1:
            st.write(f"**Aktivita:** {profile.activity_level}")
            st.write(f"**Skusenosti:** {profile.experience_level}")
        with col2:
            if profile.dietary_restrictions:
                st.write(f"**Obmedzenia:** {', '.join(profile.dietary_restrictions)}")
            if profile.health_conditions:
                st.write(f"**Zdravie:** {', '.join(profile.health_conditions)}")

        st.markdown("---")

        col1, col2 = st.columns(2)
        with col1:
            if st.button("🚀 Generovat plany", type="primary", use_container_width=True):
                api_key = get_api_key()
                if not api_key:
                    st.error("❌ Gemini API kluc nie je nastaveny")
                    return
                generate_plans(profile, api_key)

        with col2:
            if st.button("🔄 Novy klient", use_container_width=True):
                st.session_state.profile = None
                st.session_state.segment = None
                st.session_state.meal_plan = None
                st.session_state.training_plan = None
                st.session_state.email_text = ''
                st.rerun()

    else:
        # Show form for manual input or email paste
        tab1, tab2 = st.tabs(["📧 Vlozit email", "✍️ Manualne zadanie"])

        with tab1:
            st.markdown("Vloz email od klienta a klikni na parsovat:")
            email_text = st.text_area(
                "Email text",
                value=st.session_state.email_text,
                height=300,
                help="Vloz cely text emailu od klienta",
                placeholder="""Priklad:
Meno: Jan Novak
Email: jan@example.com
Vek: 30
Pohlavie: muz
Vaha: 85 kg
Vyska: 180 cm
Ciel: Chcem schudnut
Aktivita: sedave zamestnanie
Skusenosti: zaciatocnik"""
            )

            if st.button("📋 Parsovat email", use_container_width=True, type="primary"):
                if not email_text.strip():
                    st.error("❌ Vloz text emailu")
                else:
                    try:
                        parser = EmailParser()
                        profile = parser.parse_email(email_text)
                        st.session_state.profile = profile
                        st.session_state.email_text = email_text
                        st.success(f"✅ Parsovane: {profile.name}")
                        st.rerun()
                    except Exception as e:
                        st.error(f"❌ Chyba pri parsovani: {e}")

        with tab2:
            col1, col2 = st.columns(2)

            with col1:
                name = st.text_input("Meno a priezvisko*")
                email = st.text_input("Email*")

                col_age_gender = st.columns(2)
                with col_age_gender[0]:
                    age = st.number_input("Vek*", min_value=15, max_value=100, value=30)
                with col_age_gender[1]:
                    gender = st.selectbox("Pohlavie*", options=["Muz", "Zena"])

                col_weight_height = st.columns(2)
                with col_weight_height[0]:
                    weight = st.number_input("Vaha (kg)*", min_value=30.0, max_value=250.0, value=80.0, step=0.5)
                with col_weight_height[1]:
                    height = st.number_input("Vyska (cm)*", min_value=100.0, max_value=250.0, value=175.0, step=1.0)

            with col2:
                goal = st.text_area("Ciel*", height=80, help="Napr: Chcem schudnut 10 kg")
                activity_level = st.selectbox(
                    "Uroven aktivity",
                    options=["Sedava (kancelaria)", "Mierna (obcasny pohyb)", "Aktivna (pravidelny sport)", "Velmi aktivna (denne cvicenie)"]
                )
                experience = st.selectbox(
                    "Skusenosti s cvicenim",
                    options=["Zaciatocnik", "Mierne pokrocily", "Pokrocily"]
                )
                restrictions = st.text_input("Potravinove obmedzenia", help="Napr: bezlepkova dieta")

            if st.button("💾 Ulozit udaje", type="primary", use_container_width=True):
                if not name or not email or not goal:
                    st.error("❌ Vyplz vsetky povinne polia oznacene *")
                else:
                    activity_map = {
                        "Sedava (kancelaria)": "sedentary",
                        "Mierna (obcasny pohyb)": "light",
                        "Aktivna (pravidelny sport)": "active",
                        "Velmi aktivna (denne cvicenie)": "very_active"
                    }
                    experience_map = {
                        "Zaciatocnik": "beginner",
                        "Mierne pokrocily": "intermediate",
                        "Pokrocily": "advanced"
                    }

                    profile = ClientProfile(
                        name=name,
                        email=email,
                        age=age,
                        gender="male" if gender == "Muz" else "female",
                        weight=weight,
                        height=height,
                        goal=goal,
                        activity_level=activity_map.get(activity_level, "moderate"),
                        experience_level=experience_map.get(experience, "beginner"),
                        dietary_restrictions=[r.strip() for r in restrictions.split(",") if r.strip()] if restrictions else []
                    )
                    st.session_state.profile = profile
                    st.success(f"✅ Ulozene: {profile.name}")
                    st.rerun()


def generate_plans(profile: ClientProfile, api_key: str):
    """Generate meal and training plans"""

    progress_bar = st.progress(0)
    status_text = st.empty()

    try:
        # Initialize AI generator
        status_text.text("🔄 Pripajam sa k Gemini 2.5 Pro...")
        progress_bar.progress(10)

        ai = FitAIGenerator(api_key=api_key)

        # Segment client
        status_text.text("📊 Analyzujem profil klienta...")
        progress_bar.progress(25)

        segment = ai.segment_client(profile)
        st.session_state.segment = segment

        # Generate meal plan
        status_text.text("🍽️ Generujem jedalnicky (30-60 sekund)...")
        progress_bar.progress(45)

        meal_plan = ai.generate_meal_plan(profile, segment)
        st.session_state.meal_plan = meal_plan

        # Generate training plan
        status_text.text("💪 Generujem treningovy plan (30-60 sekund)...")
        progress_bar.progress(75)

        training_plan = ai.generate_training_plan(profile, segment)
        st.session_state.training_plan = training_plan

        # Done
        progress_bar.progress(100)
        status_text.text("✅ Hotovo!")

        st.balloons()
        st.rerun()

    except Exception as e:
        progress_bar.empty()
        status_text.empty()
        st.error(f"❌ Chyba pri generovani: {e}")


def render_results():
    """Render generated plans"""
    profile = st.session_state.profile
    segment = st.session_state.segment
    meal_plan = st.session_state.meal_plan
    training_plan = st.session_state.training_plan

    st.markdown("---")
    st.markdown("## 📋 Vygenerovane plany pre " + profile.name)

    # Nutrition targets
    st.markdown("### 🎯 Nutricne ciele")
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric("Kalorie", f"{segment.calorie_target} kcal")
    with col2:
        st.metric("Bielkoviny", f"{segment.protein_grams}g")
    with col3:
        st.metric("Sacharidy", f"{segment.carbs_grams}g")
    with col4:
        st.metric("Tuky", f"{segment.fat_grams}g")

    if segment.reasoning:
        st.info(f"**Zdovodnenie:** {segment.reasoning}")

    # Plans in tabs
    tab1, tab2 = st.tabs(["🍽️ Jedalnicky", "💪 Treningovy plan"])

    with tab1:
        st.markdown(meal_plan)

        # PDF download
        try:
            pdf_gen = PDFGenerator()
            with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as tmp:
                pdf_gen.generate_pdf(meal_plan, tmp.name, f"Jedalnicky - {profile.name}")
                with open(tmp.name, "rb") as f:
                    pdf_bytes = f.read()

                st.download_button(
                    label="📥 Stiahnut jedalnicky (PDF)",
                    data=pdf_bytes,
                    file_name=f"jedalnicky_{profile.name.replace(' ', '_')}.pdf",
                    mime="application/pdf",
                    use_container_width=True
                )
        except Exception as e:
            st.warning(f"PDF generovanie nedostupne: {e}")

    with tab2:
        st.markdown(training_plan)

        # PDF download
        try:
            pdf_gen = PDFGenerator()
            with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as tmp:
                pdf_gen.generate_pdf(training_plan, tmp.name, f"Treningovy Plan - {profile.name}")
                with open(tmp.name, "rb") as f:
                    pdf_bytes = f.read()

                st.download_button(
                    label="📥 Stiahnut treningovy plan (PDF)",
                    data=pdf_bytes,
                    file_name=f"treningovy_plan_{profile.name.replace(' ', '_')}.pdf",
                    mime="application/pdf",
                    use_container_width=True
                )
        except Exception as e:
            st.warning(f"PDF generovanie nedostupne: {e}")

    # Reset button
    st.markdown("---")
    if st.button("🔄 Novy klient", use_container_width=True):
        st.session_state.profile = None
        st.session_state.segment = None
        st.session_state.meal_plan = None
        st.session_state.training_plan = None
        st.session_state.email_text = ''
        st.rerun()


def main():
    """Main application"""
    init_session_state()

    # Header
    st.markdown('<div class="main-header">💪 FIT CRM</div>', unsafe_allow_html=True)
    st.markdown('<div class="sub-header">Automatizovane generovanie fitness planov pre vasich klientov</div>', unsafe_allow_html=True)

    # Sidebar
    render_sidebar()

    # Main content
    if st.session_state.meal_plan and st.session_state.training_plan:
        render_results()
    else:
        render_client_form()


if __name__ == "__main__":
    main()

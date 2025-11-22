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
import base64

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
    .success-box {
        background-color: #d5f5e3;
        border-left: 5px solid #27ae60;
        padding: 1rem;
        border-radius: 5px;
        margin: 1rem 0;
    }
    .info-box {
        background-color: #d6eaf8;
        border-left: 5px solid #3498db;
        padding: 1rem;
        border-radius: 5px;
        margin: 1rem 0;
    }
    .metric-card {
        background-color: #f8f9fa;
        padding: 1rem;
        border-radius: 10px;
        text-align: center;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
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
        return st.secrets["gemini"]["api_key"]
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
    if 'api_key' not in st.session_state:
        st.session_state.api_key = get_api_key()


def get_pdf_download_link(pdf_content: bytes, filename: str, text: str) -> str:
    """Generate a download link for PDF"""
    b64 = base64.b64encode(pdf_content).decode()
    return f'<a href="data:application/pdf;base64,{b64}" download="{filename}" class="download-btn">{text}</a>'


def render_sidebar():
    """Render sidebar with API configuration"""
    with st.sidebar:
        st.markdown("## ⚙️ Nastavenia")

        # Check if API key is from secrets
        has_secrets_key = False
        try:
            if st.secrets["gemini"]["api_key"]:
                has_secrets_key = True
        except (KeyError, FileNotFoundError):
            pass

        if has_secrets_key:
            st.success("✅ API kluc nakonfigurovany")
            st.caption("(z Streamlit secrets)")
        else:
            # API Key input
            api_key = st.text_input(
                "Gemini API Key",
                value=st.session_state.api_key,
                type="password",
                help="Ziskaj API kluc z: https://makersuite.google.com/app/apikey"
            )
            st.session_state.api_key = api_key

            if api_key:
                st.success("✅ API kluc nastaveny")
            else:
                st.warning("⚠️ Zadaj Gemini API kluc")
                st.markdown("[Ziskat API kluc →](https://makersuite.google.com/app/apikey)")

        st.markdown("---")

        # Sample data loader
        st.markdown("## 📧 Vzorove data")
        sample_dir = Path(__file__).parent / "tests" / "sample_emails"

        if sample_dir.exists():
            sample_files = list(sample_dir.glob("*.txt"))
            if sample_files:
                selected_sample = st.selectbox(
                    "Nacitaj vzorovy email",
                    options=["-- Vyber --"] + [f.stem for f in sample_files],
                    help="Nacitaj vzorovy email pre testovanie"
                )

                if selected_sample != "-- Vyber --":
                    sample_path = sample_dir / f"{selected_sample}.txt"
                    if st.button("📥 Nacitat", use_container_width=True):
                        st.session_state.sample_email = sample_path.read_text(encoding="utf-8")
                        st.rerun()

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
    st.markdown("### 📝 Udaje klienta")

    # Check for sample email in session state
    sample_email = st.session_state.get('sample_email', '')

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("#### Zakladne udaje")
        name = st.text_input("Meno a priezvisko*", value="")
        email = st.text_input("Email*", value="")

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
        st.markdown("#### Ciele a skusenosti")
        goal = st.text_area(
            "Ciel*",
            value="",
            height=80,
            help="Napr: Chcem schudnut 10 kg, nabrat svaly, zlepsit kondiciu..."
        )

        activity_level = st.selectbox(
            "Uroven aktivity",
            options=["Sedava (kancelaria)", "Mierna (obcasny pohyb)", "Aktivna (pravidelny sport)", "Velmi aktivna (denne cvicenie)"],
            index=0
        )

        experience = st.selectbox(
            "Skusenosti s cvicenim",
            options=["Zaciatocnik", "Mierne pokrocily", "Pokrocily"],
            index=0
        )

        restrictions = st.text_input(
            "Potravinove obmedzenia",
            value="",
            help="Napr: bezlepkova dieta, laktozova intolerancia, vegetarian..."
        )

    # Alternative: paste email
    with st.expander("📧 Alebo vloz email od klienta"):
        email_text = st.text_area(
            "Email text",
            value=sample_email,
            height=200,
            help="Vloz cely text emailu od klienta"
        )

        if email_text and st.button("📋 Parsovat email", use_container_width=True):
            try:
                parser = EmailParser()
                profile = parser.parse_email(email_text)
                st.session_state.profile = profile
                st.success(f"✅ Email uspesne parsovany pre: {profile.name}")
                st.rerun()
            except Exception as e:
                st.error(f"❌ Chyba pri parsovani: {e}")

    # Clear sample email after use
    if 'sample_email' in st.session_state:
        del st.session_state.sample_email

    st.markdown("---")

    # Submit button
    if st.button("🚀 Generovat plany", type="primary", use_container_width=True):
        if not st.session_state.api_key:
            st.error("❌ Najprv zadaj Gemini API kluc v bocznom paneli")
            return

        if not name or not email or not goal:
            st.error("❌ Vyplz vsetky povinne polia oznacene *")
            return

        # Create profile from form
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
        generate_plans(profile)


def generate_plans(profile: ClientProfile):
    """Generate meal and training plans"""

    progress_bar = st.progress(0)
    status_text = st.empty()

    try:
        # Initialize AI generator
        status_text.text("🔄 Inicializujem AI...")
        progress_bar.progress(10)

        ai = FitAIGenerator(api_key=st.session_state.api_key)

        # Segment client
        status_text.text("📊 Analyzujem profil klienta...")
        progress_bar.progress(25)

        segment = ai.segment_client(profile)
        st.session_state.segment = segment

        # Generate meal plan
        status_text.text("🍽️ Generujem jedalnicky (moze trvat 30-60 sekund)...")
        progress_bar.progress(45)

        meal_plan = ai.generate_meal_plan(profile, segment)
        st.session_state.meal_plan = meal_plan

        # Generate training plan
        status_text.text("💪 Generujem treningovy plan (moze trvat 30-60 sekund)...")
        progress_bar.progress(75)

        training_plan = ai.generate_training_plan(profile, segment)
        st.session_state.training_plan = training_plan

        # Done
        progress_bar.progress(100)
        status_text.text("✅ Hotovo!")

        st.success("🎉 Plany boli uspesne vygenerovane!")
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

    if not all([profile, segment, meal_plan, training_plan]):
        return

    st.markdown("---")
    st.markdown("## 📋 Vygenerovane plany")

    # Client summary
    st.markdown("### 👤 Klient")
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric("Meno", profile.name)
    with col2:
        st.metric("Vek", f"{profile.age} rokov")
    with col3:
        st.metric("Vaha", f"{profile.weight} kg")
    with col4:
        st.metric("Vyska", f"{profile.height} cm")

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

    st.info(f"**Zdovodnenie:** {segment.reasoning}")

    # Plans in tabs
    tab1, tab2 = st.tabs(["🍽️ Jedalnicky", "💪 Treningovy plan"])

    with tab1:
        st.markdown(meal_plan)

        # PDF download
        if st.button("📥 Stiahnut jedalnicky ako PDF", key="meal_pdf"):
            with st.spinner("Generujem PDF..."):
                try:
                    pdf_gen = PDFGenerator()
                    with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as tmp:
                        pdf_gen.generate_pdf(meal_plan, tmp.name, f"Jedalnicky - {profile.name}")
                        with open(tmp.name, "rb") as f:
                            pdf_bytes = f.read()

                        st.download_button(
                            label="💾 Stiahnut PDF",
                            data=pdf_bytes,
                            file_name=f"jedalnicky_{profile.name.replace(' ', '_')}.pdf",
                            mime="application/pdf"
                        )
                except Exception as e:
                    st.error(f"Chyba pri generovani PDF: {e}")

    with tab2:
        st.markdown(training_plan)

        # PDF download
        if st.button("📥 Stiahnut treningovy plan ako PDF", key="training_pdf"):
            with st.spinner("Generujem PDF..."):
                try:
                    pdf_gen = PDFGenerator()
                    with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as tmp:
                        pdf_gen.generate_pdf(training_plan, tmp.name, f"Treningovy Plan - {profile.name}")
                        with open(tmp.name, "rb") as f:
                            pdf_bytes = f.read()

                        st.download_button(
                            label="💾 Stiahnut PDF",
                            data=pdf_bytes,
                            file_name=f"treningovy_plan_{profile.name.replace(' ', '_')}.pdf",
                            mime="application/pdf"
                        )
                except Exception as e:
                    st.error(f"Chyba pri generovani PDF: {e}")

    # Reset button
    st.markdown("---")
    if st.button("🔄 Novy klient", use_container_width=True):
        st.session_state.profile = None
        st.session_state.segment = None
        st.session_state.meal_plan = None
        st.session_state.training_plan = None
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

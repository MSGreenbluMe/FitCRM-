"""Configuration settings for FIT CRM"""
import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Base paths
BASE_DIR = Path(__file__).parent
SRC_DIR = BASE_DIR / "src"
PROMPTS_DIR = BASE_DIR / "prompts"
TEMPLATES_DIR = BASE_DIR / "templates"
OUTPUT_DIR = BASE_DIR / "output"
LOGS_DIR = BASE_DIR / "logs"

# Ensure directories exist
OUTPUT_DIR.mkdir(exist_ok=True)
LOGS_DIR.mkdir(exist_ok=True)

# API Configuration
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-2.5-flash-lite")

# Email Configuration
EMAIL_USER = os.getenv("EMAIL_USER", "")
EMAIL_PASS = os.getenv("EMAIL_PASS", "")
SMTP_HOST = os.getenv("SMTP_HOST", "smtp.gmail.com")
SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))

# Trainer Configuration
TRAINER_NAME = os.getenv("TRAINER_NAME", "Fitness Trainer")
TRAINER_EMAIL = os.getenv("TRAINER_EMAIL", "")

# Language settings
DEFAULT_LANGUAGE = "sk"  # Slovak

# Activity level multipliers for TDEE calculation
ACTIVITY_MULTIPLIERS = {
    "sedentary": 1.2,
    "light": 1.375,
    "moderate": 1.55,
    "active": 1.725,
    "very_active": 1.9
}

# Goal calorie adjustments
GOAL_ADJUSTMENTS = {
    "weight_loss": -500,
    "muscle_gain": 300,
    "maintenance": 0,
    "aggressive_loss": -750,
    "lean_bulk": 200
}

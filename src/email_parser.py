"""Email Parser - Parse intake emails into structured client profiles"""
import re
from dataclasses import dataclass, field
from typing import Optional, List
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


@dataclass
class ClientProfile:
    """Structured client profile data"""
    # Required fields
    name: str
    email: str
    age: int
    gender: str
    weight: float  # kg
    height: float  # cm
    goal: str

    # Optional fields
    activity_level: str = "moderate"
    experience_level: str = "beginner"
    dietary_restrictions: List[str] = field(default_factory=list)
    health_conditions: List[str] = field(default_factory=list)
    motivation: str = ""
    preferred_foods: List[str] = field(default_factory=list)
    disliked_foods: List[str] = field(default_factory=list)
    available_equipment: List[str] = field(default_factory=list)
    training_days_per_week: int = 3

    # Metadata
    raw_email: str = ""
    parsed_at: str = field(default_factory=lambda: datetime.now().isoformat())

    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization"""
        return {
            "name": self.name,
            "email": self.email,
            "age": self.age,
            "gender": self.gender,
            "weight": self.weight,
            "height": self.height,
            "goal": self.goal,
            "activity_level": self.activity_level,
            "experience_level": self.experience_level,
            "dietary_restrictions": self.dietary_restrictions,
            "health_conditions": self.health_conditions,
            "motivation": self.motivation,
            "preferred_foods": self.preferred_foods,
            "disliked_foods": self.disliked_foods,
            "available_equipment": self.available_equipment,
            "training_days_per_week": self.training_days_per_week,
            "parsed_at": self.parsed_at
        }


class EmailParser:
    """Parse intake emails into structured ClientProfile objects"""

    # Field patterns for Slovak/Czech emails
    FIELD_PATTERNS = {
        "name": [
            r"(?:meno|jmeno|name)[:\s]+([^\n]+)",
            r"(?:celé\s+)?(?:meno|jmeno)[:\s]+([^\n]+)",
        ],
        "email": [
            r"(?:e-?mail|email)[:\s]+([^\s\n]+@[^\s\n]+)",
            r"([a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,})",
        ],
        "age": [
            r"(?:vek|věk|age)[:\s]+(\d+)",
            r"(\d+)\s*(?:rokov|let|years)",
        ],
        "gender": [
            r"(?:pohlavie|pohlaví|gender)[:\s]+([^\n]+)",
            r"(?:som\s+)?(muž|žena|man|woman|male|female)",
        ],
        "weight": [
            r"(?:váha|hmotnost|weight)[:\s]+(\d+(?:[.,]\d+)?)\s*(?:kg)?",
            r"(\d+(?:[.,]\d+)?)\s*kg",
        ],
        "height": [
            r"(?:výška|vyska|height)[:\s]+(\d+(?:[.,]\d+)?)\s*(?:cm)?",
            r"(\d+(?:[.,]\d+)?)\s*cm",
        ],
        "goal": [
            r"(?:cieľ|cíl|goal)[:\s]+([^\n]+)",
            r"(?:chcem|chci)[:\s]*([^\n]+)",
        ],
        "activity": [
            r"(?:aktivita|activity|pohyb)[:\s]+([^\n]+)",
            r"(?:práce|prace|work|zamestnanie)[:\s]+([^\n]+)",
        ],
        "experience": [
            r"(?:skúsenosti|zkušenosti|experience|úroveň|uroven)[:\s]+([^\n]+)",
        ],
        "restrictions": [
            r"(?:obmedzenia|omezení|alergie|restrictions)[:\s]+([^\n]+)",
            r"(?:nejem|nejím|nesnášam)[:\s]*([^\n]+)",
        ],
        "health": [
            r"(?:zdravotné\s+problémy|zdravotní\s+problémy|health)[:\s]+([^\n]+)",
            r"(?:ochorenia|nemoci|conditions)[:\s]+([^\n]+)",
        ],
        "motivation": [
            r"(?:motivácia|motivace|motivation)[:\s]+([^\n]+)",
            r"(?:prečo|proč|why)[:\s]+([^\n]+)",
        ],
    }

    # Gender normalization
    GENDER_MAP = {
        "muž": "male",
        "muz": "male",
        "man": "male",
        "male": "male",
        "m": "male",
        "žena": "female",
        "zena": "female",
        "woman": "female",
        "female": "female",
        "f": "female",
        "ž": "female",
    }

    # Activity level normalization
    ACTIVITY_MAP = {
        "sedavé": "sedentary",
        "sedave": "sedentary",
        "sedentary": "sedentary",
        "kancelária": "sedentary",
        "kancelaria": "sedentary",
        "office": "sedentary",
        "ľahká": "light",
        "lahka": "light",
        "light": "light",
        "mierna": "moderate",
        "moderate": "moderate",
        "stredná": "moderate",
        "stredna": "moderate",
        "aktívna": "active",
        "aktivna": "active",
        "active": "active",
        "vysoká": "very_active",
        "vysoka": "very_active",
        "very_active": "very_active",
        "športovec": "very_active",
        "sportovec": "very_active",
    }

    # Experience level normalization
    EXPERIENCE_MAP = {
        "začiatočník": "beginner",
        "zaciatocnik": "beginner",
        "začátečník": "beginner",
        "zacatecnik": "beginner",
        "beginner": "beginner",
        "nový": "beginner",
        "novy": "beginner",
        "pokročilý": "intermediate",
        "pokrocily": "intermediate",
        "intermediate": "intermediate",
        "stredný": "intermediate",
        "stredny": "intermediate",
        "expert": "advanced",
        "advanced": "advanced",
        "skúsený": "advanced",
        "skuseny": "advanced",
    }

    def __init__(self):
        self.logger = logging.getLogger(self.__class__.__name__)

    def parse_email(self, email_text: str) -> ClientProfile:
        """
        Parse an intake email and return a structured ClientProfile.

        Args:
            email_text: Raw email text content

        Returns:
            ClientProfile with parsed data

        Raises:
            ValueError: If required fields cannot be parsed
        """
        self.logger.info("Parsing email...")

        # Normalize text
        text = email_text.strip()
        text_lower = text.lower()

        # Extract required fields
        name = self._extract_field("name", text)
        email = self._extract_field("email", text)
        age = self._extract_number("age", text)
        gender = self._normalize_gender(self._extract_field("gender", text))
        weight = self._extract_float("weight", text)
        height = self._extract_float("height", text)
        goal = self._extract_field("goal", text)

        # Validate required fields
        if not name:
            raise ValueError("Could not parse client name from email")
        if not email:
            raise ValueError("Could not parse client email from email")
        if not age:
            raise ValueError("Could not parse client age from email")
        if not gender:
            gender = "male"  # Default fallback
        if not weight:
            raise ValueError("Could not parse client weight from email")
        if not height:
            raise ValueError("Could not parse client height from email")
        if not goal:
            goal = "general fitness"  # Default fallback

        # Extract optional fields
        activity_raw = self._extract_field("activity", text) or ""
        activity_level = self._normalize_activity(activity_raw)

        experience_raw = self._extract_field("experience", text) or ""
        experience_level = self._normalize_experience(experience_raw)

        restrictions_raw = self._extract_field("restrictions", text) or ""
        dietary_restrictions = self._parse_list(restrictions_raw)

        health_raw = self._extract_field("health", text) or ""
        health_conditions = self._parse_list(health_raw)

        motivation = self._extract_field("motivation", text) or ""

        # Create profile
        profile = ClientProfile(
            name=name.strip(),
            email=email.strip().lower(),
            age=age,
            gender=gender,
            weight=weight,
            height=height,
            goal=goal.strip(),
            activity_level=activity_level,
            experience_level=experience_level,
            dietary_restrictions=dietary_restrictions,
            health_conditions=health_conditions,
            motivation=motivation.strip(),
            raw_email=email_text
        )

        self.logger.info(f"Successfully parsed profile for: {profile.name}")
        return profile

    def _extract_field(self, field_name: str, text: str) -> Optional[str]:
        """Extract a field value using multiple patterns"""
        patterns = self.FIELD_PATTERNS.get(field_name, [])

        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE | re.MULTILINE)
            if match:
                return match.group(1).strip()

        return None

    def _extract_number(self, field_name: str, text: str) -> Optional[int]:
        """Extract an integer field value"""
        value = self._extract_field(field_name, text)
        if value:
            try:
                return int(re.search(r"\d+", value).group())
            except (ValueError, AttributeError):
                pass
        return None

    def _extract_float(self, field_name: str, text: str) -> Optional[float]:
        """Extract a float field value"""
        value = self._extract_field(field_name, text)
        if value:
            try:
                # Handle both comma and period as decimal separator
                clean_value = value.replace(",", ".")
                match = re.search(r"\d+(?:\.\d+)?", clean_value)
                if match:
                    return float(match.group())
            except (ValueError, AttributeError):
                pass
        return None

    def _normalize_gender(self, value: Optional[str]) -> str:
        """Normalize gender value to male/female"""
        if not value:
            return "male"

        value_lower = value.lower().strip()

        for key, normalized in self.GENDER_MAP.items():
            if key in value_lower:
                return normalized

        return "male"  # Default

    def _normalize_activity(self, value: str) -> str:
        """Normalize activity level"""
        if not value:
            return "moderate"

        value_lower = value.lower().strip()

        for key, normalized in self.ACTIVITY_MAP.items():
            if key in value_lower:
                return normalized

        return "moderate"  # Default

    def _normalize_experience(self, value: str) -> str:
        """Normalize experience level"""
        if not value:
            return "beginner"

        value_lower = value.lower().strip()

        for key, normalized in self.EXPERIENCE_MAP.items():
            if key in value_lower:
                return normalized

        return "beginner"  # Default

    def _parse_list(self, value: str) -> List[str]:
        """Parse a comma/semicolon separated list"""
        if not value or value.lower() in ["žiadne", "ziadne", "žádné", "zadne", "none", "nie", "ne", "-"]:
            return []

        # Split by comma, semicolon, or "a"/"and"
        items = re.split(r"[,;]|\s+a\s+|\s+and\s+", value)
        return [item.strip() for item in items if item.strip()]

"""AI Generator - Generate meal and training plans using Google Gemini"""
import json
import logging
import time
from pathlib import Path
from typing import Dict, Any, Optional
from dataclasses import dataclass

import google.generativeai as genai

from src.email_parser import ClientProfile


logger = logging.getLogger(__name__)


@dataclass
class ClientSegment:
    """Segmentation result from AI analysis"""
    segment: str
    calorie_target: int
    protein_grams: int
    carbs_grams: int
    fat_grams: int
    macro_ratio: Dict[str, int]
    training_frequency: str
    reasoning: str

    @classmethod
    def from_dict(cls, data: dict) -> "ClientSegment":
        return cls(
            segment=data.get("segment", "general"),
            calorie_target=int(data.get("calorie_target", 2000)),
            protein_grams=int(data.get("protein_grams", 150)),
            carbs_grams=int(data.get("carbs_grams", 200)),
            fat_grams=int(data.get("fat_grams", 70)),
            macro_ratio=data.get("macro_ratio", {"protein": 30, "carbs": 40, "fat": 30}),
            training_frequency=data.get("training_frequency", "3x_per_week"),
            reasoning=data.get("reasoning", "")
        )


class FitAIGenerator:
    """Generate fitness plans using Google Gemini AI"""

    def __init__(self, api_key: str, model_name: str = "gemini-1.5-flash"):
        """
        Initialize the AI generator.

        Args:
            api_key: Google Gemini API key
            model_name: Model to use (default: gemini-1.5-flash)
        """
        if not api_key:
            raise ValueError("Gemini API key is required")

        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel(model_name)
        self.logger = logging.getLogger(self.__class__.__name__)

        # Load prompt templates
        self.prompts_dir = Path(__file__).parent.parent / "prompts"
        self.prompts = self._load_prompts()

    def _load_prompts(self) -> Dict[str, str]:
        """Load prompt templates from files"""
        prompts = {}
        prompt_files = ["segmentation", "meal_plan", "training_plan"]

        for name in prompt_files:
            path = self.prompts_dir / f"{name}.txt"
            if path.exists():
                prompts[name] = path.read_text(encoding="utf-8")
            else:
                self.logger.warning(f"Prompt file not found: {path}")

        return prompts

    def _generate_with_retry(
        self,
        prompt: str,
        max_retries: int = 3,
        initial_delay: float = 1.0
    ) -> str:
        """
        Generate content with exponential backoff retry.

        Args:
            prompt: The prompt to send
            max_retries: Maximum number of retries
            initial_delay: Initial delay in seconds

        Returns:
            Generated text content
        """
        delay = initial_delay

        for attempt in range(max_retries + 1):
            try:
                response = self.model.generate_content(prompt)
                return response.text
            except Exception as e:
                if attempt == max_retries:
                    raise

                self.logger.warning(
                    f"Generation failed (attempt {attempt + 1}/{max_retries + 1}): {e}"
                )
                time.sleep(delay)
                delay *= 2  # Exponential backoff

        return ""

    def segment_client(self, profile: ClientProfile) -> ClientSegment:
        """
        Analyze client profile and determine segment with calorie/macro targets.

        Args:
            profile: Parsed client profile

        Returns:
            ClientSegment with calculated values
        """
        self.logger.info(f"Segmenting client: {profile.name}")

        prompt_template = self.prompts.get("segmentation", "")
        if not prompt_template:
            raise ValueError("Segmentation prompt template not found")

        # Format prompt with profile data
        prompt = prompt_template.format(
            name=profile.name,
            age=profile.age,
            gender=profile.gender,
            weight=profile.weight,
            height=profile.height,
            goal=profile.goal,
            activity_level=profile.activity_level,
            experience_level=profile.experience_level,
            dietary_restrictions=", ".join(profile.dietary_restrictions) or "None",
            health_conditions=", ".join(profile.health_conditions) or "None"
        )

        # Generate response
        response_text = self._generate_with_retry(prompt)

        # Parse JSON response
        try:
            # Clean up response - remove markdown code blocks if present
            clean_text = response_text.strip()
            if clean_text.startswith("```"):
                clean_text = clean_text.split("```")[1]
                if clean_text.startswith("json"):
                    clean_text = clean_text[4:]
            clean_text = clean_text.strip()

            data = json.loads(clean_text)
            segment = ClientSegment.from_dict(data)
            self.logger.info(f"Segmentation complete: {segment.segment}, {segment.calorie_target} kcal")
            return segment

        except json.JSONDecodeError as e:
            self.logger.error(f"Failed to parse segmentation response: {e}")
            self.logger.debug(f"Raw response: {response_text}")
            # Return default values
            return self._calculate_default_segment(profile)

    def _calculate_default_segment(self, profile: ClientProfile) -> ClientSegment:
        """Calculate default segment if AI fails"""
        # BMR calculation (Mifflin-St Jeor)
        if profile.gender == "male":
            bmr = 10 * profile.weight + 6.25 * profile.height - 5 * profile.age + 5
        else:
            bmr = 10 * profile.weight + 6.25 * profile.height - 5 * profile.age - 161

        # Activity multiplier
        activity_multipliers = {
            "sedentary": 1.2,
            "light": 1.375,
            "moderate": 1.55,
            "active": 1.725,
            "very_active": 1.9
        }
        multiplier = activity_multipliers.get(profile.activity_level, 1.55)
        tdee = bmr * multiplier

        # Goal adjustment
        goal_lower = profile.goal.lower()
        if any(word in goal_lower for word in ["schudnúť", "schudnut", "zhubnout", "weight loss", "chudnutie"]):
            calorie_target = int(tdee - 500)
            goal_type = "weight_loss"
        elif any(word in goal_lower for word in ["svaly", "muscle", "nabrat", "nabrať", "bulk"]):
            calorie_target = int(tdee + 300)
            goal_type = "muscle_gain"
        else:
            calorie_target = int(tdee)
            goal_type = "maintenance"

        # Macro calculation
        protein = int(profile.weight * 2.0)  # 2g per kg
        fat = int(profile.weight * 1.0)  # 1g per kg
        carbs = int((calorie_target - (protein * 4) - (fat * 9)) / 4)

        return ClientSegment(
            segment=f"{goal_type}_{profile.gender}",
            calorie_target=calorie_target,
            protein_grams=protein,
            carbs_grams=max(carbs, 100),
            fat_grams=fat,
            macro_ratio={"protein": 30, "carbs": 40, "fat": 30},
            training_frequency="3x_per_week",
            reasoning="Calculated using Mifflin-St Jeor formula with standard adjustments."
        )

    def generate_meal_plan(
        self,
        profile: ClientProfile,
        segment: ClientSegment
    ) -> str:
        """
        Generate a personalized meal plan.

        Args:
            profile: Client profile
            segment: Segmentation data with calorie/macro targets

        Returns:
            Meal plan in Markdown format
        """
        self.logger.info(f"Generating meal plan for: {profile.name}")

        prompt_template = self.prompts.get("meal_plan", "")
        if not prompt_template:
            raise ValueError("Meal plan prompt template not found")

        # Format gender for Slovak
        gender_sk = "muž" if profile.gender == "male" else "žena"

        prompt = prompt_template.format(
            name=profile.name,
            age=profile.age,
            gender=gender_sk,
            weight=profile.weight,
            height=profile.height,
            goal=profile.goal,
            calorie_target=segment.calorie_target,
            protein=segment.protein_grams,
            carbs=segment.carbs_grams,
            fat=segment.fat_grams,
            dietary_restrictions=", ".join(profile.dietary_restrictions) or "Žiadne",
            health_conditions=", ".join(profile.health_conditions) or "Žiadne"
        )

        meal_plan = self._generate_with_retry(prompt)
        self.logger.info(f"Meal plan generated: {len(meal_plan)} characters")
        return meal_plan

    def generate_training_plan(
        self,
        profile: ClientProfile,
        segment: ClientSegment
    ) -> str:
        """
        Generate a personalized training plan.

        Args:
            profile: Client profile
            segment: Segmentation data

        Returns:
            Training plan in Markdown format
        """
        self.logger.info(f"Generating training plan for: {profile.name}")

        prompt_template = self.prompts.get("training_plan", "")
        if not prompt_template:
            raise ValueError("Training plan prompt template not found")

        # Map experience level to Slovak
        experience_map = {
            "beginner": "začiatočník",
            "intermediate": "mierne pokročilý",
            "advanced": "pokročilý"
        }
        experience_sk = experience_map.get(profile.experience_level, "začiatočník")

        # Map training frequency
        frequency_map = {
            "2x_per_week": "2x týždenne",
            "3x_per_week": "3x týždenne",
            "4x_per_week": "4x týždenne",
            "5x_per_week": "5x týždenne",
            "6x_per_week": "6x týždenne"
        }
        frequency_sk = frequency_map.get(segment.training_frequency, "3x týždenne")

        prompt = prompt_template.format(
            name=profile.name,
            experience_level=experience_sk,
            goal=profile.goal,
            training_frequency=frequency_sk,
            health_conditions=", ".join(profile.health_conditions) or "Žiadne",
            available_equipment=", ".join(profile.available_equipment) or "Štandardné fitness centrum"
        )

        training_plan = self._generate_with_retry(prompt)
        self.logger.info(f"Training plan generated: {len(training_plan)} characters")
        return training_plan

    def generate_all_plans(
        self,
        profile: ClientProfile
    ) -> Dict[str, Any]:
        """
        Generate all plans for a client.

        Args:
            profile: Client profile

        Returns:
            Dictionary with segment, meal_plan, and training_plan
        """
        self.logger.info(f"Generating all plans for: {profile.name}")

        # Step 1: Segment client
        segment = self.segment_client(profile)

        # Step 2: Generate meal plan
        meal_plan = self.generate_meal_plan(profile, segment)

        # Step 3: Generate training plan
        training_plan = self.generate_training_plan(profile, segment)

        return {
            "segment": segment,
            "meal_plan": meal_plan,
            "training_plan": training_plan
        }

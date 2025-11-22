#!/usr/bin/env python3
"""
FIT CRM - Main Pipeline
Orchestrates the complete flow from email to delivered fitness plans.
"""
import json
import logging
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, Any

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from config import (
    GEMINI_API_KEY,
    EMAIL_USER,
    EMAIL_PASS,
    SMTP_HOST,
    SMTP_PORT,
    TRAINER_NAME,
    OUTPUT_DIR,
    LOGS_DIR,
)
from src.email_parser import EmailParser, ClientProfile
from src.ai_generator import FitAIGenerator
from src.pdf_generator import PDFGenerator
from src.email_sender import EmailSender


# Configure logging
def setup_logging():
    """Configure logging for the application"""
    log_file = LOGS_DIR / f"app_{datetime.now().strftime('%Y%m%d')}.log"

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=[
            logging.FileHandler(log_file, encoding="utf-8"),
            logging.StreamHandler(sys.stdout)
        ]
    )

    return logging.getLogger(__name__)


class FitCRMPipeline:
    """Main pipeline for processing client intake and generating plans"""

    def __init__(self):
        """Initialize all components"""
        self.logger = logging.getLogger(self.__class__.__name__)
        self.logger.info("Initializing FIT CRM Pipeline...")

        # Initialize components
        self.parser = EmailParser()

        if GEMINI_API_KEY:
            self.ai_generator = FitAIGenerator(api_key=GEMINI_API_KEY)
        else:
            self.logger.warning("GEMINI_API_KEY not set - AI generation will be disabled")
            self.ai_generator = None

        self.pdf_generator = PDFGenerator()

        if EMAIL_USER and EMAIL_PASS:
            self.email_sender = EmailSender(
                smtp_host=SMTP_HOST,
                smtp_port=SMTP_PORT,
                username=EMAIL_USER,
                password=EMAIL_PASS
            )
        else:
            self.logger.warning("Email credentials not set - email sending will be disabled")
            self.email_sender = None

        # Metrics
        self.metrics = []

    def process_intake_email(
        self,
        email_content: str,
        send_email: bool = True
    ) -> Dict[str, Any]:
        """
        Process a client intake email through the complete pipeline.

        Args:
            email_content: Raw email text
            send_email: Whether to send the welcome email

        Returns:
            Dictionary with processing results
        """
        start_time = time.time()
        result = {
            "success": False,
            "client_name": None,
            "client_email": None,
            "meal_plan_pdf": None,
            "training_plan_pdf": None,
            "email_sent": False,
            "processing_time": 0,
            "error": None
        }

        try:
            # Step 1: Parse email
            self.logger.info("=" * 50)
            self.logger.info("STEP 1: Parsing intake email...")
            profile = self.parser.parse_email(email_content)
            result["client_name"] = profile.name
            result["client_email"] = profile.email
            self.logger.info(f"Parsed client: {profile.name} ({profile.email})")

            # Step 2: Generate plans with AI
            if self.ai_generator:
                self.logger.info("=" * 50)
                self.logger.info("STEP 2: Generating fitness plans with AI...")

                # Segment client
                segment = self.ai_generator.segment_client(profile)
                self.logger.info(f"Segment: {segment.segment}")
                self.logger.info(f"Calories: {segment.calorie_target} kcal")
                self.logger.info(f"Macros: P{segment.protein_grams}g / C{segment.carbs_grams}g / F{segment.fat_grams}g")

                # Generate meal plan
                self.logger.info("Generating meal plan...")
                meal_plan = self.ai_generator.generate_meal_plan(profile, segment)
                self.logger.info(f"Meal plan generated: {len(meal_plan)} characters")

                # Generate training plan
                self.logger.info("Generating training plan...")
                training_plan = self.ai_generator.generate_training_plan(profile, segment)
                self.logger.info(f"Training plan generated: {len(training_plan)} characters")
            else:
                self.logger.error("AI generator not available - cannot generate plans")
                result["error"] = "AI generator not configured"
                return result

            # Step 3: Generate PDFs
            self.logger.info("=" * 50)
            self.logger.info("STEP 3: Generating PDF documents...")

            meal_pdf = self.pdf_generator.generate_meal_plan_pdf(
                meal_plan, profile.name, OUTPUT_DIR
            )
            training_pdf = self.pdf_generator.generate_training_plan_pdf(
                training_plan, profile.name, OUTPUT_DIR
            )

            if meal_pdf:
                result["meal_plan_pdf"] = str(meal_pdf)
                self.logger.info(f"Meal plan PDF: {meal_pdf}")
            if training_pdf:
                result["training_plan_pdf"] = str(training_pdf)
                self.logger.info(f"Training plan PDF: {training_pdf}")

            # Step 4: Send email
            if send_email and self.email_sender and meal_pdf and training_pdf:
                self.logger.info("=" * 50)
                self.logger.info("STEP 4: Sending welcome email...")

                email_sent = self.email_sender.send_welcome_email(
                    to_email=profile.email,
                    client_name=profile.name,
                    meal_plan_pdf=meal_pdf,
                    training_plan_pdf=training_pdf,
                    trainer_name=TRAINER_NAME
                )
                result["email_sent"] = email_sent

                if email_sent:
                    self.logger.info(f"Email sent to: {profile.email}")
                else:
                    self.logger.warning("Failed to send email")
            elif not send_email:
                self.logger.info("Email sending skipped (send_email=False)")
            else:
                self.logger.warning("Email sender not configured or PDFs missing")

            # Success
            result["success"] = True

        except Exception as e:
            self.logger.error(f"Pipeline error: {e}", exc_info=True)
            result["error"] = str(e)

        # Calculate processing time
        result["processing_time"] = round(time.time() - start_time, 2)
        self.logger.info("=" * 50)
        self.logger.info(f"Processing completed in {result['processing_time']} seconds")

        # Log metrics
        self._log_metrics(result)

        return result

    def process_file(self, file_path: str, send_email: bool = True) -> Dict[str, Any]:
        """
        Process an intake email from a file.

        Args:
            file_path: Path to the email file
            send_email: Whether to send the welcome email

        Returns:
            Dictionary with processing results
        """
        path = Path(file_path)
        if not path.exists():
            return {"success": False, "error": f"File not found: {file_path}"}

        email_content = path.read_text(encoding="utf-8")
        return self.process_intake_email(email_content, send_email)

    def _log_metrics(self, result: Dict[str, Any]):
        """Log processing metrics to file"""
        metrics = {
            "timestamp": datetime.now().isoformat(),
            "client_name": result.get("client_name"),
            "client_email": result.get("client_email"),
            "success": result.get("success"),
            "email_sent": result.get("email_sent"),
            "processing_time_seconds": result.get("processing_time"),
            "error": result.get("error")
        }

        self.metrics.append(metrics)

        # Append to metrics file
        metrics_file = LOGS_DIR / "metrics.jsonl"
        try:
            with open(metrics_file, "a", encoding="utf-8") as f:
                f.write(json.dumps(metrics, ensure_ascii=False) + "\n")
        except Exception as e:
            self.logger.error(f"Failed to log metrics: {e}")


def main():
    """Main entry point"""
    logger = setup_logging()
    logger.info("=" * 60)
    logger.info("FIT CRM - Fitness Client Relationship Management")
    logger.info("=" * 60)

    # Initialize pipeline
    pipeline = FitCRMPipeline()

    # Check for command line arguments
    if len(sys.argv) > 1:
        # Process specified file
        file_path = sys.argv[1]
        send_email = "--no-email" not in sys.argv
        logger.info(f"Processing file: {file_path}")
        result = pipeline.process_file(file_path, send_email)
    else:
        # Demo mode - process sample email
        sample_dir = Path(__file__).parent.parent / "tests" / "sample_emails"
        sample_files = list(sample_dir.glob("*.txt"))

        if sample_files:
            sample_file = sample_files[0]
            logger.info(f"Demo mode - processing: {sample_file}")
            result = pipeline.process_file(str(sample_file), send_email=False)
        else:
            logger.error("No sample emails found in tests/sample_emails/")
            logger.info("Create a sample email file and try again.")
            logger.info("Usage: python src/main.py [email_file.txt] [--no-email]")
            return

    # Print results
    print("\n" + "=" * 60)
    print("PROCESSING RESULTS")
    print("=" * 60)
    print(f"Success: {result['success']}")
    print(f"Client: {result['client_name']}")
    print(f"Email: {result['client_email']}")
    print(f"Meal Plan PDF: {result['meal_plan_pdf']}")
    print(f"Training Plan PDF: {result['training_plan_pdf']}")
    print(f"Email Sent: {result['email_sent']}")
    print(f"Processing Time: {result['processing_time']} seconds")
    if result['error']:
        print(f"Error: {result['error']}")
    print("=" * 60)


if __name__ == "__main__":
    main()

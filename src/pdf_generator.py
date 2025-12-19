"""PDF Generator - Convert Markdown plans to professional PDFs"""
import logging
import re
from pathlib import Path
from datetime import datetime
from typing import Optional

import markdown

try:
    from weasyprint import HTML, CSS
    WEASYPRINT_AVAILABLE = True
except (ImportError, OSError):
    WEASYPRINT_AVAILABLE = False
    HTML = None
    CSS = None

logger = logging.getLogger(__name__)


class PDFGenerator:
    """Generate professional PDFs from Markdown content"""

    def __init__(self, styles_path: Optional[Path] = None):
        """
        Initialize PDF generator.

        Args:
            styles_path: Path to custom CSS file (optional)
        """
        self.logger = logging.getLogger(self.__class__.__name__)

        # Default styles path
        if styles_path is None:
            styles_path = Path(__file__).parent.parent / "templates" / "styles.css"

        self.styles_path = styles_path
        self.css = self._load_css()

    def _load_css(self) -> str:
        """Load CSS styles"""
        if self.styles_path.exists():
            return self.styles_path.read_text(encoding="utf-8")
        else:
            self.logger.warning(f"Styles file not found: {self.styles_path}")
            return self._get_default_css()

    def _get_default_css(self) -> str:
        """Return default CSS styles"""
        return """
        @page {
            size: A4;
            margin: 2cm;
        }

        body {
            font-family: 'DejaVu Sans', Arial, sans-serif;
            font-size: 11pt;
            line-height: 1.5;
            color: #333;
        }

        h1 {
            color: #2c3e50;
            border-bottom: 3px solid #3498db;
            padding-bottom: 10px;
            font-size: 24pt;
        }

        h2 {
            color: #34495e;
            margin-top: 25px;
            font-size: 18pt;
        }

        h3 {
            color: #2980b9;
            margin-top: 15px;
            font-size: 14pt;
        }

        ul, ol {
            margin-left: 20px;
        }

        li {
            margin-bottom: 5px;
        }

        hr {
            border: none;
            border-top: 1px solid #bdc3c7;
            margin: 20px 0;
        }

        strong {
            color: #2c3e50;
        }

        .header {
            text-align: center;
            margin-bottom: 30px;
        }

        .footer {
            text-align: center;
            font-size: 9pt;
            color: #7f8c8d;
            margin-top: 40px;
        }
        """

    def _sanitize_markdown(self, md_content: str) -> str:
        """
        Sanitize Markdown content for HTML conversion.

        Args:
            md_content: Raw Markdown content

        Returns:
            Sanitized Markdown
        """
        # Remove code block markers if wrapping the entire content
        content = md_content.strip()
        if content.startswith("```markdown"):
            content = content[11:]
        if content.startswith("```"):
            content = content[3:]
        if content.endswith("```"):
            content = content[:-3]

        # Remove any remaining code block markers
        content = re.sub(r"```\w*\n?", "", content)

        return content.strip()

    def _markdown_to_html(self, md_content: str, title: str = "") -> str:
        """
        Convert Markdown to HTML.

        Args:
            md_content: Markdown content
            title: Document title

        Returns:
            HTML string
        """
        # Sanitize content
        clean_md = self._sanitize_markdown(md_content)

        # Convert to HTML
        html_content = markdown.markdown(
            clean_md,
            extensions=["tables", "fenced_code", "nl2br"]
        )

        # Wrap in full HTML document
        html = f"""
        <!DOCTYPE html>
        <html lang="sk">
        <head>
            <meta charset="UTF-8">
            <title>{title}</title>
            <style>
            {self.css}
            </style>
        </head>
        <body>
            <div class="header">
                <h1>{title}</h1>
                <p>Vytvorene: {datetime.now().strftime('%d.%m.%Y')}</p>
            </div>

            {html_content}

            <div class="footer">
                <hr>
                <p>Tento plan bol vytvoreny s pomocou FIT CRM systemu.</p>
                <p>Pre otazky kontaktujte svojho trenera.</p>
            </div>
        </body>
        </html>
        """

        return html

    def generate_pdf(
        self,
        markdown_content: str,
        output_path: str,
        title: str = "Fitness Plan"
    ) -> bool:
        """
        Generate PDF from Markdown content.

        Args:
            markdown_content: Markdown content to convert
            output_path: Path where PDF will be saved
            title: Document title

        Returns:
            True if successful, False otherwise
        """
        try:
            self.logger.info(f"Generating PDF: {output_path}")

            # Convert Markdown to HTML
            html_content = self._markdown_to_html(markdown_content, title)

            # Ensure output directory exists
            output_file = Path(output_path)
            output_file.parent.mkdir(parents=True, exist_ok=True)

            # Generate PDF
            html = HTML(string=html_content)
            html.write_pdf(str(output_file))

            self.logger.info(f"PDF generated successfully: {output_path}")
            return True

        except Exception as e:
            self.logger.error(f"Failed to generate PDF: {e}")
            return False

    def generate_meal_plan_pdf(
        self,
        meal_plan: str,
        client_name: str,
        output_dir: Path
    ) -> Optional[Path]:
        """
        Generate meal plan PDF.

        Args:
            meal_plan: Meal plan in Markdown
            client_name: Client name for filename
            output_dir: Output directory

        Returns:
            Path to generated PDF or None if failed
        """
        # Create safe filename
        safe_name = re.sub(r"[^\w\s-]", "", client_name).strip().replace(" ", "_")
        timestamp = datetime.now().strftime("%Y%m%d")
        filename = f"jedalnicky_{safe_name}_{timestamp}.pdf"
        output_path = output_dir / filename

        success = self.generate_pdf(
            meal_plan,
            str(output_path),
            f"Jedalnicky - {client_name}"
        )

        return output_path if success else None

    def generate_training_plan_pdf(
        self,
        training_plan: str,
        client_name: str,
        output_dir: Path
    ) -> Optional[Path]:
        """
        Generate training plan PDF.

        Args:
            training_plan: Training plan in Markdown
            client_name: Client name for filename
            output_dir: Output directory

        Returns:
            Path to generated PDF or None if failed
        """
        # Create safe filename
        safe_name = re.sub(r"[^\w\s-]", "", client_name).strip().replace(" ", "_")
        timestamp = datetime.now().strftime("%Y%m%d")
        filename = f"treningovy_plan_{safe_name}_{timestamp}.pdf"
        output_path = output_dir / filename

        success = self.generate_pdf(
            training_plan,
            str(output_path),
            f"Treningovy Plan - {client_name}"
        )

        return output_path if success else None

"""Email Sender - Send automated emails with attachments"""
import logging
import smtplib
import ssl
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.application import MIMEApplication
from pathlib import Path
from typing import List, Optional
from datetime import datetime

logger = logging.getLogger(__name__)


class EmailSender:
    """Send emails with attachments via SMTP"""

    def __init__(
        self,
        smtp_host: str,
        smtp_port: int,
        username: str,
        password: str,
        use_tls: bool = True
    ):
        """
        Initialize email sender.

        Args:
            smtp_host: SMTP server hostname
            smtp_port: SMTP server port
            username: Email account username
            password: Email account password (app password for Gmail)
            use_tls: Whether to use TLS encryption
        """
        self.smtp_host = smtp_host
        self.smtp_port = smtp_port
        self.username = username
        self.password = password
        self.use_tls = use_tls
        self.logger = logging.getLogger(self.__class__.__name__)

        # Load email template
        self.templates_dir = Path(__file__).parent.parent / "templates"

    def _load_template(self, template_name: str) -> str:
        """Load an email template"""
        template_path = self.templates_dir / template_name
        if template_path.exists():
            return template_path.read_text(encoding="utf-8")
        else:
            self.logger.warning(f"Template not found: {template_path}")
            return ""

    def _create_message(
        self,
        to_email: str,
        subject: str,
        html_body: str,
        attachments: Optional[List[Path]] = None
    ) -> MIMEMultipart:
        """
        Create email message with attachments.

        Args:
            to_email: Recipient email address
            subject: Email subject
            html_body: HTML email body
            attachments: List of file paths to attach

        Returns:
            MIMEMultipart message
        """
        msg = MIMEMultipart()
        msg["From"] = self.username
        msg["To"] = to_email
        msg["Subject"] = subject

        # Add HTML body
        msg.attach(MIMEText(html_body, "html", "utf-8"))

        # Add attachments
        if attachments:
            for file_path in attachments:
                if file_path and file_path.exists():
                    try:
                        with open(file_path, "rb") as f:
                            attachment = MIMEApplication(f.read(), Name=file_path.name)
                            attachment["Content-Disposition"] = f'attachment; filename="{file_path.name}"'
                            msg.attach(attachment)
                            self.logger.info(f"Attached: {file_path.name}")
                    except Exception as e:
                        self.logger.error(f"Failed to attach {file_path}: {e}")

        return msg

    def send_email(
        self,
        to_email: str,
        subject: str,
        html_body: str,
        attachments: Optional[List[Path]] = None
    ) -> bool:
        """
        Send an email.

        Args:
            to_email: Recipient email address
            subject: Email subject
            html_body: HTML email body
            attachments: List of file paths to attach

        Returns:
            True if sent successfully, False otherwise
        """
        try:
            self.logger.info(f"Sending email to: {to_email}")

            # Create message
            msg = self._create_message(to_email, subject, html_body, attachments)

            # Create secure connection
            context = ssl.create_default_context()

            if self.use_tls:
                # STARTTLS
                with smtplib.SMTP(self.smtp_host, self.smtp_port) as server:
                    server.ehlo()
                    server.starttls(context=context)
                    server.ehlo()
                    server.login(self.username, self.password)
                    server.send_message(msg)
            else:
                # SSL
                with smtplib.SMTP_SSL(self.smtp_host, self.smtp_port, context=context) as server:
                    server.login(self.username, self.password)
                    server.send_message(msg)

            self.logger.info(f"Email sent successfully to: {to_email}")
            return True

        except smtplib.SMTPAuthenticationError as e:
            self.logger.error(f"SMTP authentication failed: {e}")
            self.logger.error("Tip: For Gmail, use an App Password instead of your regular password")
            return False
        except smtplib.SMTPException as e:
            self.logger.error(f"SMTP error: {e}")
            return False
        except Exception as e:
            self.logger.error(f"Failed to send email: {e}")
            return False

    def send_welcome_email(
        self,
        to_email: str,
        client_name: str,
        meal_plan_pdf: Optional[Path] = None,
        training_plan_pdf: Optional[Path] = None,
        trainer_name: str = "Tvoj Trener"
    ) -> bool:
        """
        Send welcome email with fitness plans.

        Args:
            to_email: Client email address
            client_name: Client name
            meal_plan_pdf: Path to meal plan PDF
            training_plan_pdf: Path to training plan PDF
            trainer_name: Trainer name for signature

        Returns:
            True if sent successfully, False otherwise
        """
        # Load template
        template = self._load_template("welcome_email.html")

        if not template:
            # Use default template
            template = self._get_default_welcome_template()

        # Format template
        html_body = template.format(
            client_name=client_name,
            trainer_name=trainer_name,
            date=datetime.now().strftime("%d.%m.%Y")
        )

        # Prepare attachments
        attachments = []
        if meal_plan_pdf:
            attachments.append(Path(meal_plan_pdf))
        if training_plan_pdf:
            attachments.append(Path(training_plan_pdf))

        # Send email
        subject = f"Tvoj Osobny Fitness Plan - {client_name}"

        return self.send_email(to_email, subject, html_body, attachments)

    def _get_default_welcome_template(self) -> str:
        """Return default welcome email template"""
        return """
        <!DOCTYPE html>
        <html lang="sk">
        <head>
            <meta charset="UTF-8">
            <style>
                body {
                    font-family: 'Segoe UI', Arial, sans-serif;
                    line-height: 1.6;
                    color: #333;
                    max-width: 600px;
                    margin: 0 auto;
                    padding: 20px;
                }
                .header {
                    background: linear-gradient(135deg, #3498db 0%, #2980b9 100%);
                    color: white;
                    padding: 30px;
                    text-align: center;
                    border-radius: 10px 10px 0 0;
                }
                .content {
                    background: #f9f9f9;
                    padding: 30px;
                    border-radius: 0 0 10px 10px;
                }
                h1 {
                    margin: 0;
                    font-size: 28px;
                }
                .highlight {
                    background: #e8f4fd;
                    border-left: 4px solid #3498db;
                    padding: 15px;
                    margin: 20px 0;
                }
                .footer {
                    text-align: center;
                    color: #888;
                    font-size: 12px;
                    margin-top: 30px;
                }
                ul {
                    padding-left: 20px;
                }
                li {
                    margin-bottom: 10px;
                }
            </style>
        </head>
        <body>
            <div class="header">
                <h1>Vitaj, {client_name}!</h1>
                <p>Tvoja cesta k lepsej forme zacina teraz</p>
            </div>

            <div class="content">
                <p>Ahoj <strong>{client_name}</strong>,</p>

                <p>Dakujem ti za doveru! Pripravil som pre teba osobny fitness plan,
                ktory ti pomoze dosiahnut tvoje ciele.</p>

                <div class="highlight">
                    <strong>V prilohe najdes:</strong>
                    <ul>
                        <li><strong>Jedalnicky</strong> - 7-dnovy plan stravovania s presnym rozpisom jedal a nakupnym zoznamom</li>
                        <li><strong>Treningovy plan</strong> - Detailny program treningov s popisom cvikov a technikou</li>
                    </ul>
                </div>

                <h3>Ako zacat?</h3>
                <ol>
                    <li>Prezri si oba dokumenty a oboznam sa s planom</li>
                    <li>Priprav si nakup podla nakupneho zoznamu</li>
                    <li>Zaciatok je vzdy v pondelok - nastav si pripomienku!</li>
                    <li>Ak mas otazky, kludne mi napis</li>
                </ol>

                <h3>Dolezite tipy:</h3>
                <ul>
                    <li>Dodrzuj pitny rezim - minimalne 2-3 litre vody denne</li>
                    <li>Spánok je klucovy - cielom je 7-9 hodin denne</li>
                    <li>Konzistentnost je dovlezitejsia ako perfekcionizmus</li>
                    <li>Sleduj svoj pokrok - vaz sa raz tyzdenne</li>
                </ul>

                <p>Ak budes mat akekolvek otazky alebo budes potrebovat upravit plan,
                nevaraj sa ma kontaktovat.</p>

                <p>Drzim palce a teším sa na tvoje vysledky!</p>

                <p>S pozdravom,<br>
                <strong>{trainer_name}</strong></p>
            </div>

            <div class="footer">
                <p>Tento email bol automaticky vygenerovany systemom FIT CRM.</p>
                <p>Datum: {date}</p>
            </div>
        </body>
        </html>
        """

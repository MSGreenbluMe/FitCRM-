# FIT CRM - Fitness Client Relationship Management

Automatizovany system pre fitness trenerov na spracovanie klientov a generovanie personalizovanych planov.

## Funkcionalita

- **Email Parser**: Parsuje prijimacie emaily od klientov do strukturovanych profilov
- **AI Generator**: Generuje personalizovane jedalnicky a treningove plany pomocou Google Gemini
- **PDF Generator**: Konvertuje plany do profesionalnych PDF dokumentov
- **Email Sender**: Automaticky odosiela uvitacie emaily s prilohami klientom

## Rychly start

### 1. Instalacia

```bash
# Klonuj repozitar
git clone <repository-url>
cd FitCRM

# Vytvor virtualne prostredie
python -m venv venv

# Aktivuj venv
# Linux/Mac:
source venv/bin/activate
# Windows:
venv\Scripts\activate

# Instaluj zavislosti
pip install -r requirements.txt
```

### 2. Konfiguracia

```bash
# Skopiruj priklad konfiguracneho suboru
cp .env.example .env

# Uprav .env subor s tvojimi udajmi
nano .env
```

Potrebne premenne:
- `GEMINI_API_KEY` - API kluc z Google AI Studio
- `EMAIL_USER` - Email ucet pre odosielanie
- `EMAIL_PASS` - Heslo alebo App Password (pre Gmail)
- `SMTP_HOST` - SMTP server (napr. smtp.gmail.com)
- `SMTP_PORT` - SMTP port (zvycajne 587)

### 3. Spustenie

```bash
# Demo mod (bez odosielania emailu)
python src/main.py

# Spracuj konkretny email
python src/main.py tests/sample_emails/client1_weight_loss.txt

# Spracuj a odosli email
python src/main.py tests/sample_emails/client1_weight_loss.txt

# Spracuj bez odoslania emailu
python src/main.py tests/sample_emails/client1_weight_loss.txt --no-email
```

## Struktura projektu

```
FitCRM/
├── src/
│   ├── __init__.py
│   ├── email_parser.py      # Parsovanie emailov
│   ├── ai_generator.py      # Generovanie planov s AI
│   ├── pdf_generator.py     # Generovanie PDF
│   ├── email_sender.py      # Odosielanie emailov
│   └── main.py              # Hlavny pipeline
├── prompts/
│   ├── segmentation.txt     # Prompt pre segmentaciu klientov
│   ├── meal_plan.txt        # Prompt pre jedalnicky
│   └── training_plan.txt    # Prompt pre treningove plany
├── templates/
│   ├── styles.css           # CSS styly pre PDF
│   └── welcome_email.html   # HTML sablona emailu
├── tests/
│   └── sample_emails/       # Vzorove emaily na testovanie
├── output/                  # Vygenerovane PDF subory
├── logs/                    # Logy a metriky
├── config.py                # Konfiguracia
├── requirements.txt         # Python zavislosti
├── .env.example             # Priklad .env suboru
└── README.md
```

## Pouzitie v kode

```python
from src.main import FitCRMPipeline

# Inicializuj pipeline
pipeline = FitCRMPipeline()

# Spracuj email
email_content = open("client_email.txt").read()
result = pipeline.process_intake_email(email_content, send_email=True)

# Vysledok
print(f"Klient: {result['client_name']}")
print(f"Jedalnicky PDF: {result['meal_plan_pdf']}")
print(f"Treningovy plan PDF: {result['training_plan_pdf']}")
print(f"Email odoslany: {result['email_sent']}")
```

## Format prijimaciaho emailu

System ocakava emaily v tomto formate:

```
Novy klient z weboveho formulara:

Meno: Jan Novak
Email: jan.novak@example.com
Vek: 30
Pohlavie: muz
Vaha: 85 kg
Vyska: 180 cm
Ciel: Chcem schudnut a zlepsit kondíciu
Aktivita: sedave zamestnanie
Skusenosti: zaciatocnik
Obmedzenia: ziadne
Motivacia: Chcem sa citit lepsie
```

## Ziskanie API klucov

### Google Gemini API
1. Chod na: https://makersuite.google.com/app/apikey
2. Vytvor novy API kluc
3. Pridaj do `.env`: `GEMINI_API_KEY=tvoj_kluc`

### Gmail App Password
1. Zapni 2FA na Google ucte
2. Chod na: https://myaccount.google.com/apppasswords
3. Vygeneruj App Password
4. Pridaj do `.env`: `EMAIL_PASS=16_znakove_heslo`

## Troubleshooting

### Gemini API error 429 (Rate limit)
System ma vstavaný retry mechanizmus s exponencialnym backoff.

### WeasyPrint error
Instaluj systemove zavislosti:
```bash
# Ubuntu/Debian
sudo apt-get install python3-dev libcairo2 libpango-1.0-0 libpangocairo-1.0-0 libgdk-pixbuf2.0-0

# Mac
brew install cairo pango gdk-pixbuf
```

### Email sa neodosle (SMTPAuthenticationError)
- Pouzi App Password namiesto bezneho hesla (Gmail)
- Over spravnost SMTP hostu a portu

## Licencia

MIT License

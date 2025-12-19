# FitCRM – súhrnný technický popis (bez UI)

## 1) Účel projektu

**FitCRM** je prototyp CRM nástroja pre fitness trénera, ktorý automatizuje onboarding klientov z e‑mailu a pomáha rýchlo vytvoriť personalizovaný **jedálniček** a **tréningový plán**.

Projekt má dve hlavné „cesty“:

- **Pipeline (automatizácia)**: spracuje intake e‑mail → vytvorí štruktúrovaný profil → vygeneruje plány cez AI → vyrobí PDF → (voliteľne) pošle klientovi e‑mail s prílohami.
- **Streamlit web app (operátorské UI)**: demonštračné rozhranie pre trénera (Dashboard, Inbox, Klienti) + Email Connector (IMAP) + demo plánovač.

Poznámka: UI vrstva je v `app.py` a je primárne demo/koncept. Biznis logika je v `src/`.

---

## 2) Architektúra a kľúčové moduly

### 2.1 Prehľad modulov

- **`app.py`**
  - Streamlit aplikácia (Dashboard/Inbox/Klienti) + demo dáta.
  - Používa moduly zo `src/`.
  - Obsahuje aj „demo“ implementácie inboxu, výživovej analýzy, klient list/detail atď.

- **`src/email_parser.py`**
  - Parsuje intake e‑maily do štruktúry `ClientProfile`.

- **`src/ai_generator.py`**
  - Integrácia s **Google Gemini**.
  - Segmentácia klienta (`ClientSegment`) + generovanie jedálnička + tréningového plánu.
  - Obsahuje rate limit, retry/backoff a jednoduchý prompt cache.

- **`src/pdf_generator.py`**
  - Konverzia Markdown → HTML → PDF.
  - V tomto repozitári je použitý WeasyPrint (s poznámkami nižšie o Windows).

- **`src/email_sender.py`**
  - SMTP odosielanie e‑mailov s PDF prílohami.

- **`src/email_connector.py`**
  - IMAP konektor pre načítanie e‑mailov do Inboxu (Streamlit).

- **`src/main.py`**
  - „Headless“ pipeline (CLI) – orchestrácia: parse → AI → PDF → send.

- **`prompts/*.txt`**
  - Prompt šablóny:
    - `segmentation.txt`
    - `meal_plan.txt`
    - `training_plan.txt`

---

## 3) Tok dát (end‑to‑end)

### 3.1 Pipeline tok (automatizované spracovanie intake e‑mailu)

Autoritatívna pipeline je v `src/main.py` (class `FitCRMPipeline`).

1. **Input**: text intake e‑mailu (string)
2. **Parse**: `EmailParser.parse_email()` → `ClientProfile`
3. **AI**:
   - `FitAIGenerator.segment_client(profile)` → `ClientSegment` (kcal + makrá + frekvencia)
   - `FitAIGenerator.generate_meal_plan(profile, segment)` → Markdown
   - `FitAIGenerator.generate_training_plan(profile, segment)` → Markdown
4. **PDF**:
   - `PDFGenerator.generate_meal_plan_pdf()` → PDF súbor do `output/`
   - `PDFGenerator.generate_training_plan_pdf()` → PDF súbor do `output/`
5. **Email** (voliteľné): `EmailSender.send_welcome_email()` → SMTP e‑mail s PDF prílohami
6. **Metriky**: pipeline loguje metriky do `logs/metrics.jsonl`.

### 3.2 Streamlit tok (Inbox / Email Connector)

Streamlit má aj samostatnú IMAP cestu:

1. Užívateľ zadá IMAP údaje (host/port/user/pass, SSL/STARTTLS) v UI.
2. `test_imap_connection()` overí prístup.
3. `fetch_imap_messages()` načíta posledné správy z mailboxu a extrahuje:
   - `subject`, `from`, `date`, `body`
4. Správy sa zobrazia v Inboxe (UI vrstva) a môžu byť použité ako „zdroj“ pre vytvorenie klienta / plánov (v UI).

---

## 4) Parsovanie intake e‑mailov (`src/email_parser.py`)

### 4.1 Dátový model

`ClientProfile` je dataclass so „required“ a „optional“ poľami:

- **Required**: `name`, `email`, `age`, `gender`, `weight`, `height`, `goal`
- **Optional** (výber): `activity_level`, `experience_level`, `dietary_restrictions`, `health_conditions`, `motivation`, `training_days_per_week` …

### 4.2 Mechanika parsovania

`EmailParser` používa regex patterny pre Slovak/Czech varianty názvov polí (napr. `meno/jmeno/name`, `vek/věk/age`, `váha/hmotnost/weight`).

Hlavné kroky v `parse_email()`:

- Normalizácia textu (`strip`, lower pre pomocné mapovania)
- Extrakcia required polí cez `_extract_field/_extract_number/_extract_float`
- Validácia:
  - Ak chýba `name/email/age/weight/height` → `ValueError`
  - `gender` má fallback default `male`
  - `goal` má fallback `general fitness`
- Optional polia:
  - `activity_level` mapované cez `ACTIVITY_MAP`
  - `experience_level` mapované cez `EXPERIENCE_MAP`
  - zoznamy (alergie/obmedzenia) cez `_parse_list()`

### 4.3 Limity parsovania

- Parser je regex‑based, čiže je citlivý na formát (je to zámer pre jednoduchosť demo).
- Ak e‑mail príde vo veľmi voľnej forme, môže padnúť na missing required fields.

Odporúčanie pre „produkciu“:

- Pridať robustnejší parser (LLM‑based extraction alebo form‑based ingestion).
- Pridať viac patternov a „fuzzy“ normalizácie.

---

## 5) AI generovanie plánov (`src/ai_generator.py`)

### 5.1 Model a konfigurácia

- Používa knižnicu `google.generativeai` a `genai.GenerativeModel(model_name)`.
- Model sa berie z env/config:
  - `GEMINI_MODEL` (default v `config.py`: `gemini-2.5-flash-lite`)

### 5.2 Prompt šablóny

Prompt súbory sú v `prompts/` a načítavajú sa pri inicializácii `FitAIGenerator`.

- `segmentation.txt`: očakáva **čisté JSON** (bez markdown) s:
  - `calorie_target`, `protein_grams`, `carbs_grams`, `fat_grams`, `training_frequency`, `reasoning`…
- `meal_plan.txt`: generuje 7‑dňový jedálniček v Markdown formáte + nákupný zoznam.
- `training_plan.txt`: generuje tréningový plán v Markdown formáte.

### 5.3 Rate limiting, retry/backoff, cache

Aensure stabilitu na free tier:

- **Rate limit**:
  - buď explicitne cez `GEMINI_MIN_INTERVAL_SECONDS`, alebo odvodené z `GEMINI_RPM` (default 5 rpm).
- **Retry/backoff**:
  - `GEMINI_MAX_ATTEMPTS` (default 3)
  - pri 429/quota/rate zlyhaní exponenciálny backoff:
    - `GEMINI_BACKOFF_BASE_SECONDS` (default 5)
    - `GEMINI_BACKOFF_CAP_SECONDS` (default 60)
- **Cache**:
  - jednoduchý in‑memory cache mapovaný podľa hash(promptu) – pomáha pri opakovaných renderoch v UI.

### 5.4 Fallback pri zlom výstupe

Pri `segment_client()` sa očakáva valid JSON. Ak AI vráti text, ktorý nejde parse‑nuť:

- systém prejde na `_calculate_default_segment()`:
  - BMR (Mifflin‑St Jeor)
  - TDEE cez activity multipliers
  - úprava podľa cieľa (weight loss / muscle gain / maintenance)
  - makrá vypočítané heuristikou

---

## 6) PDF generovanie (`src/pdf_generator.py`)

### 6.1 Ako to funguje

1. Markdown sa vyčistí (`_sanitize_markdown`) – odstráni wrapping code fences.
2. Markdown sa konvertuje na HTML cez `markdown.markdown(... extensions=[tables, fenced_code, nl2br])`.
3. HTML sa zabalí do jednoduchej HTML šablóny + vloží sa CSS (`templates/styles.css` alebo default).
4. PDF export:
   - WeasyPrint `HTML(string=html_content).write_pdf(path)`

### 6.2 Dôležité: Windows kompatibilita

WeasyPrint často na Windows vyžaduje externé knižnice (GTK/Pango) a môže padať.

V repozitári je import WeasyPrint spravený **voliteľne** (`try/except ImportError, OSError`), ale samotné `generate_pdf()` momentálne predpokladá, že `HTML` je dostupné.

Odporúčanie pre „produkciu“ (Windows):

- Použiť alternatívu (ReportLab, wkhtmltopdf, alebo server‑side PDF službu).
- Alebo generovať iba HTML a PDF riešiť mimo tejto appky.

---

## 7) Odosielanie e‑mailov (`src/email_sender.py`)

- SMTP klient cez `smtplib`.
- Podpora:
  - STARTTLS (`use_tls=True`, default)
  - alebo SMTP_SSL
- E‑mail je HTML (`MIMEText(html, "html")`), prílohy sú `MIMEApplication`.
- Šablóna welcome e‑mailu:
  - `templates/welcome_email.html` alebo fallback default template v kóde.

Poznámka:
- Gmail typicky vyžaduje **App Password** (pri zapnutom 2FA).

---

## 8) IMAP Email Connector (`src/email_connector.py`)

- Minimalistická integrácia iba so stdlib (`imaplib`, `email`).
- `fetch_imap_messages()`:
  - `search("ALL")`, vezme posledné N (`limit`, default 20)
  - `fetch(RFC822)`
  - extrahuje text body preferenčne z `text/plain` častí (ignoruje attachmenty)

Limity:

- Neexistuje zatiaľ:
  - deduplikácia podľa Message‑ID
  - paging na serveri
  - caching / rate limit IMAP
  - threadovanie

---

## 9) Konfigurácia a secrets

### 9.1 `.env` / `config.py`

`config.py` číta `.env` cez `python-dotenv`.

Kľúčové premenné:

- **Gemini**:
  - `GEMINI_API_KEY`
  - `GEMINI_MODEL` (default `gemini-2.5-flash-lite`)
  - voliteľne throttling/backoff:
    - `GEMINI_RPM`, `GEMINI_MIN_INTERVAL_SECONDS`
    - `GEMINI_MAX_ATTEMPTS`, `GEMINI_BACKOFF_BASE_SECONDS`, `GEMINI_BACKOFF_CAP_SECONDS`

- **SMTP**:
  - `EMAIL_USER`, `EMAIL_PASS`
  - `SMTP_HOST`, `SMTP_PORT`

- **Výživa lookup (API Ninjas)**:
  - `NUTRITION_API_KEY`

### 9.2 Streamlit secrets

V `app.py` sú helpery, ktoré najprv skúšajú `st.secrets` a až potom env:

- `get_api_key()` → `st.secrets["gemini"]["api_key"]` alebo `GEMINI_API_KEY`
- `get_nutrition_api_key()` → `st.secrets["nutrition"]["api_key"]` alebo `NUTRITION_API_KEY`

Odporúčanie:

- API kľúče nikdy necommitovať.
- Pre produkciu preferovať `st.secrets` (alebo bezpečný vault).

---

## 10) Limity a praktické poznámky k „free API“

### 10.1 Google Gemini (free tier)

Limity free tier sa menia podľa policy Google a modelu.

V praxi treba rátať s:

- **Rate limits** (requests per minute / day)
- **Quota** pre generovanie (najmä pri dlhších výstupoch ako 7‑dňový jedálniček)
- **429 / RESOURCE_EXHAUSTED** chyby

FitCRM v kóde rieši stabilitu takto:

- rate limiting (default ~5 rpm)
- retry/backoff pri 429/quota
- in‑memory cache promptov

Odporúčanie pre prevádzku:

- Nastaviť `GEMINI_RPM` konzervatívne (napr. 3–5)
- Urobiť generovanie asynchrónne a queue‑ované (v budúcnosti)
- Pri dlhých výstupoch používať „flash“ modely alebo generovať po častiach

### 10.2 API Ninjas – Nutrition

Používa sa endpoint:

- `GET https://api.api-ninjas.com/v1/nutrition?query=...` s headerom `X-Api-Key`.

Free tier limity sa tiež môžu meniť.

V UI je to použité ako doplnková funkcia (lookup nutričných hodnôt), takže:

- je vhodné mať fallback (zobraziť „kľúč nie je nastavený“ / “nenašlo sa”)
- cacheovať výsledky (aktuálne nie je persistent cache)

---

## 11) Čo je demo vs. „produkčné“ správanie

**Demo / prototyp**:

- Streamlit UI drží stav v `st.session_state` (nepersistuje DB).
- Inbox môže pracovať s demo e‑mailami aj s IMAP.
- Generovanie plánov je „best effort“ – závisí od dostupného API kľúča a quota.

Na „produkciu“ by bolo vhodné doplniť:

- DB (klienti, plány, história)
- audit log / metriky
- bezpečné ukladanie credentials
- robustné PDF generovanie kompatibilné s Windows
- job queue pre AI generovanie

---

## 12) Rýchly návod: ako projekt reálne používať

1. Nastav `.env` (alebo `st.secrets`):
   - `GEMINI_API_KEY`
   - SMTP (ak chceš posielať e‑maily)
   - voliteľne `NUTRITION_API_KEY`
2. Spusti UI:
   - `streamlit run app.py`
3. Test pipeline cez CLI:
   - `python src/main.py tests/sample_emails/<file>.txt --no-email`

---

## 13) Najčastejšie problémy

- **429 / quota** na Gemini: pomôže nižšie RPM + retry/backoff (je už v kóde).
- **PDF na Windows**: WeasyPrint môže padať kvôli chýbajúcim systémovým knižniciam.
- **SMTP auth** (Gmail): nutné App Password.
- **IMAP**: niektorí provideri blokujú basic auth – je lepšie OAuth (plán do budúcna).

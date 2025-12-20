# FitCRM Backend Documentation

## Prehľad (Overview)

FitCRM je teraz vybavený robustnou backend logikou pre automatizované spracovanie emailov, správu klientov, generovanie tréningových a nutričných plánov, a sledovanie pokroku.

## 🚀 Nové Funkcie

### 1. **Database Layer** (Databázová vrstva)
- Persistent storage pomocou Netlify Blobs
- CRUD operácie pre všetky entity (clients, plans, progress, emails)
- Indexovanie pre rýchle vyhľadávanie
- Automatické časové značky (timestamps)

### 2. **Email Processing** (Spracovanie emailov)
- IMAP connector pre automatické sťahovanie emailov
- Email parser - rozpoznáva typy emailov (dotazník, progress update, otázka)
- Automatická klasifikácia a prioritizácia
- Spracovanie príloh

### 3. **Client Onboarding** (Onboarding klientov)
- Automatické parsovanie dotazníkov z emailov
- Extrakcia klientských dát (meno, vek, váha, ciele, atď.)
- Vytvorenie klientského profilu
- Welcome email automation

### 4. **Progress Tracking** (Sledovanie pokroku)
- Endpoint pre submission progress updatov
- Automatická analýza trendu (váha, compliance, energia)
- Generovanie personalizovaných odpovedí
- Automatické posielanie feedbacku

### 5. **Automation Engine** (Automatizačný engine)
- Trigger-based workflows
- Action pipeline system
- Template variable resolution
- Automation logging

### 6. **Email Templates** (Emailové šablóny)
- Predpripravené šablóny (welcome, plan ready, check-in reminder)
- Support pre HTML a plain text
- Variable substitution ({{client.name}}, atď.)

## 📁 Štruktúra Backend Kódu

```
netlify/functions/
├── db/
│   ├── schema.js          # Database schemas
│   └── database.js        # Database abstraction layer
├── services/
│   ├── email-processor.js # IMAP + email parsing
│   └── automation-engine.js # Workflow automation
├── check_emails.js        # Endpoint: Check new emails
├── submit_progress.js     # Endpoint: Submit progress
├── clients.js             # Endpoint: CRUD for clients
├── setup.js               # Initialize system with defaults
├── generate_plan.js       # Existing: AI plan generation
├── send_email.js          # Existing: Send emails
└── health.js              # Existing: Health check
```

## 🔧 Setup a Konfigurácia

### Krok 1: Inštalácia Dependencies

```bash
npm install
```

Nové dependencies:
- `imap` - IMAP email fetching
- `mailparser` - Email parsing
- `@netlify/blobs` - Persistent storage

### Krok 2: Environment Variables

Vytvor `.env` súbor s nasledujúcimi premennými:

```bash
# IMAP Configuration (pre príjem emailov)
IMAP_HOST=imap.gmail.com
IMAP_PORT=993
IMAP_USER=your-email@gmail.com
IMAP_PASSWORD=your-app-password

# SMTP Configuration (pre posielanie emailov - už existuje)
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your-email@gmail.com
SMTP_PASS=your-app-password

# Gemini AI (už existuje)
GEMINI_API_KEY=your-gemini-api-key

# Netlify
URL=https://your-site.netlify.app
```

**Gmail Setup:**
1. Zapni 2-Factor Authentication
2. Vygeneruj "App Password" (Nastavenia > Bezpečnosť > 2-Step Verification > App passwords)
3. Použi App Password namiesto tvojho normálneho hesla

### Krok 3: Inicializácia Systému

Po deploymente, zavolaj setup endpoint:

```bash
curl https://your-site.netlify.app/.netlify/functions/setup?sample=true
```

Toto vytvorí:
- ✅ 3 automation rules (onboarding, progress response, plan activation)
- ✅ 3 email templates (welcome, plan ready, check-in reminder)
- ✅ 2 scheduled tasks (email checking, reminders)
- ✅ Sample client data (ak `sample=true`)

## 📡 API Endpoints

### **1. Check Emails**

Skontroluje nové emaily cez IMAP a automaticky ich spracuje.

```
GET/POST /.netlify/functions/check_emails
```

**Response:**
```json
{
  "ok": true,
  "emailsChecked": 5,
  "processed": 5,
  "automationRulesTriggered": 2,
  "results": [
    {
      "emailId": "uuid",
      "category": "questionnaire",
      "clientId": "uuid"
    }
  ]
}
```

**Kategórie emailov:**
- `questionnaire` - Dotazník od nového klienta
- `progress_update` - Progress update od existujúceho klienta
- `question` - Otázka vyžadujúca manuálnu odpoveď

### **2. Submit Progress**

Endpoint pre submission progress updatov (cez web form alebo API).

```
POST /.netlify/functions/submit_progress
```

**Payload:**
```json
{
  "clientId": "uuid",  // alebo "email": "client@example.com"
  "weight": 180,
  "bodyFatPct": 18,
  "energyLevel": 8,
  "sleepQuality": 7,
  "stressLevel": 3,
  "compliance": 85,
  "notes": "Feeling great!",
  "challenges": "A bit hungry in the evenings",
  "wins": "Hit all my workouts this week"
}
```

**Response:**
```json
{
  "ok": true,
  "progressId": "uuid",
  "clientId": "uuid",
  "automated": true,
  "message": "Progress submitted successfully"
}
```

**Ak je zapnutá automatizácia**, systém:
1. Vytvorí progress entry
2. Analyzuje trend (váha, compliance)
3. Vygeneruje personalizovaný feedback
4. Pošle email s odpoveďou klientovi

### **3. Clients API**

CRUD operácie pre klientov.

```
GET    /.netlify/functions/clients         # List všetkých klientov
GET    /.netlify/functions/clients/:id     # Detail klienta
POST   /.netlify/functions/clients         # Vytvoriť klienta
PUT    /.netlify/functions/clients/:id     # Updatnúť klienta
DELETE /.netlify/functions/clients/:id     # Vymazať klienta
```

**GET /clients/:id Response:**
```json
{
  "ok": true,
  "client": { ... },
  "trainingPlans": [ ... ],
  "nutritionPlans": [ ... ],
  "progress": [ ... ],
  "emails": [ ... ]
}
```

### **4. Generate Plan** (už existuje, teraz integrované)

```
POST /.netlify/functions/generate_plan
```

**Payload:**
```json
{
  "client": { ... },
  "goal": "Weight Loss",
  "type": "training_plan",  // alebo "nutrition_plan"
  "constraints": {
    "availableDays": ["mon", "wed", "fri"],
    "equipment": ["dumbbells", "barbell"]
  }
}
```

## 🤖 Automation System

### Ako fungujú Automation Rules

Každá rule má:
- **Trigger** - Udalosť ktorá spustí rule
- **Conditions** - Podmienky ktoré musia byť splnené
- **Actions** - Sekvencia akcií ktoré sa vykonajú

### Prednastavené Rules

#### **1. New Client Onboarding**

**Trigger:** `questionnaire_received` (email kategória = questionnaire)

**Actions:**
1. `activate_client` - Aktivuj klienta
2. `generate_training_plan` - Vygeneruj tréningový plán (draft)
3. `generate_nutrition_plan` - Vygeneruj nutričný plán (draft)
4. `send_template_email` - Pošli welcome email

**Flow:**
```
Email dotazník príde
  → Parser extrahuje dáta
  → Vytvorí sa client profil
  → Trigger: questionnaire_received
  → Rule vykoná actions
  → Klient dostane welcome email
  → Plány sú pripravené na review
```

#### **2. Progress Update Auto-Response**

**Trigger:** `progress_submitted`

**Actions:**
1. `analyze_progress` - Analyzuj trend a data
2. `generate_progress_response` - Vygeneruj personalizovaný feedback
3. `send_email` - Pošli feedback klientovi

**Analýza zahŕňa:**
- Trend váhy (klesá/stúpa/stabilná)
- Priemerná compliance
- Odporúčania na základe energie, spánku, stress levelu

#### **3. Auto-Activate Plans** (disabled by default)

**Trigger:** `plan_approved` (manual trigger)

**Actions:**
1. `activate_plan` - Aktivuj plán
2. `send_template_email` - Pošli email že plán je ready

### Dostupné Actions

| Action | Popis | Parametre |
|--------|-------|-----------|
| `create_client` | Vytvor nového klienta | client data |
| `update_client` | Updatni klienta | clientId, updates |
| `activate_client` | Aktivuj klienta | clientId |
| `generate_training_plan` | Vygeneruj tréningový plán | clientId, goal, constraints |
| `generate_nutrition_plan` | Vygeneruj nutričný plán | clientId, goal, constraints |
| `activate_plan` | Aktivuj plán | planId, planType |
| `send_email` | Pošli email | to, subject, text, html |
| `send_template_email` | Pošli email zo šablóny | templateId, to, data |
| `analyze_progress` | Analyzuj progress entry | progressId |
| `generate_progress_response` | Vygeneruj feedback | progressId |
| `log` | Log do konzoly | message |
| `wait` | Počkaj (delay) | ms alebo seconds |
| `webhook` | Zavolaj external API | url, method, data |

### Template Variables

V actions môžeš používať template variables:

```javascript
{
  "type": "send_email",
  "params": {
    "to": "{{client.email}}",
    "subject": "Hello {{client.name}}!",
    "text": "Your goal is: {{client.goal}}"
  }
}
```

**Dostupné v context:**
- `client.*` - Klient data
- `progressEntry.*` - Progress entry data
- `trainingPlan.*` - Tréningový plán
- `nutritionPlan.*` - Nutričný plán
- `progressAnalysis.*` - Výsledok analýzy
- `progressResponse` - Vygenerovaný feedback

## 📧 Email Templates

### Vytváranie Custom Šablón

```javascript
await db.createEmailTemplate({
  id: 'my_template',
  name: 'My Custom Template',
  subject: 'Hello {{client.name}}',
  textContent: `
    Hi {{client.name}},

    Your goal is {{client.goal}}.

    Coach
  `,
  htmlContent: `<p>Hi <strong>{{client.name}}</strong>,</p>...`,
  variables: ['client.name', 'client.goal']
});
```

### Používanie Šablón v Automation

```javascript
{
  "type": "send_template_email",
  "params": {
    "templateId": "my_template",
    "to": "{{client.email}}",
    "data": {
      "extraVariable": "value"
    }
  }
}
```

## 🔄 Scheduled Tasks

### Email Checking (každých 30 minút)

```javascript
{
  "name": "Check Emails",
  "schedule": "0 */30 * * * *",  // Cron format
  "enabled": false  // Zapni po IMAP konfigurácii
}
```

**Ako zapnúť:**
1. Nakonfiguruj IMAP credentials
2. Updatni scheduled task: `enabled: true`
3. Systém automaticky checkuje emaily každých 30 min

### Weekly Check-in Reminders (každý pondelok 9:00)

```javascript
{
  "name": "Weekly Check-in Reminders",
  "schedule": "0 0 9 * * MON",
  "enabled": true
}
```

Pošle reminder všetkým aktívnym klientom.

## 🗄️ Database Schema

### Hlavné Entity

- **clients** - Profily klientov
- **questionnaires** - Dotazníky (raw submissions)
- **training_plans** - Tréningové plány
- **nutrition_plans** - Nutričné plány
- **progress_entries** - Progress check-ins
- **emails** - Email tickets/správy
- **email_threads** - Konverzácie
- **automation_rules** - Automation pravidlá
- **automation_logs** - Logy vykonaných automatizácií
- **email_templates** - Emailové šablóny
- **scheduled_tasks** - Naplánované úlohy
- **settings** - Globálne nastavenia

### Príklad: Client Schema

```javascript
{
  id: "uuid",
  createdAt: "2025-01-15T10:00:00Z",
  updatedAt: "2025-01-15T10:00:00Z",

  // Personal
  name: "John Doe",
  email: "john@example.com",
  age: 32,
  height: "180cm",
  currentWeight: 185,

  // Goals
  goal: "Weight Loss",
  experience: "intermediate",

  // Status
  status: "active",  // pending, active, paused, inactive

  // Plans
  currentTrainingPlanId: "uuid",
  currentNutritionPlanId: "uuid",

  // Constraints
  availableDays: ["mon", "wed", "fri"],
  equipment: ["dumbbells", "barbell"],
  injuries: [],
  dietaryRestrictions: []
}
```

## 🔍 Email Processing Flow

### 1. Questionnaire Email

```
Klient pošle email s dotazníkom
  ↓
IMAP connector stiahne email
  ↓
Parser rozpozná: category = "questionnaire"
  ↓
Extrahuje dáta (meno, vek, váha, goal, atď.)
  ↓
Vytvorí questionnaire record
  ↓
Vytvorí/updatne client profil
  ↓
Trigger event: "questionnaire_received"
  ↓
Automation rule spustí onboarding
  ↓
Vygenerujú sa plány (draft)
  ↓
Pošle sa welcome email
```

### 2. Progress Update Email

```
Klient pošle progress update email
  ↓
Parser rozpozná: category = "progress_update"
  ↓
Extrahuje dáta (váha, energia, compliance, atď.)
  ↓
Vytvorí progress_entry
  ↓
Trigger event: "progress_submitted"
  ↓
Automation analyzuje trend
  ↓
Vygeneruje personalizovaný feedback
  ↓
Pošle email s feedbackom
```

## 🎯 Use Cases

### Use Case 1: Nový Klient

1. Klient vyplní dotazník a pošle emailom
2. Systém automaticky:
   - Vytvorí profil
   - Vygeneruje tréningový plán
   - Vygeneruje nutričný plán
   - Pošle welcome email
3. Tréner reviewne plány a aktivuje ich
4. Klient dostane email že plány sú ready

### Use Case 2: Weekly Check-in

1. Každý pondelok klient dostane reminder
2. Klient pošle progress update (váha, energia, compliance)
3. Systém automaticky:
   - Analyzuje trend váhy
   - Vypočíta priemernú compliance
   - Vygeneruje personalizované odporúčania
   - Pošle feedback email
4. Tréner môže vidieť progress v CRM

### Use Case 3: Manuálny Progress Submit

1. Klient vyplní web form
2. Form zavolá `POST /submit_progress`
3. Systém spracuje a pošle feedback
4. Tréner dostane notifikáciu (optional)

## 🛠️ Development & Testing

### Local Testing

```bash
# Install dependencies
npm install

# Run Netlify Dev (local functions)
netlify dev
```

### Test Endpoints

```bash
# Setup system
curl http://localhost:8888/.netlify/functions/setup?sample=true

# List clients
curl http://localhost:8888/.netlify/functions/clients

# Submit progress
curl -X POST http://localhost:8888/.netlify/functions/submit_progress \
  -H "Content-Type: application/json" \
  -d '{
    "email": "john.doe@example.com",
    "weight": 183,
    "energyLevel": 8,
    "compliance": 85,
    "notes": "Great week!"
  }'

# Check emails (requires IMAP config)
curl http://localhost:8888/.netlify/functions/check_emails
```

### Debugging

Všetky funkcie logujú do konzoly:

```javascript
console.log('[function_name] Message');
```

Môžeš vidieť logy v:
- **Local:** Terminal kde beží `netlify dev`
- **Production:** Netlify Dashboard > Functions > Function logs

## 🚨 Error Handling

Všetky endpointy vracajú štandardný formát:

**Success:**
```json
{
  "ok": true,
  "data": { ... }
}
```

**Error:**
```json
{
  "ok": false,
  "error": "Error message"
}
```

### Common Errors

| Error | Cause | Solution |
|-------|-------|----------|
| "IMAP is not enabled" | IMAP config chýba | Nastav IMAP credentials |
| "Client not found" | Klient neexistuje | Check email alebo clientId |
| "Failed to generate plan" | AI API error | Check GEMINI_API_KEY |
| "Template not found" | Šablóna neexistuje | Run setup endpoint |

## 📈 Next Steps

### Recommended Enhancements

1. **PDF Generation** - Generovanie PDF plánov
2. **File Upload** - Upload progress photos
3. **Webhooks** - Integration s externými službami
4. **Analytics Dashboard** - Stats a metriky
5. **Multi-language Support** - Podpora viacerých jazykov
6. **Mobile App** - Client portal app
7. **Payment Integration** - Stripe/PayPal
8. **Calendar Integration** - Google Calendar sync

### Scaling Considerations

- **Database:** Pre production zvážiť PostgreSQL (Supabase) namiesto Blobs
- **Email:** Pre veľký objem používať Sendgrid/Mailgun API
- **Rate Limiting:** Implementovať rate limiting na API
- **Caching:** Redis cache pre často používané dáta
- **Queue System:** Bull/BullMQ pre background jobs

## 🔐 Security

### Best Practices

1. **Never commit credentials** - Použite `.env` súbory
2. **Validate input** - Validujte všetky user inputs
3. **Sanitize emails** - Pozor na email injection
4. **Rate limiting** - Obmedzte API calls
5. **Authentication** - Pridajte auth pre admin endpoints

### Environment Variables Security

- Netlify automaticky šifruje env vars
- Nikdy ne-commitujte `.env` do gitu
- Používajte Netlify UI na nastavenie production env vars

## 📞 Support

Ak máš otázky alebo problémy:

1. Check logy v Netlify Dashboard
2. Skontroluj IMAP/SMTP credentials
3. Verify že setup endpoint bol zavolaný
4. Check database v Netlify Blobs

---

**Version:** 0.2.0
**Last Updated:** 2025-01-15

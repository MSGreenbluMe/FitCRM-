# Deployment

## Goal

Host the static UI demo publicly and keep API keys off the frontend.

Recommended approach:

- **Netlify** for static hosting + serverless functions
- GitHub for versioning

## Netlify (static + functions)

### What is already prepared in the repo

- `netlify.toml`
  - publishes from repo root
  - redirects `/` to `/demo/`
  - functions directory: `netlify/functions`

### Deploy steps

1. Push repo to GitHub.
2. Create a new site in Netlify.
3. Connect the GitHub repo.
4. Build settings:
   - Build command: `npm install`
   - Publish directory: `.`
5. Deploy.

After deploy:

- App: `https://<your-site>.netlify.app/` (will redirect to `/demo/`)
- Health check:
  - `https://<your-site>.netlify.app/.netlify/functions/health`

### Environment variables

Set in Netlify UI (Site settings -> Environment variables).

Planned variables (do not commit to git):

- `GEMINI_API_KEY`

SMTP (demo approach):

- `SMTP_HOST`
- `SMTP_PORT` (usually `465` for SMTPS or `587` for STARTTLS)
- `SMTP_USER`
- `SMTP_PASS`

For Gmail, use an **App Password** (recommended for demo) and store it in `SMTP_PASS`.

### Test endpoints

Health:

- `/.netlify/functions/health`

Generate plan (Gemini):

- `/.netlify/functions/generate_plan`

Example:

```bash
curl -X POST "https://<your-site>.netlify.app/.netlify/functions/generate_plan" \
  -H "content-type: application/json" \
  -d '{
    "type": "training_plan",
    "goal": "Hypertrophy",
    "client": {
      "name": "Demo Client",
      "age": 30,
      "goal": "Hypertrophy"
    }
  }'
```

Send email (SMTP):

- `/.netlify/functions/send_email`

Example:

```bash
curl -X POST "https://<your-site>.netlify.app/.netlify/functions/send_email" \
  -H "content-type: application/json" \
  -d '{
    "to": "client@example.com",
    "subject": "FitCRM Demo Email",
    "text": "Hello from FitCRM demo",
    "fromName": "FitCRM"
  }'
```

## Notes on Gmail / IMAP

- For serverless platforms, **HTTPS-based APIs** are the most reliable.
- IMAP/SMTP may require outbound ports (993/465/587) that can be restricted depending on the provider.
- If you want full IMAP + SMTP support, consider a small dedicated backend (Render/Fly.io) and keep Netlify only for UI.

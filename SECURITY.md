# Security Notes & Audit

This document summarizes the security posture of FitCRM and the findings/fixes
from the audit on 2026-05-30.

## Architecture recap

- **Frontend** (`demo/`): static, single-user demo. All app data lives in the
  browser's `localStorage`. There is **no login / multi-user auth**.
- **Backend** (`netlify/functions/`): serverless functions.
  - **Used by the frontend:** `generate_plan` (Gemini), `send_email` (SMTP),
    `health`.
  - **Not yet wired to the frontend** (future automation backend, persisted in
    Netlify Blobs): `clients`, `settings`, `setup`, `submit_progress`,
    `check_emails`.

## Fixed in this audit

| # | Finding | Severity | Fix |
|---|---------|----------|-----|
| 1 | The data/automation endpoints (`clients`, `settings`, `setup`, `submit_progress`, `check_emails`) were **public and unauthenticated** once deployed. Anyone could read/delete client PII, seed the database, or change settings. | High | Gated behind a shared secret (`FITCRM_API_TOKEN`). **Disabled by default** (returns `503`) until the env var is set; otherwise requires a matching `x-api-token` header (`401` on mismatch). See `netlify/functions/_shared/guard.js`. |
| 2 | `setup` returned `error.stack` to the client (info disclosure). | Low | Removed stack from the response. |
| 3 | Self-XSS: the trainer's own settings values (name, avatar URL) were injected into `innerHTML` unescaped in `Layout.js` and `SettingsPage.js`. | Low | Added HTML escaping for all user-controlled values. |
| 4 | `settings` backend masked `ai.apiKey` but the frontend uses `ai.geminiApiKey`, and `safeSettings` could throw if a section was missing. | Low | Mask both keys and access sections defensively. |

## Known limitations / accepted risk (demo)

- **`generate_plan` and `send_email` are public and unauthenticated**, because
  the static frontend calls them directly and there is no login system. This
  means that, once the corresponding env vars are configured, a third party who
  knows the URL could:
  - consume your Gemini quota (`generate_plan`), and
  - send email from your configured SMTP account (`send_email`).

  Mitigations for a real deployment (not done here, to keep the demo simple):
  - put the site behind Netlify password protection / access control, or
  - add a real auth layer and move the API key server-side only, and
  - apply rate limiting.

  If you only want to show the UI, you can simply **not set** `GEMINI_API_KEY`
  and `SMTP_*` — the app falls back to a local sample plan and just won't send
  real email.

- **Secrets in `localStorage`:** the Settings page stores the Gemini API key and
  (optional) SMTP/IMAP passwords in the browser in plain text, and sends the
  Gemini key to `generate_plan` with each request. This is acceptable for a
  local single-user demo but is **not** how you'd handle secrets in production.

## Environment variables

| Variable | Purpose | Required? |
|----------|---------|-----------|
| `GEMINI_API_KEY` | AI plan generation. Without it, a safe fallback plan is used. | Optional |
| `SMTP_HOST` / `SMTP_PORT` / `SMTP_USER` / `SMTP_PASS` | Email sending. Without them, `send_email` returns an error. | Optional |
| `FITCRM_API_TOKEN` | Enables the gated data/automation endpoints. Leave unset to keep them disabled. | Optional (keep unset unless you use the backend) |

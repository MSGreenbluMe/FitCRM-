# FitCRM

## Project overview

FitCRM is a **prototype CRM for fitness trainers**.

This repository contains a **functional UI demo** (static Tailwind + vanilla JS) based on the provided Stitch/Tailwind mockups, plus **serverless backend functions** (Netlify Functions) for AI plan generation and email, and technical documentation in `/docs`.

## Deploy live (Netlify)

One-click deploy from GitHub:

[![Deploy to Netlify](https://www.netlify.com/img/deploy/button.svg)](https://app.netlify.com/start/deploy?repository=https://github.com/MSGreenbluMe/FitCRM-)

After the site is created, set the environment variables (Site settings → Environment variables):

- `GEMINI_API_KEY` – enables AI plan generation (otherwise a built-in fallback plan is used)
- `SMTP_HOST`, `SMTP_PORT`, `SMTP_USER`, `SMTP_PASS` – enable email sending (Gmail: use an App Password)

The site serves the demo at `/` (redirects to `/demo/`). Verify the backend with the health check:
`https://<your-site>.netlify.app/.netlify/functions/health`

See `docs/DEPLOYMENT.md` for full details and `curl` test examples.

## Demo (UI)

### What it includes

- Dashboard
- Mailbox (Inbox-style UI) with:
  - folders (Inbox / Assigned / Done / All)
  - ticket status changes (Assign/Done)
  - message composer (adds message to thread)
- Clients (list + detail)
- Training Plan (edit sets/reps/RPE, add exercise from library)
- Nutrition (quick add meals, notes, daily totals)

### Run the demo

Because the demo uses ES modules (`type="module"`), **open it via a local HTTP server** (not `file://`).

Option A (npm script):

```bash
npm run serve
# then open http://localhost:8000/demo/
```

Option B (Netlify Dev — also runs the backend functions locally):

```bash
npm run dev
# serves the demo + /.netlify/functions/* with hot reload
```

Option C (VS Code):

- Use the **Live Server** extension
- Open `demo/index.html`

## Docs

- `docs/FITCRM_PROJECT_SUMMARY.md` – technical overview
- `docs/INBOX.md` – inbox UI requirements
- `docs/DEMO.md` – demo structure and flows

## Troubleshooting

- **Blank page / module error**: make sure you are not opening `demo/index.html` via `file://`.
- **Reset demo state**: click `Reset demo state` in the left navigation.

# FitCRM

## Project overview

FitCRM is a **prototype CRM for fitness trainers**.

This repository currently contains a **functional UI demo** (static Tailwind + vanilla JS) based on the provided Stitch/Tailwind mockups, plus technical documentation in `/docs`.

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

Option A (Python):

- From the repository root, start a server that serves the repo.
- Then open:
  - `http://localhost:8000/demo/`

Option B (VS Code):

- Use the **Live Server** extension
- Open `demo/index.html`

## Docs

- `docs/FITCRM_PROJECT_SUMMARY.md` – technical overview
- `docs/INBOX.md` – inbox UI requirements
- `docs/DEMO.md` – demo structure and flows

## Troubleshooting

- **Blank page / module error**: make sure you are not opening `demo/index.html` via `file://`.
- **Reset demo state**: click `Reset demo state` in the left navigation.

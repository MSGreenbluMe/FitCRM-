# FitCRM Demo

## Purpose

Provide a functional, static UI prototype based on the Stitch/Tailwind mockups.

The demo is intentionally **backend-less** and uses:

- Hash routing (e.g. `#/mailbox`)
- Mock data
- `localStorage` persistence

## Entry point

- `demo/index.html`

## Pages

- Dashboard (`#/dashboard`)
- Mailbox (`#/mailbox`)
  - folders: Inbox / Assigned / Done / All
  - statuses: `new | assigned | done`
- Clients (`#/clients`)
- Training Plan (`#/training-plan`)
- Nutrition (`#/nutrition`)

## State

Main state lives in:

- `demo/src/store.js`

The store persists into:

- `localStorage` key: `fitcrm_demo_state_v1`

## Known limitations

- No real IMAP/SMTP/Gemini integrations (UI only)
- Drag & drop in Training Plan is not implemented

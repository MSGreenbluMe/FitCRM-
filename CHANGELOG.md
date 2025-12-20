# Changelog

## 0.1.9

- AI: global request queue (serialize `generatePlan` calls) to prevent parallel bursts.
- AI: global cooldown persisted in localStorage; during cooldown UI shows "Please wait" without overwriting plans.
- AI: add minimum gap between AI requests and set cooldown immediately on HTTP 429.

## 0.1.8

- AI: stabilize client-side cache key to avoid cache misses (prevents repeated Gemini calls from volatile plan/client payload).
- UX: if Gemini quota is exhausted (429) and no retryAfterSeconds is provided, apply conservative ~10 min cooldown and surface it in the UI.

## 0.1.7

- Training editor: per-day Rest/Training toggle (`day.isRest`) + editable day title.
- Training editor: auto-convert rest day to training day when adding an exercise.
- Fix: define missing `truncate()` helper (prevent UI runtime error in fallback toasts).
- Data: normalize/migrate legacy training plans from localStorage to include `isRest`.

## 0.1.6

- Gemini quota: improved handling of 429 RESOURCE_EXHAUSTED (compact warning + retryAfterSeconds).
- Demo: cache AI generate responses (10 min) and apply retryAfter-based cooldown.

## 0.1.5

- Training AI: prevent duplicate requests (in-flight guard + cooldown) and improve usability.
- Training editor: add exercises to any day (Mon/Tue/Wed/Thu) and auto-create draft plan per client.
- Nutrition: added AI Generate flow (server + UI) with fallback.

## 0.1.4

- Hotfix: hardened `generate_plan` with JSON mode + fallback plan so demo always generates an editable plan.
- QA: fixed several CTA buttons/links to always navigate to existing routes.

## 0.1.3

- Connected demo UI to Netlify Functions (email sending + AI plan generation).
- Implemented `/.netlify/functions/generate_plan` (Gemini via `GEMINI_API_KEY`).

## 0.1.2

- Implemented SMTP email sending via Netlify Function `/.netlify/functions/send_email` (server-side secrets).
- Added `package.json` dependency (`nodemailer`) for functions.

## 0.1.1

- Added Netlify deployment scaffolding (`netlify.toml`, `netlify/functions/*`).
- Added deployment documentation (`docs/DEPLOYMENT.md`).

## 0.1.0

- Added functional static UI demo under `demo/`.
- Added routing and mock state with basic interactions (Mailbox/Clients/Training Plan/Nutrition).

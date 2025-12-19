# Changelog

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

# Progress

## 🚧 In Progress

- (none)

## ✅ Completed

- **API integration (Netlify Functions)**
  - Demo UI calls `/.netlify/functions/send_email`
  - Training Plan uses `/.netlify/functions/generate_plan` (Gemini)

- **Versioned + pushed to GitHub**
  - Repo: `https://github.com/MSGreenbluMe/FitCRM-`
  - Tag: `v0.1.6`

- **Functional UI demo** (static Tailwind + vanilla JS)
  - Routing between: Dashboard / Mailbox / Clients / Training Plan / Nutrition
  - Mock data + basic interactions
  - Local persistence via `localStorage`

- **Project metadata + docs**
  - `README.md`, `CHANGELOG.md`, `TESTING.md`, `LESSONS.md`, `manifest.json`
  - `docs/DEMO.md`

- **Netlify sharing scaffolding**
  - `netlify.toml` (publish root, redirect `/` -> `/demo/`)
  - `netlify/functions/*` stubs
  - `docs/DEPLOYMENT.md`

- **SMTP email function (Netlify)**
  - `/.netlify/functions/send_email` implemented (server-side)
  - `package.json` includes `nodemailer`

## 🔄 Needs Revision

- (none)

## 🔜 Coming Next

- Add more realistic workflows (onboarding from inbox -> create client -> generate/send plan)
- Add drag & drop for training plan builder
- Extend API layer behind the demo (server-side):
  - Improve Gemini structured output reliability (schema + validation)
  - Add nutrition generation endpoint and connect it to Nutrition page

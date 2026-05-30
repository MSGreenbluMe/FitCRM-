# Bugs

## Open

- (none)

## Fixed

- **Open, unauthenticated backend endpoints (PII exposure).** `clients`, `settings`, `setup`, `submit_progress`, `check_emails` were publicly reachable once deployed. Gated behind `FITCRM_API_TOKEN`; disabled by default. (0.2.2)
- **Self-XSS via settings.** Trainer name/avatar were injected into `innerHTML` unescaped (`Layout.js`, `SettingsPage.js`). Now escaped; verified in-browser. (0.2.2)
- **Info disclosure.** `setup` returned `error.stack` to the client. Removed. (0.2.2)
- **Netlify Functions crashed on deploy (CJS/ESM mismatch).** Root `package.json` is `"type": "module"`, but `health.js`, `generate_plan.js`, and `send_email.js` used CommonJS `exports.handler` / `require`, so their handlers resolved to `undefined`. Converted them to ESM (`export const handler`, `import`). Verified all 8 function handlers now load and run. (0.2.1)

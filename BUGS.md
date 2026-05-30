# Bugs

## Open

- (none)

## Fixed

- **Netlify Functions crashed on deploy (CJS/ESM mismatch).** Root `package.json` is `"type": "module"`, but `health.js`, `generate_plan.js`, and `send_email.js` used CommonJS `exports.handler` / `require`, so their handlers resolved to `undefined`. Converted them to ESM (`export const handler`, `import`). Verified all 8 function handlers now load and run. (0.2.1)

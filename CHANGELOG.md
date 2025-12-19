# Changelog

## 0.2.2

- Dashboard UI refined toward Tailwind mockup (dark theme layering) + Slovak labels
- Topbar now includes functional demo panels for notifications and user menu
- Clients page redesigned to split-pane layout (list + detail) aligned to mockup

## 0.2.1

- Improved Inbox list UX for large volumes (paging + table-based selection + snippet + panel cards)
- Improved Gemini free-tier stability (default flash-lite model + rate limiting/backoff + prompt caching)

## 0.2.0

- Added Gmail-like Inbox page (folders, list, preview, actions)
- Added IMAP Email Connector page (test connection, fetch latest emails into Inbox)
- Added `src/email_connector.py` for IMAP connectivity
- Unified displayed app version to use `src.__version__`

## 0.1.0

- Initial FIT CRM pipeline (email parser, AI generator, PDF generator, SMTP sender)

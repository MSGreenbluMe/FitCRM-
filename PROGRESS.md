# Progress

## Current Status

✅ Inbox UI (Gmail-like 3-panel layout) + Email Connector (IMAP) are implemented in Streamlit.

## Completed

✅ Added `📥 Inbox` page (folders, search, status filters, unread state, detail preview, actions)
✅ Added `⚙️ Email konektor` page (IMAP settings, test connection, fetch latest emails into Inbox)
✅ Added IMAP integration layer: `src/email_connector.py`
✅ Unified displayed app version across UI (`src.__version__`)
✅ Added project docs & QA files (PROGRESS/CHANGELOG/TESTING/LESSONS/BUGS/PERFORMANCE + /docs)

## Coming Next

🔜 Persist email connector settings securely (Streamlit secrets / encrypted storage)
🔜 Gmail OAuth connector (instead of app-password IMAP)
🔜 Message threading + labels (Inbox, Starred, etc.)
🔜 Caching + rate-limit / retry policy for IMAP fetch

# Email Connector

## Purpose

Connect a mailbox to the app so incoming emails can populate the Inbox.

## Current implementation

- Protocol: IMAP
- Implementation: `src/email_connector.py`
- UI: `render_email_connector()` in `app.py`

## Credentials

Do not hardcode credentials.

Recommended:

- Use `.env` only for local defaults
- Use Streamlit secrets / secure storage for production

## Coming next

- Gmail OAuth connector
- Caching + retry strategy

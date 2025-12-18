# Inbox UI

## Purpose

Provide an email-client-like Inbox inside the Streamlit app for processing incoming client requests.

## UX layout

- Left: folders (Inbox / Assigned / Done / All)
- Middle: message list (select one)
- Right: message preview + actions

## Data source

- Demo messages: `DEMO_EMAILS` in `app.py`
- IMAP messages: fetched via `src/email_connector.py` and ingested into `st.session_state.email_tickets`

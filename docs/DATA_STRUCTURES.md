# Data Structures

## Inbox ticket (`st.session_state.email_tickets[]`)

Fields:

- `id`: unique string
- `subject`: string
- `from`: string
- `time`: human readable string
- `priority`: `high|normal|low`
- `status`: `new|assigned|done`
- `content`: string
- `read`: boolean
- `source`: `demo|imap`

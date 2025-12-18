# Lessons Learned

- Streamlit `st.session_state` is the safest place to keep UI state for navigation and selection.
- For Inbox-like UIs in Streamlit, `st.radio` with `format_func` provides a more email-client-like selection than many buttons.
- IMAP integration can be done with stdlib (`imaplib` + `email`) and kept dependency-free.
- Credentials should not be committed; prefer `.env` for defaults and Streamlit secrets / secure storage for real usage.

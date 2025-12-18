# Testing

## Checklist (per feature)

### Inbox

- [ ] Inbox page loads without errors
- [ ] Folder switching works (Inbox/Assigned/Done/All)
- [ ] Search filters by subject/from/content
- [ ] Unread-only filter works
- [ ] Selecting a message marks it as read
- [ ] Actions work: Assign / Done / Mark unread / Create client

### Email Connector (IMAP)

- [ ] Test connection works with valid credentials
- [ ] Test connection shows clear error on invalid credentials
- [ ] Fetch emails ingests messages into Inbox
- [ ] Fetch does not duplicate existing messages

### Regression

- [ ] Dashboard still renders
- [ ] Clients list/detail still renders
- [ ] Plan generation flow still works
- [ ] Email sending still works (SMTP)

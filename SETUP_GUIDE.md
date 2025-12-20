# FitCRM Setup Guide 🚀

Quick start guide for setting up the FitCRM backend automation system.

## Prerequisites

- Netlify account
- Gmail account (or other email provider)
- Google Gemini API key

## Step 1: Install Dependencies

```bash
npm install
```

This installs:
- `nodemailer` - Email sending
- `imap` - Email receiving
- `mailparser` - Email parsing
- `@netlify/blobs` - Persistent storage

## Step 2: Configure Email (Gmail)

### Enable IMAP in Gmail

1. Go to Gmail Settings > Forwarding and POP/IMAP
2. Enable IMAP
3. Save changes

### Generate App Password

1. Go to https://myaccount.google.com/security
2. Enable 2-Step Verification (if not already enabled)
3. Go to "App passwords"
4. Generate new app password
5. Copy the 16-character password

## Step 3: Set Environment Variables

### Local Development (.env file)

Create `.env` in the root directory:

```bash
# Email Configuration
IMAP_HOST=imap.gmail.com
IMAP_PORT=993
IMAP_USER=your-email@gmail.com
IMAP_PASSWORD=your-16-char-app-password

SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your-email@gmail.com
SMTP_PASS=your-16-char-app-password

# AI Configuration
GEMINI_API_KEY=your-gemini-api-key

# Netlify
URL=http://localhost:8888
```

### Production (Netlify Dashboard)

1. Go to Site settings > Environment variables
2. Add each variable above
3. Set `URL` to your production URL: `https://your-site.netlify.app`

## Step 4: Deploy to Netlify

### Option A: Git Deploy (Recommended)

```bash
git add .
git commit -m "feat: add backend automation system"
git push origin claude/fitness-coach-automation-HWioz
```

Netlify will auto-deploy.

### Option B: Manual Deploy

```bash
netlify deploy --prod
```

## Step 5: Initialize the System

After deployment, initialize the database with default settings:

```bash
curl https://your-site.netlify.app/.netlify/functions/setup?sample=true
```

This creates:
- ✅ 3 automation rules
- ✅ 3 email templates
- ✅ 2 scheduled tasks
- ✅ Sample client data

**Response:**
```json
{
  "ok": true,
  "message": "FitCRM initialized successfully",
  "created": {
    "automationRules": 3,
    "emailTemplates": 3,
    "scheduledTasks": 2,
    "sampleClients": 1
  }
}
```

## Step 6: Test the System

### Test 1: Check Health

```bash
curl https://your-site.netlify.app/.netlify/functions/health
```

Expected: `{"ok": true, "service": "fitcrm", "version": "0.2.0"}`

### Test 2: List Clients

```bash
curl https://your-site.netlify.app/.netlify/functions/clients
```

Expected: Should return sample client if you ran setup with `?sample=true`

### Test 3: Check Emails (requires IMAP)

```bash
curl https://your-site.netlify.app/.netlify/functions/check_emails
```

Expected: Fetches emails from your inbox

### Test 4: Submit Progress

```bash
curl -X POST https://your-site.netlify.app/.netlify/functions/submit_progress \
  -H "Content-Type: application/json" \
  -d '{
    "email": "john.doe@example.com",
    "weight": 183,
    "energyLevel": 8,
    "sleepQuality": 7,
    "compliance": 85,
    "notes": "Feeling great this week!"
  }'
```

Expected: Creates progress entry and triggers automation

## Step 7: Enable Automatic Email Checking (Optional)

To automatically check emails every 30 minutes, you need to:

### Option A: Netlify Scheduled Functions

Create `netlify/functions/scheduled-email-check.js`:

```javascript
import { schedule } from '@netlify/functions';
import { handler as checkEmails } from './check_emails.js';

export const handler = schedule('*/30 * * * *', async (event) => {
  return await checkEmails(event);
});
```

### Option B: External Cron Service

Use a service like:
- **cron-job.org**
- **EasyCron**
- **GitHub Actions**

Configure to call:
```
GET https://your-site.netlify.app/.netlify/functions/check_emails
```

Every 30 minutes.

## Testing Email Automation

### Test Questionnaire Email

Send an email to your IMAP email with subject "New Client Questionnaire" and body:

```
Name: John Doe
Age: 32
Weight: 185 lbs
Height: 180cm
Goal: Weight Loss
Experience: Intermediate
Equipment: Dumbbells, Barbell
Days available: Monday, Wednesday, Friday
Injuries: None
Dietary restrictions: None
```

Then call check_emails:

```bash
curl https://your-site.netlify.app/.netlify/functions/check_emails
```

Expected flow:
1. ✅ Email fetched
2. ✅ Classified as "questionnaire"
3. ✅ Client profile created
4. ✅ Automation triggered
5. ✅ Training plan generated
6. ✅ Nutrition plan generated
7. ✅ Welcome email sent

### Test Progress Update Email

Send email with subject "Weekly Progress Update":

```
Weight: 183 lbs
Energy: 8/10
Sleep: 7/10
Compliance: 85%
Notes: Great week! Feeling strong.
```

Expected flow:
1. ✅ Email fetched
2. ✅ Classified as "progress_update"
3. ✅ Progress entry created
4. ✅ Trend analyzed
5. ✅ Feedback generated
6. ✅ Response email sent

## Troubleshooting

### "IMAP is not enabled"

**Solution:** Set IMAP environment variables in Netlify dashboard

### "Authentication failed" (IMAP/SMTP)

**Solutions:**
- Use Gmail App Password (not regular password)
- Enable "Less secure app access" (not recommended)
- Check username is full email address

### "Failed to generate plan"

**Solution:** Check `GEMINI_API_KEY` is set correctly

### "Template not found"

**Solution:** Run the setup endpoint: `curl .../setup`

### No emails being fetched

**Solutions:**
- Check IMAP credentials
- Verify emails are marked as UNSEEN
- Check inbox folder name (might be "Inbox" vs "INBOX")

## Monitoring

### View Function Logs

Netlify Dashboard > Functions > Select function > View logs

### Check Automation Logs

Query the database:

```javascript
// In a function:
const db = getDatabase();
const logs = await db.query('automation_logs', {}, {
  orderBy: 'createdAt:desc',
  limit: 10
});
```

## Next Steps

1. **Customize Email Templates**
   - Edit templates in database
   - Add your branding
   - Adjust tone/language

2. **Create Custom Automation Rules**
   - Add new triggers
   - Chain multiple actions
   - Set up conditional logic

3. **Integrate Frontend**
   - Update UI to call new APIs
   - Show real-time progress
   - Display automation status

4. **Add Authentication**
   - Implement Netlify Identity
   - Protect admin endpoints
   - Create client portal

5. **Enable Scheduled Tasks**
   - Set up cron for email checking
   - Send weekly reminders
   - Generate reports

## Support

For detailed documentation, see [BACKEND_DOCUMENTATION.md](./BACKEND_DOCUMENTATION.md)

For issues:
1. Check Netlify function logs
2. Verify environment variables
3. Test each endpoint individually

---

**Version:** 0.2.0

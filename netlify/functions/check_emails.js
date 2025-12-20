/**
 * Check Emails Function
 *
 * Fetches new emails via IMAP and processes them
 * Can be triggered:
 * - Manually via API call
 * - By scheduled function (cron)
 * - By webhook
 */

import { createEmailProcessor } from './services/email-processor.js';
import { getAutomationEngine } from './services/automation-engine.js';
import { getDatabase } from './db/database.js';

export async function handler(event, context) {
  console.log('[check_emails] Starting email check...');

  const db = getDatabase();
  const automation = getAutomationEngine();

  try {
    // Get settings
    const settings = await db.getSettings();

    if (!settings.email?.imapEnabled) {
      return {
        statusCode: 400,
        body: JSON.stringify({
          ok: false,
          error: 'IMAP is not enabled. Please configure email settings.'
        })
      };
    }

    // Create email processor
    const processor = await createEmailProcessor();

    // Fetch new emails
    console.log('[check_emails] Fetching emails from IMAP...');
    const emails = await processor.fetchNewEmails('INBOX', 50);

    console.log(`[check_emails] Found ${emails.length} new emails`);

    // Process each email
    const results = await processor.processEmails(emails);

    // Trigger automation events
    const automationResults = [];
    for (const result of results) {
      if (result.category === 'questionnaire') {
        // Trigger client_created or questionnaire_received event
        const eventResults = await automation.triggerEvent('questionnaire_received', {
          emailId: result.emailId,
          clientId: result.clientId,
          category: result.category
        });
        automationResults.push(...eventResults);
      }

      if (result.category === 'progress_update') {
        // Trigger progress_submitted event
        const eventResults = await automation.triggerEvent('progress_submitted', {
          emailId: result.emailId,
          clientId: result.clientId,
          progressId: result.processed?.actions?.[0]?.progressId
        });
        automationResults.push(...eventResults);
      }
    }

    return {
      statusCode: 200,
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        ok: true,
        emailsChecked: emails.length,
        processed: results.length,
        automationRulesTriggered: automationResults.length,
        results: results.map(r => ({
          emailId: r.emailId,
          category: r.category,
          clientId: r.clientId
        }))
      })
    };

  } catch (error) {
    console.error('[check_emails] Error:', error);

    return {
      statusCode: 500,
      body: JSON.stringify({
        ok: false,
        error: error.message
      })
    };
  }
}

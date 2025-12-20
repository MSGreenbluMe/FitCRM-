/**
 * Email Processing Service
 *
 * Handles:
 * - Fetching emails via IMAP
 * - Parsing email content
 * - Classifying emails (questionnaire, progress update, question)
 * - Extracting structured data
 * - Triggering automation workflows
 */

import Imap from 'imap';
import { simpleParser } from 'mailparser';
import { getDatabase } from '../db/database.js';

export class EmailProcessor {
  constructor(config) {
    this.config = config;
    this.db = getDatabase();
    this.imap = null;
  }

  /**
   * Connect to IMAP server
   */
  async connect() {
    return new Promise((resolve, reject) => {
      this.imap = new Imap({
        user: this.config.user,
        password: this.config.password,
        host: this.config.host,
        port: this.config.port || 993,
        tls: this.config.tls !== false,
        tlsOptions: { rejectUnauthorized: false }
      });

      this.imap.once('ready', () => resolve());
      this.imap.once('error', (err) => reject(err));
      this.imap.connect();
    });
  }

  /**
   * Disconnect from IMAP
   */
  disconnect() {
    if (this.imap) {
      this.imap.end();
    }
  }

  /**
   * Fetch new emails
   */
  async fetchNewEmails(mailbox = 'INBOX', limit = 50) {
    await this.connect();

    return new Promise((resolve, reject) => {
      this.imap.openBox(mailbox, false, async (err, box) => {
        if (err) {
          this.disconnect();
          return reject(err);
        }

        try {
          // Search for unseen emails
          this.imap.search(['UNSEEN'], async (err, results) => {
            if (err) {
              this.disconnect();
              return reject(err);
            }

            if (!results || results.length === 0) {
              this.disconnect();
              return resolve([]);
            }

            // Limit results
            const messageIds = results.slice(0, limit);
            const emails = [];

            const fetch = this.imap.fetch(messageIds, {
              bodies: '',
              markSeen: false
            });

            fetch.on('message', (msg, seqno) => {
              let buffer = '';

              msg.on('body', (stream, info) => {
                stream.on('data', (chunk) => {
                  buffer += chunk.toString('utf8');
                });
              });

              msg.once('end', async () => {
                try {
                  const parsed = await simpleParser(buffer);
                  emails.push({
                    seqno,
                    parsed,
                    messageId: parsed.messageId,
                    from: parsed.from?.text || '',
                    to: parsed.to?.text || '',
                    subject: parsed.subject || '',
                    date: parsed.date,
                    textContent: parsed.text || '',
                    htmlContent: parsed.html || '',
                    attachments: parsed.attachments || []
                  });
                } catch (parseErr) {
                  console.error('Error parsing email:', parseErr);
                }
              });
            });

            fetch.once('error', (err) => {
              this.disconnect();
              reject(err);
            });

            fetch.once('end', () => {
              this.disconnect();
              resolve(emails);
            });
          });
        } catch (error) {
          this.disconnect();
          reject(error);
        }
      });
    });
  }

  /**
   * Process emails and save to database
   */
  async processEmails(emails) {
    const results = [];

    for (const email of emails) {
      try {
        const result = await this.processEmail(email);
        results.push(result);
      } catch (error) {
        console.error('Error processing email:', error);
        results.push({ error: error.message, email });
      }
    }

    return results;
  }

  /**
   * Process a single email
   */
  async processEmail(email) {
    // Extract email address from "Name <email@domain.com>" format
    const fromEmail = this.extractEmail(email.from);
    const toEmail = this.extractEmail(email.to);

    // Check if client exists
    let client = await this.db.getClientByEmail(fromEmail);

    // Classify email
    const classification = this.classifyEmail(email);

    // Create email record
    const emailRecord = await this.db.createEmail({
      messageId: email.messageId,
      from: fromEmail,
      to: toEmail,
      subject: email.subject,
      textContent: email.textContent,
      htmlContent: email.htmlContent,
      clientId: client?.id,
      category: classification.category,
      priority: classification.priority,
      source: 'imap',
      attachments: email.attachments.map(att => ({
        filename: att.filename,
        contentType: att.contentType,
        size: att.size
      }))
    });

    // Auto-process based on category
    const processingResult = await this.autoProcess(emailRecord, email, client);

    // Update email with processing results
    await this.db.updateEmail(emailRecord.id, {
      autoProcessed: true,
      processingResults: processingResult
    });

    return {
      emailId: emailRecord.id,
      clientId: client?.id,
      category: classification.category,
      processed: processingResult
    };
  }

  /**
   * Classify email type
   */
  classifyEmail(email) {
    const subject = email.subject.toLowerCase();
    const text = email.textContent.toLowerCase();
    const combined = subject + ' ' + text;

    // Check for questionnaire keywords
    const questionnaireKeywords = [
      'questionnaire', 'dotazník', 'new client', 'nový klient',
      'registration', 'registrácia', 'sign up', 'prihlásenie',
      'onboarding', 'začíname', 'getting started'
    ];

    if (questionnaireKeywords.some(kw => combined.includes(kw))) {
      return { category: 'questionnaire', priority: 'high' };
    }

    // Check for progress update keywords
    const progressKeywords = [
      'progress', 'pokrok', 'check-in', 'check in', 'update', 'aktualizácia',
      'weight', 'váha', 'measurements', 'merania', 'photos', 'fotky'
    ];

    if (progressKeywords.some(kw => combined.includes(kw))) {
      return { category: 'progress_update', priority: 'normal' };
    }

    // Check for urgent keywords
    const urgentKeywords = [
      'urgent', 'urgentné', 'important', 'dôležité', 'help', 'pomoc',
      'injury', 'zranenie', 'pain', 'bolesť', 'problem', 'problém'
    ];

    const priority = urgentKeywords.some(kw => combined.includes(kw))
      ? 'high'
      : 'normal';

    return { category: 'question', priority };
  }

  /**
   * Auto-process email based on category
   */
  async autoProcess(emailRecord, email, client) {
    const { category } = emailRecord;
    const results = { type: category, actions: [] };

    try {
      if (category === 'questionnaire') {
        // Parse questionnaire and create/update client
        const questionnaireResult = await this.processQuestionnaire(email, client);
        results.actions.push(questionnaireResult);
        return results;
      }

      if (category === 'progress_update') {
        // Parse progress data and create progress entry
        const progressResult = await this.processProgressUpdate(email, client);
        results.actions.push(progressResult);
        return results;
      }

      // For questions, just mark as needing manual review
      results.actions.push({
        action: 'manual_review_required',
        reason: 'Question requires trainer response'
      });

    } catch (error) {
      results.error = error.message;
    }

    return results;
  }

  /**
   * Process questionnaire email
   */
  async processQuestionnaire(email, existingClient) {
    const formData = this.parseQuestionnaire(email.textContent);

    // Create questionnaire record
    const questionnaire = await this.db.createQuestionnaire({
      email: this.extractEmail(email.from),
      emailMessageId: email.messageId,
      formData,
      status: 'processing'
    });

    try {
      // Extract client data
      const clientData = this.extractClientData(formData);

      let client;
      if (existingClient) {
        // Update existing client
        client = await this.db.updateClient(existingClient.id, clientData);
      } else {
        // Create new client
        client = await this.db.createClient({
          ...clientData,
          email: this.extractEmail(email.from),
          status: 'pending',
          source: 'email_questionnaire'
        });
      }

      // Update questionnaire
      await this.db.updateQuestionnaire(questionnaire.id, {
        status: 'processed',
        clientId: client.id,
        extractedData: clientData,
        actionsPerformed: [
          {
            action: existingClient ? 'client_updated' : 'client_created',
            id: client.id,
            timestamp: new Date().toISOString()
          }
        ]
      });

      return {
        action: existingClient ? 'client_updated' : 'client_created',
        clientId: client.id,
        questionnaireId: questionnaire.id,
        success: true
      };

    } catch (error) {
      // Mark questionnaire as failed
      await this.db.updateQuestionnaire(questionnaire.id, {
        status: 'failed',
        errors: [error.message]
      });

      throw error;
    }
  }

  /**
   * Parse questionnaire from email text
   */
  parseQuestionnaire(text) {
    const formData = {};

    // Common patterns for extracting data
    const patterns = {
      name: /(?:name|meno|jméno):\s*(.+)/i,
      age: /(?:age|vek|věk):\s*(\d+)/i,
      weight: /(?:weight|váha|hmotnost):\s*(\d+(?:\.\d+)?)\s*(?:lbs|kg|pounds)?/i,
      height: /(?:height|výška):\s*(\d+(?:\.\d+)?)\s*(?:cm|m|ft|'|")?/i,
      goal: /(?:goal|cieľ|cíl):\s*(.+)/i,
      experience: /(?:experience|skúsenosť|zkušenost):\s*(.+)/i,
      injuries: /(?:injuries|zranenia|zranění):\s*(.+)/i,
      equipment: /(?:equipment|vybavenie):\s*(.+)/i,
      days: /(?:days available|dostupné dni|available days):\s*(.+)/i,
      dietary: /(?:dietary restrictions|diétne obmedzenia|stravovací omezení):\s*(.+)/i
    };

    for (const [key, pattern] of Object.entries(patterns)) {
      const match = text.match(pattern);
      if (match) {
        formData[key] = match[1].trim();
      }
    }

    return formData;
  }

  /**
   * Extract client data from parsed questionnaire
   */
  extractClientData(formData) {
    const clientData = {};

    if (formData.name) clientData.name = formData.name;
    if (formData.age) clientData.age = parseInt(formData.age);
    if (formData.weight) clientData.currentWeight = parseFloat(formData.weight);
    if (formData.height) clientData.height = formData.height;
    if (formData.goal) clientData.goal = formData.goal;
    if (formData.experience) clientData.experience = formData.experience;

    if (formData.injuries) {
      clientData.injuries = formData.injuries
        .split(/,|;/)
        .map(i => i.trim())
        .filter(Boolean);
    }

    if (formData.equipment) {
      clientData.equipment = formData.equipment
        .split(/,|;/)
        .map(e => e.trim())
        .filter(Boolean);
    }

    if (formData.days) {
      clientData.availableDays = formData.days
        .toLowerCase()
        .split(/,|;/)
        .map(d => d.trim())
        .filter(Boolean);
    }

    if (formData.dietary) {
      clientData.dietaryRestrictions = formData.dietary
        .split(/,|;/)
        .map(d => d.trim())
        .filter(Boolean);
    }

    return clientData;
  }

  /**
   * Process progress update email
   */
  async processProgressUpdate(email, client) {
    if (!client) {
      return {
        action: 'progress_update_failed',
        reason: 'Client not found',
        success: false
      };
    }

    const progressData = this.parseProgressUpdate(email.textContent);

    // Create progress entry
    const progressEntry = await this.db.createProgressEntry({
      clientId: client.id,
      emailMessageId: email.messageId,
      ...progressData,
      rawText: email.textContent,
      status: 'pending'
    });

    return {
      action: 'progress_entry_created',
      progressId: progressEntry.id,
      clientId: client.id,
      success: true
    };
  }

  /**
   * Parse progress update from email text
   */
  parseProgressUpdate(text) {
    const data = {};

    // Weight
    const weightMatch = text.match(/(?:weight|váha):\s*(\d+(?:\.\d+)?)\s*(?:lbs|kg)?/i);
    if (weightMatch) {
      data.weight = parseFloat(weightMatch[1]);
    }

    // Body fat
    const bfMatch = text.match(/(?:body fat|telesný tuk):\s*(\d+(?:\.\d+)?)\s*%?/i);
    if (bfMatch) {
      data.bodyFatPct = parseFloat(bfMatch[1]);
    }

    // Energy level (1-10)
    const energyMatch = text.match(/(?:energy|energia):\s*(\d+)(?:\/10)?/i);
    if (energyMatch) {
      data.energyLevel = parseInt(energyMatch[1]);
    }

    // Sleep quality (1-10)
    const sleepMatch = text.match(/(?:sleep|spánok):\s*(\d+)(?:\/10)?/i);
    if (sleepMatch) {
      data.sleepQuality = parseInt(sleepMatch[1]);
    }

    // Compliance (percentage)
    const complianceMatch = text.match(/(?:compliance|dodržiavanie):\s*(\d+)\s*%?/i);
    if (complianceMatch) {
      data.compliance = parseInt(complianceMatch[1]);
    }

    // Notes - extract everything after "notes:" or "poznámky:"
    const notesMatch = text.match(/(?:notes|poznámky|comments|komentáre):\s*(.+)/is);
    if (notesMatch) {
      data.notes = notesMatch[1].trim();
    }

    return data;
  }

  /**
   * Extract email address from "Name <email@domain.com>" format
   */
  extractEmail(str) {
    if (!str) return '';
    const match = str.match(/<([^>]+)>/);
    return match ? match[1] : str.split(/\s+/)[0];
  }

  /**
   * Mark email as seen
   */
  async markAsSeen(messageId) {
    // Implementation depends on IMAP library
    // This would mark the message as seen in the mailbox
  }
}

/**
 * Create email processor from settings
 */
export async function createEmailProcessor() {
  const db = getDatabase();
  const settings = await db.getSettings();

  if (!settings.email?.imapEnabled) {
    throw new Error('IMAP is not enabled in settings');
  }

  return new EmailProcessor({
    user: settings.email.imapUser || process.env.IMAP_USER,
    password: settings.email.imapPassword || process.env.IMAP_PASSWORD,
    host: settings.email.imapHost || process.env.IMAP_HOST,
    port: settings.email.imapPort || 993,
    tls: true
  });
}

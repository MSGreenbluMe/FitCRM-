/**
 * Settings API
 *
 * GET /settings - Get current settings
 * PUT /settings - Update settings
 */

import { getDatabase } from './db/database.js';
import { requireApiToken } from './_shared/guard.js';

export async function handler(event, context) {
  const blocked = requireApiToken(event);
  if (blocked) return blocked;

  const db = getDatabase();
  const { httpMethod, body } = event;

  try {
    // GET /settings - Get current settings
    if (httpMethod === 'GET') {
      const settings = await db.getSettings();

      // Don't send sensitive data to frontend (defensive against missing sections)
      const email = settings.email || {};
      const ai = settings.ai || {};
      const safeSettings = {
        ...settings,
        email: {
          ...email,
          imapPassword: email.imapPassword ? '••••••••' : '',
          smtpPassword: email.smtpPassword ? '••••••••' : ''
        },
        ai: {
          ...ai,
          // Support both legacy `apiKey` and the frontend's `geminiApiKey`
          apiKey: ai.apiKey ? '••••••••' : '',
          geminiApiKey: ai.geminiApiKey ? '••••••••' : ''
        }
      };

      return {
        statusCode: 200,
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          ok: true,
          settings: safeSettings
        })
      };
    }

    // PUT /settings - Update settings
    if (httpMethod === 'PUT') {
      const updates = JSON.parse(body);

      // Validate structure
      const allowedSections = ['profile', 'email', 'ai', 'automation', 'business'];
      const updateData = {};

      for (const [section, data] of Object.entries(updates)) {
        if (allowedSections.includes(section)) {
          updateData[section] = data;
        }
      }

      // Update settings
      const settings = await db.updateSettings(updateData);

      return {
        statusCode: 200,
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          ok: true,
          message: 'Settings updated successfully',
          settings
        })
      };
    }

    return {
      statusCode: 405,
      body: JSON.stringify({ error: 'Method not allowed' })
    };

  } catch (error) {
    console.error('[settings] Error:', error);

    return {
      statusCode: 500,
      body: JSON.stringify({
        ok: false,
        error: error.message
      })
    };
  }
}

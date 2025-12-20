/**
 * Submit Progress Function
 *
 * Endpoint for clients to submit progress updates
 * Can be called via:
 * - Web form
 * - API
 * - Email (processed by email processor)
 */

import { getDatabase } from './db/database.js';
import { getAutomationEngine } from './services/automation-engine.js';

export async function handler(event, context) {
  if (event.httpMethod !== 'POST') {
    return {
      statusCode: 405,
      body: JSON.stringify({ error: 'Method not allowed' })
    };
  }

  const db = getDatabase();
  const automation = getAutomationEngine();

  try {
    const data = JSON.parse(event.body);

    // Validate required fields
    if (!data.clientId && !data.email) {
      return {
        statusCode: 400,
        body: JSON.stringify({
          ok: false,
          error: 'clientId or email required'
        })
      };
    }

    // Get client
    let client;
    if (data.clientId) {
      client = await db.getClient(data.clientId);
    } else {
      client = await db.getClientByEmail(data.email);
    }

    if (!client) {
      return {
        statusCode: 404,
        body: JSON.stringify({
          ok: false,
          error: 'Client not found'
        })
      };
    }

    // Create progress entry
    const progressEntry = await db.createProgressEntry({
      clientId: client.id,
      type: data.type || 'weekly',
      weekNumber: data.weekNumber,
      weight: data.weight,
      bodyFatPct: data.bodyFatPct,
      measurements: data.measurements,
      photoUrls: data.photoUrls,
      energyLevel: data.energyLevel,
      sleepQuality: data.sleepQuality,
      stressLevel: data.stressLevel,
      hunger: data.hunger,
      compliance: data.compliance,
      notes: data.notes,
      challenges: data.challenges,
      wins: data.wins,
      status: 'pending'
    });

    console.log(`[submit_progress] Created progress entry: ${progressEntry.id}`);

    // Update client last activity
    await db.updateClient(client.id, {
      lastActivityAt: new Date().toISOString()
    });

    // Trigger automation event
    const settings = await db.getSettings();
    let automationResult = null;

    if (settings.automation?.autoRespondProgress) {
      console.log('[submit_progress] Triggering automation...');

      const eventResults = await automation.triggerEvent('progress_submitted', {
        clientId: client.id,
        progressId: progressEntry.id,
        progressEntry,
        client
      });

      automationResult = eventResults;

      // Mark as processed
      await db.updateProgressEntry(progressEntry.id, {
        status: 'processed'
      });
    }

    return {
      statusCode: 200,
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        ok: true,
        progressId: progressEntry.id,
        clientId: client.id,
        automated: !!automationResult,
        message: 'Progress submitted successfully'
      })
    };

  } catch (error) {
    console.error('[submit_progress] Error:', error);

    return {
      statusCode: 500,
      body: JSON.stringify({
        ok: false,
        error: error.message
      })
    };
  }
}

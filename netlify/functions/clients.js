/**
 * Clients API
 *
 * CRUD operations for clients
 */

import { getDatabase } from './db/database.js';

export async function handler(event, context) {
  const db = getDatabase();
  const { httpMethod, path, body } = event;
  const pathParts = path.split('/').filter(Boolean);
  const clientId = pathParts[pathParts.length - 1];

  try {
    // GET /clients - List all clients
    // GET /clients/:id - Get single client
    if (httpMethod === 'GET') {
      if (clientId && clientId !== 'clients') {
        const client = await db.getClient(clientId);
        if (!client) {
          return {
            statusCode: 404,
            body: JSON.stringify({ error: 'Client not found' })
          };
        }

        // Get related data
        const trainingPlans = await db.getClientTrainingPlans(clientId);
        const nutritionPlans = await db.getClientNutritionPlans(clientId);
        const progress = await db.getClientProgress(clientId, 10);
        const emails = await db.getClientEmails(clientId);

        return {
          statusCode: 200,
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            ok: true,
            client,
            trainingPlans,
            nutritionPlans,
            progress,
            emails
          })
        };
      }

      // List clients with optional filters
      const query = event.queryStringParameters || {};
      const filter = {};

      if (query.status) filter.status = query.status;
      if (query.email) filter.email = query.email;

      const clients = await db.listClients(filter);

      return {
        statusCode: 200,
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          ok: true,
          clients,
          total: clients.length
        })
      };
    }

    // POST /clients - Create new client
    if (httpMethod === 'POST') {
      const data = JSON.parse(body);

      // Check if client with email already exists
      if (data.email) {
        const existing = await db.getClientByEmail(data.email);
        if (existing) {
          return {
            statusCode: 409,
            body: JSON.stringify({
              ok: false,
              error: 'Client with this email already exists',
              clientId: existing.id
            })
          };
        }
      }

      const client = await db.createClient(data);

      return {
        statusCode: 201,
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          ok: true,
          client
        })
      };
    }

    // PUT/PATCH /clients/:id - Update client
    if ((httpMethod === 'PUT' || httpMethod === 'PATCH') && clientId) {
      const data = JSON.parse(body);
      const client = await db.updateClient(clientId, data);

      return {
        statusCode: 200,
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          ok: true,
          client
        })
      };
    }

    // DELETE /clients/:id - Delete client
    if (httpMethod === 'DELETE' && clientId) {
      const deleted = await db.delete('clients', clientId);

      if (!deleted) {
        return {
          statusCode: 404,
          body: JSON.stringify({ error: 'Client not found' })
        };
      }

      return {
        statusCode: 200,
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          ok: true,
          deleted: true
        })
      };
    }

    return {
      statusCode: 405,
      body: JSON.stringify({ error: 'Method not allowed' })
    };

  } catch (error) {
    console.error('[clients] Error:', error);

    return {
      statusCode: 500,
      body: JSON.stringify({
        ok: false,
        error: error.message
      })
    };
  }
}

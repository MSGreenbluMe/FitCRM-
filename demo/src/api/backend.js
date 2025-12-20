/**
 * Backend API Client
 *
 * Helper functions to interact with the new backend APIs
 */

const API_BASE = '/.netlify/functions';

/**
 * Generic API call helper
 */
async function apiCall(endpoint, options = {}) {
  const url = `${API_BASE}/${endpoint}`;

  try {
    const response = await fetch(url, {
      ...options,
      headers: {
        'Content-Type': 'application/json',
        ...options.headers
      }
    });

    const data = await response.json();

    if (!response.ok) {
      throw new Error(data.error || `API error: ${response.status}`);
    }

    return data;
  } catch (error) {
    console.error(`[API] ${endpoint} failed:`, error);
    throw error;
  }
}

/**
 * Client Management
 */
export const clients = {
  /**
   * List all clients
   */
  async list(filters = {}) {
    const params = new URLSearchParams(filters);
    const query = params.toString() ? `?${params}` : '';
    return await apiCall(`clients${query}`);
  },

  /**
   * Get single client with all related data
   */
  async get(clientId) {
    return await apiCall(`clients/${clientId}`);
  },

  /**
   * Create new client
   */
  async create(clientData) {
    return await apiCall('clients', {
      method: 'POST',
      body: JSON.stringify(clientData)
    });
  },

  /**
   * Update client
   */
  async update(clientId, updates) {
    return await apiCall(`clients/${clientId}`, {
      method: 'PUT',
      body: JSON.stringify(updates)
    });
  },

  /**
   * Delete client
   */
  async delete(clientId) {
    return await apiCall(`clients/${clientId}`, {
      method: 'DELETE'
    });
  }
};

/**
 * Progress Tracking
 */
export const progress = {
  /**
   * Submit progress update
   */
  async submit(data) {
    return await apiCall('submit_progress', {
      method: 'POST',
      body: JSON.stringify(data)
    });
  }
};

/**
 * Email Management
 */
export const emails = {
  /**
   * Check for new emails
   */
  async check() {
    return await apiCall('check_emails');
  }
};

/**
 * Plan Generation
 */
export const plans = {
  /**
   * Generate training or nutrition plan
   */
  async generate(client, type, constraints = {}) {
    return await apiCall('generate_plan', {
      method: 'POST',
      body: JSON.stringify({
        client,
        goal: client.goal,
        type,
        constraints
      })
    });
  }
};

/**
 * System Setup
 */
export const system = {
  /**
   * Initialize system with defaults
   */
  async setup(includeSample = false) {
    const query = includeSample ? '?sample=true' : '';
    return await apiCall(`setup${query}`);
  },

  /**
   * Health check
   */
  async health() {
    return await apiCall('health');
  }
};

/**
 * Migration helper - sync localStorage data to backend
 */
export async function migrateLocalStorageToBackend() {
  try {
    // Get data from localStorage
    const localData = localStorage.getItem('fitcrm-data');
    if (!localData) {
      console.log('[Migration] No localStorage data found');
      return { migrated: 0 };
    }

    const data = JSON.parse(localData);
    const migrated = { clients: 0, tickets: 0 };

    // Migrate clients
    if (data.clients && Array.isArray(data.clients)) {
      for (const client of data.clients) {
        try {
          await clients.create(client);
          migrated.clients++;
        } catch (error) {
          console.warn('[Migration] Failed to migrate client:', client.email, error);
        }
      }
    }

    // Migrate tickets as emails
    // (tickets would need custom migration logic)

    console.log('[Migration] Completed:', migrated);
    return migrated;
  } catch (error) {
    console.error('[Migration] Failed:', error);
    throw error;
  }
}

/**
 * Example Usage:
 *
 * // List all active clients
 * const result = await clients.list({ status: 'active' });
 * console.log(result.clients);
 *
 * // Get client details
 * const client = await clients.get('client-id');
 * console.log(client.client, client.trainingPlans, client.progress);
 *
 * // Submit progress
 * await progress.submit({
 *   email: 'client@example.com',
 *   weight: 180,
 *   energyLevel: 8,
 *   compliance: 85,
 *   notes: 'Great week!'
 * });
 *
 * // Check emails
 * const emailCheck = await emails.check();
 * console.log(`Processed ${emailCheck.processed} emails`);
 *
 * // Generate plan
 * const plan = await plans.generate(client, 'training_plan', {
 *   availableDays: ['mon', 'wed', 'fri'],
 *   equipment: ['dumbbells']
 * });
 *
 * // Initialize system
 * await system.setup(true);  // with sample data
 */

export default {
  clients,
  progress,
  emails,
  plans,
  system,
  migrateLocalStorageToBackend
};

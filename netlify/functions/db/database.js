/**
 * FitCRM Database Abstraction Layer
 *
 * Uses Netlify Blobs for persistent storage
 * Provides CRUD operations for all entities
 */

import { getStore } from '@netlify/blobs';
import { randomUUID } from 'crypto';

/**
 * Database class - handles all data operations
 */
export class Database {
  constructor() {
    this.stores = {};
  }

  /**
   * Get or create a blob store for a collection
   */
  getStore(collection) {
    if (!this.stores[collection]) {
      this.stores[collection] = getStore({
        name: collection,
        consistency: 'strong'
      });
    }
    return this.stores[collection];
  }

  /**
   * Generate a new UUID
   */
  uuid() {
    return randomUUID();
  }

  /**
   * Current timestamp
   */
  now() {
    return new Date().toISOString();
  }

  // ==========================================================================
  // GENERIC CRUD OPERATIONS
  // ==========================================================================

  /**
   * Create a new document
   */
  async create(collection, data) {
    const store = this.getStore(collection);
    const id = data.id || this.uuid();
    const timestamp = this.now();

    const doc = {
      ...data,
      id,
      createdAt: data.createdAt || timestamp,
      updatedAt: data.updatedAt || timestamp
    };

    await store.set(id, JSON.stringify(doc));

    // Update indexes
    await this._updateIndexes(collection, doc);

    return doc;
  }

  /**
   * Get a document by ID
   */
  async get(collection, id) {
    const store = this.getStore(collection);
    const data = await store.get(id);

    if (!data) {
      return null;
    }

    return JSON.parse(data);
  }

  /**
   * Update a document
   */
  async update(collection, id, updates) {
    const store = this.getStore(collection);
    const existing = await this.get(collection, id);

    if (!existing) {
      throw new Error(`Document ${id} not found in ${collection}`);
    }

    const updated = {
      ...existing,
      ...updates,
      id, // Ensure ID doesn't change
      createdAt: existing.createdAt, // Preserve creation time
      updatedAt: this.now()
    };

    await store.set(id, JSON.stringify(updated));

    // Update indexes
    await this._updateIndexes(collection, updated);

    return updated;
  }

  /**
   * Delete a document
   */
  async delete(collection, id) {
    const store = this.getStore(collection);
    const doc = await this.get(collection, id);

    if (!doc) {
      return false;
    }

    await store.delete(id);

    // Remove from indexes
    await this._removeFromIndexes(collection, doc);

    return true;
  }

  /**
   * List all documents in a collection
   */
  async list(collection, options = {}) {
    const store = this.getStore(collection);
    const { limit = 1000, prefix = '' } = options;

    const { blobs } = await store.list({ prefix, limit });

    const docs = await Promise.all(
      blobs.map(async (blob) => {
        const data = await store.get(blob.key);
        return JSON.parse(data);
      })
    );

    return docs;
  }

  /**
   * Query documents with filters
   */
  async query(collection, filter = {}, options = {}) {
    const docs = await this.list(collection);
    let results = docs;

    // Apply filters
    results = results.filter(doc => {
      return Object.entries(filter).every(([key, value]) => {
        if (typeof value === 'function') {
          return value(doc[key]);
        }
        return doc[key] === value;
      });
    });

    // Sort
    if (options.orderBy) {
      const [field, direction = 'asc'] = options.orderBy.split(':');
      results.sort((a, b) => {
        const aVal = a[field];
        const bVal = b[field];
        const cmp = aVal < bVal ? -1 : aVal > bVal ? 1 : 0;
        return direction === 'desc' ? -cmp : cmp;
      });
    }

    // Limit
    if (options.limit) {
      results = results.slice(0, options.limit);
    }

    return results;
  }

  /**
   * Count documents matching filter
   */
  async count(collection, filter = {}) {
    const results = await this.query(collection, filter);
    return results.length;
  }

  // ==========================================================================
  // INDEX MANAGEMENT
  // ==========================================================================

  /**
   * Update indexes for a document
   */
  async _updateIndexes(collection, doc) {
    const indexStore = this.getStore(`_indexes_${collection}`);

    // Email index
    if (doc.email) {
      await indexStore.set(`email:${doc.email}`, doc.id);
    }

    // Client ID index
    if (doc.clientId) {
      const key = `clientId:${doc.clientId}`;
      const existing = await indexStore.get(key);
      const ids = existing ? JSON.parse(existing) : [];
      if (!ids.includes(doc.id)) {
        ids.push(doc.id);
        await indexStore.set(key, JSON.stringify(ids));
      }
    }

    // Status index
    if (doc.status) {
      const key = `status:${doc.status}`;
      const existing = await indexStore.get(key);
      const ids = existing ? JSON.parse(existing) : [];
      if (!ids.includes(doc.id)) {
        ids.push(doc.id);
        await indexStore.set(key, JSON.stringify(ids));
      }
    }
  }

  /**
   * Remove document from indexes
   */
  async _removeFromIndexes(collection, doc) {
    const indexStore = this.getStore(`_indexes_${collection}`);

    if (doc.email) {
      await indexStore.delete(`email:${doc.email}`);
    }

    if (doc.clientId) {
      const key = `clientId:${doc.clientId}`;
      const existing = await indexStore.get(key);
      if (existing) {
        const ids = JSON.parse(existing);
        const filtered = ids.filter(id => id !== doc.id);
        await indexStore.set(key, JSON.stringify(filtered));
      }
    }

    if (doc.status) {
      const key = `status:${doc.status}`;
      const existing = await indexStore.get(key);
      if (existing) {
        const ids = JSON.parse(existing);
        const filtered = ids.filter(id => id !== doc.id);
        await indexStore.set(key, JSON.stringify(filtered));
      }
    }
  }

  /**
   * Find document by email
   */
  async findByEmail(collection, email) {
    const indexStore = this.getStore(`_indexes_${collection}`);
    const id = await indexStore.get(`email:${email}`);

    if (!id) {
      return null;
    }

    return await this.get(collection, id);
  }

  /**
   * Find documents by client ID
   */
  async findByClientId(collection, clientId) {
    const indexStore = this.getStore(`_indexes_${collection}`);
    const idsJson = await indexStore.get(`clientId:${clientId}`);

    if (!idsJson) {
      return [];
    }

    const ids = JSON.parse(idsJson);
    const docs = await Promise.all(ids.map(id => this.get(collection, id)));

    return docs.filter(Boolean);
  }

  /**
   * Find documents by status
   */
  async findByStatus(collection, status) {
    const indexStore = this.getStore(`_indexes_${collection}`);
    const idsJson = await indexStore.get(`status:${status}`);

    if (!idsJson) {
      return [];
    }

    const ids = JSON.parse(idsJson);
    const docs = await Promise.all(ids.map(id => this.get(collection, id)));

    return docs.filter(Boolean);
  }

  // ==========================================================================
  // ENTITY-SPECIFIC METHODS
  // ==========================================================================

  // --- CLIENTS ---

  async createClient(data) {
    return await this.create('clients', {
      status: 'pending',
      emailNotifications: true,
      ...data
    });
  }

  async getClient(id) {
    return await this.get('clients', id);
  }

  async getClientByEmail(email) {
    return await this.findByEmail('clients', email);
  }

  async updateClient(id, updates) {
    return await this.update('clients', id, updates);
  }

  async listClients(filter = {}) {
    return await this.query('clients', filter, { orderBy: 'createdAt:desc' });
  }

  async getActiveClients() {
    return await this.findByStatus('clients', 'active');
  }

  // --- QUESTIONNAIRES ---

  async createQuestionnaire(data) {
    return await this.create('questionnaires', {
      status: 'pending',
      ...data
    });
  }

  async getQuestionnaire(id) {
    return await this.get('questionnaires', id);
  }

  async updateQuestionnaire(id, updates) {
    return await this.update('questionnaires', id, updates);
  }

  async getPendingQuestionnaires() {
    return await this.findByStatus('questionnaires', 'pending');
  }

  // --- TRAINING PLANS ---

  async createTrainingPlan(data) {
    return await this.create('training_plans', {
      status: 'draft',
      version: 1,
      ...data
    });
  }

  async getTrainingPlan(id) {
    return await this.get('training_plans', id);
  }

  async updateTrainingPlan(id, updates) {
    return await this.update('training_plans', id, updates);
  }

  async getClientTrainingPlans(clientId) {
    return await this.findByClientId('training_plans', clientId);
  }

  async getActiveTrainingPlan(clientId) {
    const plans = await this.query('training_plans', {
      clientId,
      status: 'active'
    }, { orderBy: 'createdAt:desc', limit: 1 });
    return plans[0] || null;
  }

  // --- NUTRITION PLANS ---

  async createNutritionPlan(data) {
    return await this.create('nutrition_plans', {
      status: 'draft',
      version: 1,
      ...data
    });
  }

  async getNutritionPlan(id) {
    return await this.get('nutrition_plans', id);
  }

  async updateNutritionPlan(id, updates) {
    return await this.update('nutrition_plans', id, updates);
  }

  async getClientNutritionPlans(clientId) {
    return await this.findByClientId('nutrition_plans', clientId);
  }

  async getActiveNutritionPlan(clientId) {
    const plans = await this.query('nutrition_plans', {
      clientId,
      status: 'active'
    }, { orderBy: 'createdAt:desc', limit: 1 });
    return plans[0] || null;
  }

  // --- PROGRESS ENTRIES ---

  async createProgressEntry(data) {
    return await this.create('progress_entries', {
      status: 'pending',
      responded: false,
      ...data
    });
  }

  async getProgressEntry(id) {
    return await this.get('progress_entries', id);
  }

  async updateProgressEntry(id, updates) {
    return await this.update('progress_entries', id, updates);
  }

  async getClientProgress(clientId, limit = 10) {
    return await this.query('progress_entries', { clientId }, {
      orderBy: 'createdAt:desc',
      limit
    });
  }

  async getPendingProgressEntries() {
    return await this.findByStatus('progress_entries', 'pending');
  }

  // --- EMAILS ---

  async createEmail(data) {
    return await this.create('emails', {
      status: 'new',
      read: false,
      autoProcessed: false,
      priority: 'normal',
      folder: 'inbox',
      ...data
    });
  }

  async getEmail(id) {
    return await this.get('emails', id);
  }

  async updateEmail(id, updates) {
    return await this.update('emails', id, updates);
  }

  async listEmails(filter = {}) {
    return await this.query('emails', filter, { orderBy: 'createdAt:desc' });
  }

  async getClientEmails(clientId) {
    return await this.findByClientId('emails', clientId);
  }

  async getUnreadEmails() {
    return await this.query('emails', { read: false });
  }

  // --- EMAIL THREADS ---

  async createEmailThread(data) {
    return await this.create('email_threads', {
      status: 'active',
      messageCount: 0,
      messageIds: [],
      ...data
    });
  }

  async getEmailThread(id) {
    return await this.get('email_threads', id);
  }

  async updateEmailThread(id, updates) {
    return await this.update('email_threads', id, updates);
  }

  async addMessageToThread(threadId, messageId) {
    const thread = await this.getEmailThread(threadId);
    if (!thread) {
      throw new Error(`Thread ${threadId} not found`);
    }

    return await this.updateEmailThread(threadId, {
      messageIds: [...thread.messageIds, messageId],
      messageCount: thread.messageCount + 1,
      lastMessageAt: this.now()
    });
  }

  // --- AUTOMATION RULES ---

  async createAutomationRule(data) {
    return await this.create('automation_rules', {
      enabled: true,
      executionCount: 0,
      errorCount: 0,
      ...data
    });
  }

  async getAutomationRule(id) {
    return await this.get('automation_rules', id);
  }

  async updateAutomationRule(id, updates) {
    return await this.update('automation_rules', id, updates);
  }

  async getEnabledAutomationRules() {
    return await this.query('automation_rules', { enabled: true });
  }

  // --- AUTOMATION LOGS ---

  async createAutomationLog(data) {
    return await this.create('automation_logs', data);
  }

  async getAutomationLogs(ruleId, limit = 50) {
    return await this.query('automation_logs', { ruleId }, {
      orderBy: 'createdAt:desc',
      limit
    });
  }

  // --- SCHEDULED TASKS ---

  async createScheduledTask(data) {
    return await this.create('scheduled_tasks', {
      enabled: true,
      runCount: 0,
      errorCount: 0,
      ...data
    });
  }

  async getScheduledTask(id) {
    return await this.get('scheduled_tasks', id);
  }

  async updateScheduledTask(id, updates) {
    return await this.update('scheduled_tasks', id, updates);
  }

  async getDueScheduledTasks() {
    const tasks = await this.query('scheduled_tasks', { enabled: true });
    const now = new Date();

    return tasks.filter(task => {
      if (!task.nextRunAt) return true;
      return new Date(task.nextRunAt) <= now;
    });
  }

  // --- SETTINGS ---

  async getSettings() {
    let settings = await this.get('settings', 'global');

    if (!settings) {
      // Create default settings
      settings = await this.create('settings', {
        id: 'global',
        email: {
          imapEnabled: false,
          checkInterval: 30
        },
        ai: {
          provider: 'gemini',
          model: 'gemini-2.0-flash',
          maxRetries: 3,
          timeout: 30000,
          cacheDuration: 600
        },
        automation: {
          autoProcessEmails: true,
          autoRespondProgress: true,
          autoGeneratePlans: false
        },
        business: {
          name: 'FitCoach Pro',
          timezone: 'Europe/Bratislava',
          currency: 'EUR'
        }
      });
    }

    return settings;
  }

  async updateSettings(updates) {
    const settings = await this.getSettings();
    return await this.update('settings', 'global', {
      ...settings,
      ...updates
    });
  }

  // --- EMAIL TEMPLATES ---

  async createEmailTemplate(data) {
    return await this.create('email_templates', data);
  }

  async getEmailTemplate(id) {
    return await this.get('email_templates', id);
  }

  async updateEmailTemplate(id, updates) {
    return await this.update('email_templates', id, updates);
  }

  async listEmailTemplates() {
    return await this.list('email_templates');
  }
}

// Singleton instance
let dbInstance = null;

/**
 * Get database instance
 */
export function getDatabase() {
  if (!dbInstance) {
    dbInstance = new Database();
  }
  return dbInstance;
}

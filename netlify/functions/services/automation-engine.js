/**
 * Automation Engine
 *
 * Handles:
 * - Workflow execution based on triggers
 * - Action processing (create client, generate plan, send email, etc.)
 * - Event-based automation
 * - Rule evaluation
 */

import { getDatabase } from '../db/database.js';
import nodemailer from 'nodemailer';

export class AutomationEngine {
  constructor() {
    this.db = getDatabase();
    this.actions = this.registerActions();
  }

  /**
   * Register all available actions
   */
  registerActions() {
    return {
      // Client actions
      create_client: this.createClientAction.bind(this),
      update_client: this.updateClientAction.bind(this),
      activate_client: this.activateClientAction.bind(this),

      // Plan generation
      generate_training_plan: this.generateTrainingPlanAction.bind(this),
      generate_nutrition_plan: this.generateNutritionPlanAction.bind(this),
      activate_plan: this.activatePlanAction.bind(this),

      // Email actions
      send_email: this.sendEmailAction.bind(this),
      send_template_email: this.sendTemplateEmailAction.bind(this),

      // Progress actions
      analyze_progress: this.analyzeProgressAction.bind(this),
      generate_progress_response: this.generateProgressResponseAction.bind(this),

      // General actions
      log: this.logAction.bind(this),
      wait: this.waitAction.bind(this),
      webhook: this.webhookAction.bind(this)
    };
  }

  /**
   * Execute automation rule
   */
  async executeRule(rule, triggerData = {}) {
    const startTime = Date.now();
    const log = {
      ruleId: rule.id,
      ruleName: rule.name,
      triggeredBy: triggerData,
      status: 'success',
      actions: [],
      errors: [],
      results: {}
    };

    try {
      console.log(`[Automation] Executing rule: ${rule.name}`);

      // Execute each action in sequence
      for (const actionConfig of rule.actions) {
        try {
          const actionResult = await this.executeAction(actionConfig, {
            ...triggerData,
            previousResults: log.results
          });

          log.actions.push({
            type: actionConfig.type,
            status: 'success',
            result: actionResult
          });

          // Store result for next actions
          log.results[actionConfig.type] = actionResult;

        } catch (error) {
          console.error(`[Automation] Action failed: ${actionConfig.type}`, error);

          log.actions.push({
            type: actionConfig.type,
            status: 'failed',
            error: error.message
          });

          log.errors.push(error.message);
          log.status = 'partial';

          // Stop execution on critical errors
          if (actionConfig.critical !== false) {
            log.status = 'failed';
            break;
          }
        }
      }

      // Update rule execution stats
      await this.db.updateAutomationRule(rule.id, {
        lastExecutedAt: new Date().toISOString(),
        executionCount: (rule.executionCount || 0) + 1,
        errorCount: log.status === 'failed'
          ? (rule.errorCount || 0) + 1
          : rule.errorCount || 0,
        lastError: log.status === 'failed' ? log.errors[0] : null
      });

    } catch (error) {
      console.error(`[Automation] Rule execution failed: ${rule.name}`, error);
      log.status = 'failed';
      log.errors.push(error.message);
    }

    // Calculate duration
    log.duration = Date.now() - startTime;

    // Save log
    await this.db.createAutomationLog(log);

    return log;
  }

  /**
   * Execute a single action
   */
  async executeAction(config, context) {
    const { type, params = {} } = config;

    if (!this.actions[type]) {
      throw new Error(`Unknown action type: ${type}`);
    }

    console.log(`[Automation] Executing action: ${type}`);

    // Resolve template variables in params
    const resolvedParams = this.resolveParams(params, context);

    // Execute action
    return await this.actions[type](resolvedParams, context);
  }

  /**
   * Resolve template variables like {{client.email}}
   */
  resolveParams(params, context) {
    const resolved = {};

    for (const [key, value] of Object.entries(params)) {
      if (typeof value === 'string' && value.includes('{{')) {
        resolved[key] = this.resolveTemplate(value, context);
      } else if (typeof value === 'object' && value !== null) {
        resolved[key] = this.resolveParams(value, context);
      } else {
        resolved[key] = value;
      }
    }

    return resolved;
  }

  /**
   * Resolve template string
   */
  resolveTemplate(template, context) {
    return template.replace(/\{\{([^}]+)\}\}/g, (match, path) => {
      const keys = path.trim().split('.');
      let value = context;

      for (const key of keys) {
        value = value?.[key];
      }

      return value !== undefined ? value : match;
    });
  }

  // ==========================================================================
  // ACTION IMPLEMENTATIONS
  // ==========================================================================

  /**
   * Create client action
   */
  async createClientAction(params, context) {
    const client = await this.db.createClient(params);
    context.client = client;
    return { clientId: client.id, client };
  }

  /**
   * Update client action
   */
  async updateClientAction(params, context) {
    const { clientId, ...updates } = params;
    const id = clientId || context.client?.id;

    if (!id) {
      throw new Error('Client ID required for update_client action');
    }

    const client = await this.db.updateClient(id, updates);
    context.client = client;
    return { clientId: client.id, updated: true };
  }

  /**
   * Activate client action
   */
  async activateClientAction(params, context) {
    const clientId = params.clientId || context.client?.id;

    if (!clientId) {
      throw new Error('Client ID required for activate_client action');
    }

    const client = await this.db.updateClient(clientId, {
      status: 'active',
      onboardedAt: new Date().toISOString()
    });

    return { clientId: client.id, activated: true };
  }

  /**
   * Generate training plan action
   */
  async generateTrainingPlanAction(params, context) {
    const clientId = params.clientId || context.client?.id;

    if (!clientId) {
      throw new Error('Client ID required for generate_training_plan action');
    }

    const client = await this.db.getClient(clientId);
    if (!client) {
      throw new Error(`Client ${clientId} not found`);
    }

    // Call plan generation API
    const response = await fetch(`${process.env.URL}/.netlify/functions/generate_plan`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        client,
        goal: params.goal || client.goal,
        type: 'training_plan',
        constraints: params.constraints
      })
    });

    const result = await response.json();

    if (!result.ok) {
      throw new Error('Failed to generate training plan');
    }

    // Save plan
    const plan = await this.db.createTrainingPlan({
      clientId: client.id,
      name: result.plan.name,
      focus: result.plan.focus,
      durationWeeks: result.plan.durationWeeks,
      startDate: result.plan.startDate,
      days: result.plan.days,
      generatedBy: 'ai',
      aiModel: 'gemini-2.0-flash',
      status: params.activate ? 'active' : 'draft'
    });

    // Update client
    if (params.activate) {
      await this.db.updateClient(clientId, {
        currentTrainingPlanId: plan.id
      });
    }

    context.trainingPlan = plan;
    return { planId: plan.id, plan };
  }

  /**
   * Generate nutrition plan action
   */
  async generateNutritionPlanAction(params, context) {
    const clientId = params.clientId || context.client?.id;

    if (!clientId) {
      throw new Error('Client ID required for generate_nutrition_plan action');
    }

    const client = await this.db.getClient(clientId);
    if (!client) {
      throw new Error(`Client ${clientId} not found`);
    }

    // Call plan generation API
    const response = await fetch(`${process.env.URL}/.netlify/functions/generate_plan`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        client,
        goal: params.goal || client.goal,
        type: 'nutrition_plan',
        constraints: params.constraints
      })
    });

    const result = await response.json();

    if (!result.ok) {
      throw new Error('Failed to generate nutrition plan');
    }

    // Save plan
    const plan = await this.db.createNutritionPlan({
      clientId: client.id,
      name: result.plan.name || 'Nutrition Plan',
      weekLabel: result.plan.weekLabel,
      targets: result.plan.targets,
      days: result.plan.days,
      generatedBy: 'ai',
      aiModel: 'gemini-2.0-flash',
      status: params.activate ? 'active' : 'draft'
    });

    // Update client
    if (params.activate) {
      await this.db.updateClient(clientId, {
        currentNutritionPlanId: plan.id
      });
    }

    context.nutritionPlan = plan;
    return { planId: plan.id, plan };
  }

  /**
   * Activate plan action
   */
  async activatePlanAction(params, context) {
    const { planId, planType } = params;
    const collection = planType === 'training' ? 'training_plans' : 'nutrition_plans';

    const plan = await this.db.get(collection, planId);
    if (!plan) {
      throw new Error(`Plan ${planId} not found`);
    }

    await this.db.update(collection, planId, { status: 'active' });

    // Update client
    const field = planType === 'training'
      ? 'currentTrainingPlanId'
      : 'currentNutritionPlanId';

    await this.db.updateClient(plan.clientId, { [field]: planId });

    return { planId, activated: true };
  }

  /**
   * Send email action
   */
  async sendEmailAction(params, context) {
    const { to, subject, text, html, fromName, replyTo } = params;

    const settings = await this.db.getSettings();
    const smtpConfig = settings.email;

    // Create transporter
    const transporter = nodemailer.createTransport({
      host: smtpConfig.smtpHost || process.env.SMTP_HOST,
      port: smtpConfig.smtpPort || process.env.SMTP_PORT,
      secure: smtpConfig.smtpPort === 465,
      auth: {
        user: smtpConfig.smtpUser || process.env.SMTP_USER,
        pass: smtpConfig.smtpPassword || process.env.SMTP_PASS
      }
    });

    // Send email
    const info = await transporter.sendMail({
      from: fromName
        ? `"${fromName}" <${smtpConfig.smtpUser || process.env.SMTP_USER}>`
        : smtpConfig.smtpUser || process.env.SMTP_USER,
      to,
      replyTo: replyTo || smtpConfig.replyTo,
      subject,
      text,
      html
    });

    return { messageId: info.messageId, sent: true };
  }

  /**
   * Send template email action
   */
  async sendTemplateEmailAction(params, context) {
    const { templateId, to, data } = params;

    // Get template
    const template = await this.db.getEmailTemplate(templateId);
    if (!template) {
      throw new Error(`Email template ${templateId} not found`);
    }

    // Render template
    const subject = this.resolveTemplate(template.subject, { ...context, ...data });
    const text = this.resolveTemplate(template.textContent, { ...context, ...data });
    const html = template.htmlContent
      ? this.resolveTemplate(template.htmlContent, { ...context, ...data })
      : null;

    // Send email
    return await this.sendEmailAction({ to, subject, text, html }, context);
  }

  /**
   * Analyze progress action
   */
  async analyzeProgressAction(params, context) {
    const progressId = params.progressId || context.progressEntry?.id;

    if (!progressId) {
      throw new Error('Progress ID required for analyze_progress action');
    }

    const progress = await this.db.getProgressEntry(progressId);
    if (!progress) {
      throw new Error(`Progress entry ${progressId} not found`);
    }

    // Get client and previous progress
    const client = await this.db.getClient(progress.clientId);
    const previousProgress = await this.db.getClientProgress(progress.clientId, 5);

    // Calculate trends
    const analysis = {
      weightChange: null,
      trend: 'stable',
      complianceAvg: progress.compliance || 0,
      recommendations: []
    };

    if (previousProgress.length > 1) {
      const prev = previousProgress[1]; // Second most recent
      if (progress.weight && prev.weight) {
        analysis.weightChange = progress.weight - prev.weight;
        analysis.trend = analysis.weightChange < -0.5 ? 'decreasing'
          : analysis.weightChange > 0.5 ? 'increasing'
          : 'stable';
      }

      // Calculate average compliance
      const complianceValues = previousProgress
        .filter(p => p.compliance !== null)
        .map(p => p.compliance);

      if (complianceValues.length > 0) {
        analysis.complianceAvg = complianceValues.reduce((a, b) => a + b, 0) / complianceValues.length;
      }
    }

    // Generate recommendations
    if (analysis.complianceAvg < 70) {
      analysis.recommendations.push('Focus on consistency - try to hit your targets at least 80% of the time');
    }

    if (progress.energyLevel && progress.energyLevel < 5) {
      analysis.recommendations.push('Low energy levels detected - consider adjusting carb intake or sleep schedule');
    }

    if (progress.sleepQuality && progress.sleepQuality < 6) {
      analysis.recommendations.push('Improve sleep quality - aim for 7-9 hours per night');
    }

    context.progressAnalysis = analysis;
    return analysis;
  }

  /**
   * Generate progress response action
   */
  async generateProgressResponseAction(params, context) {
    const progressId = params.progressId || context.progressEntry?.id;
    const analysis = context.progressAnalysis;

    if (!progressId) {
      throw new Error('Progress ID required for generate_progress_response action');
    }

    const progress = await this.db.getProgressEntry(progressId);
    const client = await this.db.getClient(progress.clientId);

    // Generate response text
    let response = `Hey ${client.name}!\n\nGreat job checking in! Here's my feedback:\n\n`;

    if (analysis?.weightChange) {
      if (analysis.weightChange < 0) {
        response += `✓ Weight: Down ${Math.abs(analysis.weightChange).toFixed(1)} lbs - excellent progress!\n`;
      } else {
        response += `Weight: Up ${analysis.weightChange.toFixed(1)} lbs - let's review your nutrition.\n`;
      }
    }

    if (progress.compliance) {
      if (progress.compliance >= 80) {
        response += `✓ Compliance: ${progress.compliance}% - fantastic consistency!\n`;
      } else {
        response += `Compliance: ${progress.compliance}% - let's work on hitting your targets more consistently.\n`;
      }
    }

    if (analysis?.recommendations && analysis.recommendations.length > 0) {
      response += `\nRecommendations:\n`;
      analysis.recommendations.forEach(rec => {
        response += `- ${rec}\n`;
      });
    }

    response += `\nKeep up the great work! Let me know if you have any questions.\n\nYour coach`;

    context.progressResponse = response;
    return { response };
  }

  /**
   * Log action
   */
  async logAction(params, context) {
    console.log('[Automation Log]', params.message || params);
    return { logged: true };
  }

  /**
   * Wait action
   */
  async waitAction(params, context) {
    const ms = params.ms || params.seconds * 1000 || 1000;
    await new Promise(resolve => setTimeout(resolve, ms));
    return { waited: ms };
  }

  /**
   * Webhook action
   */
  async webhookAction(params, context) {
    const { url, method = 'POST', data } = params;

    const response = await fetch(url, {
      method,
      headers: { 'Content-Type': 'application/json' },
      body: method !== 'GET' ? JSON.stringify(data || context) : undefined
    });

    const result = await response.json();
    return { status: response.status, result };
  }

  // ==========================================================================
  // TRIGGER EVALUATION
  // ==========================================================================

  /**
   * Evaluate if trigger conditions are met
   */
  evaluateTrigger(rule, event) {
    const { trigger } = rule;

    // Type must match
    if (trigger.type !== event.type) {
      return false;
    }

    // Check conditions
    if (trigger.conditions) {
      return this.evaluateConditions(trigger.conditions, event.data);
    }

    return true;
  }

  /**
   * Evaluate conditions object
   */
  evaluateConditions(conditions, data) {
    return Object.entries(conditions).every(([key, value]) => {
      const dataValue = this.getNestedValue(data, key);

      // Special operators
      if (key.endsWith('_contains')) {
        const field = key.replace('_contains', '');
        const fieldValue = this.getNestedValue(data, field);
        return fieldValue && fieldValue.toLowerCase().includes(value.toLowerCase());
      }

      if (key.endsWith('_gt')) {
        const field = key.replace('_gt', '');
        const fieldValue = this.getNestedValue(data, field);
        return fieldValue > value;
      }

      if (key.endsWith('_lt')) {
        const field = key.replace('_lt', '');
        const fieldValue = this.getNestedValue(data, field);
        return fieldValue < value;
      }

      // Exact match
      return dataValue === value;
    });
  }

  /**
   * Get nested object value by path
   */
  getNestedValue(obj, path) {
    const keys = path.split('.');
    let value = obj;

    for (const key of keys) {
      value = value?.[key];
    }

    return value;
  }

  /**
   * Trigger event
   */
  async triggerEvent(eventType, eventData) {
    console.log(`[Automation] Event triggered: ${eventType}`);

    // Get all enabled rules
    const rules = await this.db.getEnabledAutomationRules();

    // Find matching rules
    const matchingRules = rules.filter(rule =>
      this.evaluateTrigger(rule, { type: eventType, data: eventData })
    );

    console.log(`[Automation] Found ${matchingRules.length} matching rules`);

    // Execute matching rules
    const results = [];
    for (const rule of matchingRules) {
      const result = await this.executeRule(rule, eventData);
      results.push(result);
    }

    return results;
  }
}

/**
 * Get singleton automation engine instance
 */
let engineInstance = null;

export function getAutomationEngine() {
  if (!engineInstance) {
    engineInstance = new AutomationEngine();
  }
  return engineInstance;
}

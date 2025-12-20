/**
 * FitCRM Database Schema
 *
 * This schema supports both NoSQL (Netlify Blobs) and SQL (PostgreSQL) backends
 */

// ============================================================================
// CLIENTS
// ============================================================================
export const ClientSchema = {
  id: 'string (uuid)',
  createdAt: 'timestamp',
  updatedAt: 'timestamp',

  // Personal Info
  name: 'string',
  email: 'string (unique)',
  phone: 'string?',
  age: 'number',
  city: 'string?',

  // Physical Stats
  height: 'string', // e.g., "180cm"
  currentWeight: 'number', // in lbs
  bodyFatPct: 'number?',

  // Goals & Plans
  goal: 'string', // "Weight Loss", "Hypertrophy", "Endurance", "General Fitness"
  motivationLevel: 'string?', // "high", "medium", "low"
  experience: 'string?', // "beginner", "intermediate", "advanced"

  // Status
  status: 'string', // "pending", "active", "paused", "inactive"
  onboardedAt: 'timestamp?',
  lastActivityAt: 'timestamp?',

  // Current Plans
  currentTrainingPlanId: 'string?',
  currentNutritionPlanId: 'string?',

  // Preferences & Constraints
  dietaryRestrictions: 'array<string>?', // ["vegetarian", "gluten-free", etc.]
  injuries: 'array<string>?',
  availableDays: 'array<string>?', // ["mon", "tue", "wed", etc.]
  equipment: 'array<string>?', // ["dumbbells", "barbell", "resistance_bands", etc.]

  // Communication
  preferredLanguage: 'string?', // "en", "sk", etc.
  emailNotifications: 'boolean',

  // Metadata
  source: 'string?', // "email_questionnaire", "manual", "web_form"
  notes: 'string?'
};

// ============================================================================
// QUESTIONNAIRES (Raw submissions from clients)
// ============================================================================
export const QuestionnaireSchema = {
  id: 'string (uuid)',
  createdAt: 'timestamp',
  processedAt: 'timestamp?',

  clientId: 'string?', // Set after processing
  email: 'string',
  emailMessageId: 'string?', // Reference to source email

  // Status
  status: 'string', // "pending", "processing", "processed", "failed"

  // Raw form data
  formData: 'object', // {name, age, weight, goal, etc.}

  // Processing results
  extractedData: 'object?',
  errors: 'array<string>?',

  // Actions taken
  actionsPerformed: 'array<object>?', // [{action: "client_created", id: "..."}, etc.]
};

// ============================================================================
// TRAINING PLANS
// ============================================================================
export const TrainingPlanSchema = {
  id: 'string (uuid)',
  createdAt: 'timestamp',
  updatedAt: 'timestamp',

  clientId: 'string',
  name: 'string',

  // Plan Details
  startDate: 'string', // ISO date
  endDate: 'string?', // ISO date
  durationWeeks: 'number',
  focus: 'string', // "Strength", "Hypertrophy", "Endurance", "Weight Loss"

  // Status
  status: 'string', // "draft", "active", "completed", "archived"

  // Days structure
  days: 'object', // { mon: {...}, tue: {...}, etc. }
  /*
  days: {
    mon: {
      title: "Upper Body",
      isRest: false,
      items: [
        {
          id: "uuid",
          name: "Bench Press",
          sets: 3,
          reps: "8-10",
          rpe: 8,
          notes: "Focus on form"
        }
      ]
    },
    tue: { isRest: true }
  }
  */

  // Generation metadata
  generatedBy: 'string?', // "ai", "manual", "template"
  aiModel: 'string?',
  prompt: 'string?',

  // Versioning
  version: 'number',
  previousVersionId: 'string?'
};

// ============================================================================
// NUTRITION PLANS
// ============================================================================
export const NutritionPlanSchema = {
  id: 'string (uuid)',
  createdAt: 'timestamp',
  updatedAt: 'timestamp',

  clientId: 'string',
  name: 'string',

  // Plan Details
  startDate: 'string', // ISO date
  endDate: 'string?',
  weekLabel: 'string', // "Week 1", "Week 2", etc.

  // Status
  status: 'string', // "draft", "active", "completed", "archived"

  // Daily targets
  targets: 'object',
  /*
  targets: {
    kcal: 2000,
    protein: 150,
    carbs: 200,
    fats: 67,
    waterLiters: 3
  }
  */

  // Meals by day
  days: 'object', // { mon: {...}, tue: {...}, etc. }
  /*
  days: {
    mon: {
      meals: {
        breakfast: [
          {
            id: "uuid",
            name: "Oatmeal with berries",
            desc: "Steel-cut oats, mixed berries, honey",
            kcal: 350,
            protein: 12,
            carbs: 65,
            fats: 8
          }
        ],
        lunch: [...],
        dinner: [...]
      },
      notes: "Drink extra water today"
    }
  }
  */

  // Generation metadata
  generatedBy: 'string?',
  aiModel: 'string?',
  prompt: 'string?',

  // Versioning
  version: 'number',
  previousVersionId: 'string?'
};

// ============================================================================
// PROGRESS ENTRIES (Check-ins from clients)
// ============================================================================
export const ProgressEntrySchema = {
  id: 'string (uuid)',
  createdAt: 'timestamp',

  clientId: 'string',
  emailMessageId: 'string?', // Source email if from email

  // Type of check-in
  type: 'string', // "weekly", "biweekly", "ad_hoc"
  weekNumber: 'number?',

  // Physical measurements
  weight: 'number?', // lbs
  bodyFatPct: 'number?',
  measurements: 'object?', // { waist: 32, chest: 40, etc. }

  // Progress photos
  photoUrls: 'array<string>?',

  // Subjective feedback
  energyLevel: 'number?', // 1-10
  sleepQuality: 'number?', // 1-10
  stressLevel: 'number?', // 1-10
  hunger: 'string?', // "low", "normal", "high"
  compliance: 'number?', // 0-100%

  // Text feedback
  notes: 'string?',
  challenges: 'string?',
  wins: 'string?',

  // Parsed from email
  rawText: 'string?',

  // Response tracking
  responded: 'boolean',
  responseId: 'string?', // ID of email response
  responseAt: 'timestamp?',

  // Processing
  status: 'string', // "pending", "processed", "responded"
  processingNotes: 'string?'
};

// ============================================================================
// EMAILS (Ticket system)
// ============================================================================
export const EmailSchema = {
  id: 'string (uuid)',
  createdAt: 'timestamp',
  updatedAt: 'timestamp',

  // Email metadata
  messageId: 'string?', // IMAP message ID
  inReplyTo: 'string?',
  threadId: 'string?',

  // Sender/Recipient
  from: 'string', // email address
  to: 'string',
  cc: 'array<string>?',

  clientId: 'string?', // Matched client

  // Content
  subject: 'string',
  textContent: 'string',
  htmlContent: 'string?',

  // Attachments
  attachments: 'array<object>?',
  /*
  attachments: [
    {
      filename: "progress.jpg",
      contentType: "image/jpeg",
      size: 123456,
      url: "blob://..."
    }
  ]
  */

  // Classification
  category: 'string?', // "questionnaire", "progress_update", "question", "other"
  priority: 'string', // "high", "normal", "low"

  // Status
  status: 'string', // "new", "assigned", "in_progress", "done"
  read: 'boolean',

  // Processing
  autoProcessed: 'boolean',
  processingResults: 'object?',
  /*
  processingResults: {
    type: "progress_update",
    extractedData: {...},
    actions: [{...}]
  }
  */

  // Source
  source: 'string', // "imap", "smtp_inbound", "manual"

  // Folder/Labels
  folder: 'string' // "inbox", "assigned", "done", "archive"
};

// ============================================================================
// EMAIL THREADS (Conversations)
// ============================================================================
export const EmailThreadSchema = {
  id: 'string (uuid)',
  createdAt: 'timestamp',
  updatedAt: 'timestamp',
  lastMessageAt: 'timestamp',

  clientId: 'string?',
  subject: 'string',

  // Messages in thread
  messageIds: 'array<string>', // IDs of EmailSchema entries
  messageCount: 'number',

  // Status
  status: 'string', // "active", "resolved", "archived"

  // Classification
  category: 'string?'
};

// ============================================================================
// AUTOMATION RULES
// ============================================================================
export const AutomationRuleSchema = {
  id: 'string (uuid)',
  createdAt: 'timestamp',
  updatedAt: 'timestamp',

  name: 'string',
  description: 'string?',

  // Status
  enabled: 'boolean',

  // Trigger
  trigger: 'object',
  /*
  trigger: {
    type: "email_received", // or "schedule", "progress_submitted", "client_created"
    conditions: {
      subject_contains: "questionnaire",
      from_domain: "@gmail.com"
    }
  }
  */

  // Actions
  actions: 'array<object>',
  /*
  actions: [
    {
      type: "parse_questionnaire",
      params: {...}
    },
    {
      type: "create_client",
      params: {...}
    },
    {
      type: "generate_training_plan",
      params: {...}
    },
    {
      type: "send_email",
      params: {
        template: "welcome",
        to: "{{client.email}}"
      }
    }
  ]
  */

  // Execution tracking
  lastExecutedAt: 'timestamp?',
  executionCount: 'number',
  errorCount: 'number',
  lastError: 'string?'
};

// ============================================================================
// AUTOMATION LOGS
// ============================================================================
export const AutomationLogSchema = {
  id: 'string (uuid)',
  createdAt: 'timestamp',

  ruleId: 'string',
  ruleName: 'string',

  triggeredBy: 'object', // { type: "email", id: "...", ... }

  // Execution
  status: 'string', // "success", "partial", "failed"
  duration: 'number', // milliseconds

  // Actions executed
  actions: 'array<object>',
  /*
  actions: [
    {
      type: "parse_questionnaire",
      status: "success",
      result: {...}
    }
  ]
  */

  // Errors
  errors: 'array<string>?',

  // Results
  results: 'object?'
};

// ============================================================================
// EMAIL TEMPLATES
// ============================================================================
export const EmailTemplateSchema = {
  id: 'string',
  name: 'string',
  description: 'string?',

  subject: 'string', // Supports {{variables}}
  textContent: 'string',
  htmlContent: 'string?',

  // Template variables
  variables: 'array<string>', // ["client.name", "plan.name", etc.]

  // Metadata
  category: 'string?', // "welcome", "progress_response", "reminder"

  createdAt: 'timestamp',
  updatedAt: 'timestamp'
};

// ============================================================================
// SCHEDULED TASKS
// ============================================================================
export const ScheduledTaskSchema = {
  id: 'string (uuid)',
  createdAt: 'timestamp',

  name: 'string',
  type: 'string', // "check_emails", "send_reminder", "generate_report"

  // Schedule (cron-like)
  schedule: 'string', // "0 */30 * * * *" (every 30 min), "0 0 9 * * MON" (Mon 9am)

  // Status
  enabled: 'boolean',

  // Execution tracking
  lastRunAt: 'timestamp?',
  nextRunAt: 'timestamp?',
  runCount: 'number',

  // Config
  config: 'object?',

  // Errors
  lastError: 'string?',
  errorCount: 'number'
};

// ============================================================================
// SETTINGS
// ============================================================================
export const SettingsSchema = {
  id: 'string (always "global")',
  updatedAt: 'timestamp',

  // Email settings
  email: 'object',
  /*
  email: {
    imapEnabled: true,
    imapHost: "imap.gmail.com",
    imapPort: 993,
    imapUser: "trainer@example.com",
    imapPassword: "***", // encrypted
    checkInterval: 30, // minutes

    smtpHost: "smtp.gmail.com",
    smtpPort: 587,
    smtpUser: "trainer@example.com",
    smtpPassword: "***",
    fromName: "FitCoach Pro",
    replyTo: "trainer@example.com"
  }
  */

  // AI settings
  ai: 'object',
  /*
  ai: {
    provider: "gemini",
    model: "gemini-2.0-flash",
    apiKey: "***",
    maxRetries: 3,
    timeout: 30000,
    cacheDuration: 600 // seconds
  }
  */

  // Automation settings
  automation: 'object',
  /*
  automation: {
    autoProcessEmails: true,
    autoRespondProgress: true,
    autoGeneratePlans: false // require manual approval
  }
  */

  // Business settings
  business: 'object'
  /*
  business: {
    name: "FitCoach Pro",
    trainerName: "John Doe",
    timezone: "Europe/Bratislava",
    currency: "EUR"
  }
  */
};

// ============================================================================
// INDEXES (for NoSQL storage)
// ============================================================================
export const Indexes = {
  clients: [
    'email',
    'status',
    'createdAt',
    'lastActivityAt'
  ],
  questionnaires: [
    'email',
    'status',
    'clientId',
    'createdAt'
  ],
  trainingPlans: [
    'clientId',
    'status',
    'startDate'
  ],
  nutritionPlans: [
    'clientId',
    'status',
    'startDate'
  ],
  progressEntries: [
    'clientId',
    'createdAt',
    'status',
    'type'
  ],
  emails: [
    'clientId',
    'status',
    'category',
    'messageId',
    'threadId',
    'createdAt',
    'folder'
  ],
  emailThreads: [
    'clientId',
    'status',
    'lastMessageAt'
  ],
  automationRules: [
    'enabled'
  ],
  automationLogs: [
    'ruleId',
    'createdAt',
    'status'
  ],
  scheduledTasks: [
    'enabled',
    'nextRunAt'
  ]
};

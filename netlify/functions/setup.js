/**
 * Setup Function
 *
 * Initialize the database with default:
 * - Automation rules
 * - Email templates
 * - Settings
 * - Sample data (optional)
 */

import { getDatabase } from './db/database.js';

export async function handler(event, context) {
  const db = getDatabase();
  const query = event.queryStringParameters || {};
  const includeSample = query.sample === 'true';

  try {
    const results = {
      automationRules: [],
      emailTemplates: [],
      scheduledTasks: [],
      sampleClients: []
    };

    // ==========================================================================
    // DEFAULT AUTOMATION RULES
    // ==========================================================================

    console.log('[setup] Creating default automation rules...');

    // Rule 1: New Client Onboarding
    const onboardingRule = await db.createAutomationRule({
      name: 'New Client Onboarding',
      description: 'Automatically onboard new clients from questionnaire emails',
      enabled: true,
      trigger: {
        type: 'questionnaire_received',
        conditions: {}
      },
      actions: [
        {
          type: 'activate_client',
          params: {}
        },
        {
          type: 'generate_training_plan',
          params: {
            activate: false // Create as draft for review
          }
        },
        {
          type: 'generate_nutrition_plan',
          params: {
            activate: false
          }
        },
        {
          type: 'send_template_email',
          params: {
            templateId: 'welcome',
            to: '{{client.email}}',
            data: {}
          }
        }
      ]
    });

    results.automationRules.push(onboardingRule);

    // Rule 2: Progress Update Response
    const progressRule = await db.createAutomationRule({
      name: 'Progress Update Auto-Response',
      description: 'Analyze progress and send personalized feedback',
      enabled: true,
      trigger: {
        type: 'progress_submitted',
        conditions: {}
      },
      actions: [
        {
          type: 'analyze_progress',
          params: {}
        },
        {
          type: 'generate_progress_response',
          params: {}
        },
        {
          type: 'send_email',
          params: {
            to: '{{client.email}}',
            subject: 'Your Progress Update - Feedback from Coach',
            text: '{{progressResponse}}'
          }
        }
      ]
    });

    results.automationRules.push(progressRule);

    // Rule 3: Plan Activation
    const planActivationRule = await db.createAutomationRule({
      name: 'Auto-Activate Plans After Review',
      description: 'Automatically activate and send plans to clients',
      enabled: false, // Manual trigger only
      trigger: {
        type: 'plan_approved',
        conditions: {}
      },
      actions: [
        {
          type: 'activate_plan',
          params: {
            planId: '{{planId}}',
            planType: '{{planType}}'
          }
        },
        {
          type: 'send_template_email',
          params: {
            templateId: 'plan_ready',
            to: '{{client.email}}',
            data: {}
          }
        }
      ]
    });

    results.automationRules.push(planActivationRule);

    // ==========================================================================
    // EMAIL TEMPLATES
    // ==========================================================================

    console.log('[setup] Creating email templates...');

    // Template 1: Welcome Email
    const welcomeTemplate = await db.createEmailTemplate({
      id: 'welcome',
      name: 'Welcome New Client',
      description: 'Sent to new clients after questionnaire is processed',
      category: 'welcome',
      subject: 'Welcome to FitCoach Pro! 🎯',
      textContent: `Hi {{client.name}},

Welcome to FitCoach Pro! I'm excited to work with you on your fitness journey.

I've received your questionnaire and I'm currently preparing your personalized training and nutrition plans based on your goals: {{client.goal}}.

Here's what happens next:
1. I'll review and customize your plans (usually within 24 hours)
2. You'll receive your complete training and nutrition program
3. We'll schedule a quick call to go over everything
4. You'll start your transformation!

In the meantime, if you have any questions, just reply to this email.

Let's do this! 💪

Your Coach
FitCoach Pro`,
      htmlContent: `<div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
  <h2>Welcome to FitCoach Pro! 🎯</h2>

  <p>Hi <strong>{{client.name}}</strong>,</p>

  <p>Welcome to FitCoach Pro! I'm excited to work with you on your fitness journey.</p>

  <p>I've received your questionnaire and I'm currently preparing your personalized training and nutrition plans based on your goals: <strong>{{client.goal}}</strong>.</p>

  <h3>What's Next?</h3>
  <ol>
    <li>I'll review and customize your plans (usually within 24 hours)</li>
    <li>You'll receive your complete training and nutrition program</li>
    <li>We'll schedule a quick call to go over everything</li>
    <li>You'll start your transformation!</li>
  </ol>

  <p>In the meantime, if you have any questions, just reply to this email.</p>

  <p><strong>Let's do this! 💪</strong></p>

  <p>Your Coach<br>FitCoach Pro</p>
</div>`,
      variables: ['client.name', 'client.goal']
    });

    results.emailTemplates.push(welcomeTemplate);

    // Template 2: Plan Ready
    const planReadyTemplate = await db.createEmailTemplate({
      id: 'plan_ready',
      name: 'Your Plan is Ready',
      description: 'Sent when training/nutrition plan is activated',
      category: 'plan_ready',
      subject: 'Your Personalized {{planType}} Plan is Ready! 🎉',
      textContent: `Hi {{client.name}},

Great news! Your personalized {{planType}} plan is ready and waiting for you.

I've carefully designed this program based on:
- Your goal: {{client.goal}}
- Your experience level
- Your available equipment and schedule
- Your specific needs and preferences

You can view your plan in the client portal or I can send you a PDF version - just let me know.

Remember:
- Consistency is key
- Don't hesitate to ask questions
- Check in weekly so I can track your progress
- We can adjust the plan anytime based on your feedback

Ready to crush your goals? Let's get started!

Your Coach
FitCoach Pro`,
      htmlContent: `<div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
  <h2>Your Personalized {{planType}} Plan is Ready! 🎉</h2>

  <p>Hi <strong>{{client.name}}</strong>,</p>

  <p>Great news! Your personalized {{planType}} plan is ready and waiting for you.</p>

  <h3>What I've Designed For You:</h3>
  <p>I've carefully created this program based on:</p>
  <ul>
    <li>Your goal: <strong>{{client.goal}}</strong></li>
    <li>Your experience level</li>
    <li>Your available equipment and schedule</li>
    <li>Your specific needs and preferences</li>
  </ul>

  <p>You can view your plan in the client portal or I can send you a PDF version - just let me know.</p>

  <h3>Important Reminders:</h3>
  <ul>
    <li>✓ Consistency is key</li>
    <li>✓ Don't hesitate to ask questions</li>
    <li>✓ Check in weekly so I can track your progress</li>
    <li>✓ We can adjust the plan anytime based on your feedback</li>
  </ul>

  <p><strong>Ready to crush your goals? Let's get started!</strong></p>

  <p>Your Coach<br>FitCoach Pro</p>
</div>`,
      variables: ['client.name', 'client.goal', 'planType']
    });

    results.emailTemplates.push(planReadyTemplate);

    // Template 3: Progress Check-in Reminder
    const checkInTemplate = await db.createEmailTemplate({
      id: 'checkin_reminder',
      name: 'Weekly Check-in Reminder',
      description: 'Reminder to submit weekly progress',
      category: 'reminder',
      subject: 'Time for Your Weekly Check-in! 📊',
      textContent: `Hi {{client.name}},

Hope you're having a great week! It's time for your weekly check-in.

Please send me an update with:
- Current weight
- Energy levels (1-10)
- Sleep quality (1-10)
- Compliance with your plan (%)
- Any challenges or wins this week

This helps me track your progress and make adjustments to keep you moving toward your goal.

Reply to this email or use the check-in form in the client portal.

Keep crushing it! 💪

Your Coach
FitCoach Pro`,
      htmlContent: `<div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
  <h2>Time for Your Weekly Check-in! 📊</h2>

  <p>Hi <strong>{{client.name}}</strong>,</p>

  <p>Hope you're having a great week! It's time for your weekly check-in.</p>

  <h3>Please share:</h3>
  <ul>
    <li>Current weight</li>
    <li>Energy levels (1-10)</li>
    <li>Sleep quality (1-10)</li>
    <li>Compliance with your plan (%)</li>
    <li>Any challenges or wins this week</li>
  </ul>

  <p>This helps me track your progress and make adjustments to keep you moving toward your goal.</p>

  <p>Reply to this email or use the check-in form in the client portal.</p>

  <p><strong>Keep crushing it! 💪</strong></p>

  <p>Your Coach<br>FitCoach Pro</p>
</div>`,
      variables: ['client.name']
    });

    results.emailTemplates.push(checkInTemplate);

    // ==========================================================================
    // SCHEDULED TASKS
    // ==========================================================================

    console.log('[setup] Creating scheduled tasks...');

    // Task 1: Check emails every 30 minutes
    const emailCheckTask = await db.createScheduledTask({
      name: 'Check Emails',
      type: 'check_emails',
      schedule: '0 */30 * * * *', // Every 30 minutes
      enabled: false, // Disabled by default - enable when IMAP configured
      config: {
        mailbox: 'INBOX',
        limit: 50
      }
    });

    results.scheduledTasks.push(emailCheckTask);

    // Task 2: Weekly check-in reminders (Monday 9am)
    const checkinReminderTask = await db.createScheduledTask({
      name: 'Weekly Check-in Reminders',
      type: 'send_checkin_reminders',
      schedule: '0 0 9 * * MON', // Monday 9am
      enabled: true,
      config: {
        templateId: 'checkin_reminder'
      }
    });

    results.scheduledTasks.push(checkinReminderTask);

    // ==========================================================================
    // SAMPLE DATA (Optional)
    // ==========================================================================

    if (includeSample) {
      console.log('[setup] Creating sample data...');

      // Sample client
      const sampleClient = await db.createClient({
        name: 'John Doe',
        email: 'john.doe@example.com',
        phone: '+421 900 123 456',
        age: 32,
        city: 'Bratislava',
        height: '180cm',
        currentWeight: 185,
        bodyFatPct: 22,
        goal: 'Weight Loss',
        experience: 'intermediate',
        status: 'active',
        availableDays: ['mon', 'wed', 'fri'],
        equipment: ['dumbbells', 'barbell', 'bench'],
        dietaryRestrictions: [],
        injuries: [],
        source: 'manual'
      });

      results.sampleClients.push(sampleClient);

      // Sample progress entry
      await db.createProgressEntry({
        clientId: sampleClient.id,
        type: 'weekly',
        weekNumber: 1,
        weight: 183,
        energyLevel: 8,
        sleepQuality: 7,
        compliance: 85,
        notes: 'Feeling great! A bit sore from workouts.',
        status: 'pending'
      });
    }

    // ==========================================================================
    // RESPONSE
    // ==========================================================================

    return {
      statusCode: 200,
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        ok: true,
        message: 'FitCRM initialized successfully',
        created: {
          automationRules: results.automationRules.length,
          emailTemplates: results.emailTemplates.length,
          scheduledTasks: results.scheduledTasks.length,
          sampleClients: results.sampleClients.length
        },
        results
      })
    };

  } catch (error) {
    console.error('[setup] Error:', error);

    return {
      statusCode: 500,
      body: JSON.stringify({
        ok: false,
        error: error.message,
        stack: error.stack
      })
    };
  }
}

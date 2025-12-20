# Frontend Integration Guide

How to integrate the new backend APIs with the existing frontend.

## Overview

The backend is now ready with full automation. The frontend currently uses `localStorage` for data. We need to migrate to using the backend APIs.

## Quick Integration

### 1. Import the Backend API Client

In any frontend file:

```javascript
import backend from './api/backend.js';
```

### 2. Replace localStorage Calls

**Before (localStorage):**
```javascript
// demo/src/store.js
const clients = JSON.parse(localStorage.getItem('fitcrm-data'))?.clients || [];
```

**After (backend API):**
```javascript
import backend from './api/backend.js';

const { clients } = await backend.clients.list();
```

## Migration Strategy

### Phase 1: Dual Mode (Recommended)

Keep localStorage as fallback while testing backend:

```javascript
// demo/src/store.js
import backend from './api/backend.js';

const store = {
  async getClients() {
    try {
      // Try backend first
      const result = await backend.clients.list();
      return result.clients;
    } catch (error) {
      console.warn('Backend unavailable, using localStorage', error);
      // Fallback to localStorage
      const data = JSON.parse(localStorage.getItem('fitcrm-data'));
      return data?.clients || [];
    }
  },

  async addClient(client) {
    try {
      // Save to backend
      await backend.clients.create(client);
      // Also save to localStorage for offline support
      const data = JSON.parse(localStorage.getItem('fitcrm-data')) || {};
      data.clients = [...(data.clients || []), client];
      localStorage.setItem('fitcrm-data', JSON.stringify(data));
    } catch (error) {
      console.error('Failed to save client', error);
      throw error;
    }
  }
};
```

### Phase 2: Backend Only

Once backend is stable, remove localStorage completely:

```javascript
const store = {
  async getClients() {
    const result = await backend.clients.list();
    return result.clients;
  },

  async addClient(client) {
    await backend.clients.create(client);
  }
};
```

## Example Integrations

### 1. Clients Page

**File:** `demo/src/pages/ClientsPage.js`

```javascript
import backend from '../api/backend.js';

async function loadClients() {
  showLoading();

  try {
    const result = await backend.clients.list({ status: 'active' });
    renderClients(result.clients);
  } catch (error) {
    showError('Failed to load clients');
  } finally {
    hideLoading();
  }
}

async function viewClient(clientId) {
  try {
    const result = await backend.clients.get(clientId);
    const { client, trainingPlans, nutritionPlans, progress } = result;

    renderClientDetail(client);
    renderPlans(trainingPlans, nutritionPlans);
    renderProgress(progress);
  } catch (error) {
    showError('Failed to load client details');
  }
}
```

### 2. Mailbox Page

**File:** `demo/src/pages/MailboxPage.js`

Add "Check Emails" button:

```javascript
async function checkNewEmails() {
  const btn = document.getElementById('check-emails-btn');
  btn.disabled = true;
  btn.textContent = 'Checking...';

  try {
    const result = await backend.emails.check();

    showToast(`✅ Processed ${result.processed} new emails`, 'success');

    // Reload inbox
    await loadInbox();
  } catch (error) {
    showToast('❌ Failed to check emails', 'error');
  } finally {
    btn.disabled = false;
    btn.textContent = 'Check New Emails';
  }
}
```

Add button to UI:

```html
<button id="check-emails-btn" onclick="checkNewEmails()">
  Check New Emails
</button>
```

### 3. Training Plan Page

**File:** `demo/src/pages/TrainingPlanPage.js`

Generate plan button:

```javascript
async function generatePlan(clientId) {
  showLoading('Generating training plan with AI...');

  try {
    const clientResult = await backend.clients.get(clientId);
    const client = clientResult.client;

    const result = await backend.plans.generate(client, 'training_plan', {
      availableDays: client.availableDays,
      equipment: client.equipment,
      injuries: client.injuries
    });

    renderPlan(result.plan);
    showToast('✅ Training plan generated!', 'success');
  } catch (error) {
    showToast('❌ Failed to generate plan', 'error');
  } finally {
    hideLoading();
  }
}
```

### 4. Progress Submission (Client Portal)

Create new page: `demo/src/pages/ProgressSubmitPage.js`

```javascript
async function submitProgress(formData) {
  const data = {
    email: formData.get('email'),
    weight: parseFloat(formData.get('weight')),
    energyLevel: parseInt(formData.get('energy')),
    sleepQuality: parseInt(formData.get('sleep')),
    compliance: parseInt(formData.get('compliance')),
    notes: formData.get('notes'),
    challenges: formData.get('challenges'),
    wins: formData.get('wins')
  };

  try {
    const result = await backend.progress.submit(data);

    if (result.automated) {
      showToast('✅ Progress submitted! You\'ll receive feedback via email.', 'success');
    } else {
      showToast('✅ Progress submitted!', 'success');
    }

    // Redirect or reset form
    form.reset();
  } catch (error) {
    showToast('❌ Failed to submit progress', 'error');
  }
}

// Form HTML
const progressForm = `
  <form id="progress-form" onsubmit="submitProgress(new FormData(this)); return false;">
    <h2>Weekly Check-in</h2>

    <label>Email:</label>
    <input type="email" name="email" required>

    <label>Weight (lbs):</label>
    <input type="number" name="weight" step="0.1" required>

    <label>Energy Level (1-10):</label>
    <input type="range" name="energy" min="1" max="10" value="5">

    <label>Sleep Quality (1-10):</label>
    <input type="range" name="sleep" min="1" max="10" value="5">

    <label>Plan Compliance (%):</label>
    <input type="number" name="compliance" min="0" max="100" value="80">

    <label>Notes:</label>
    <textarea name="notes"></textarea>

    <label>Challenges this week:</label>
    <textarea name="challenges"></textarea>

    <label>Wins this week:</label>
    <textarea name="wins"></textarea>

    <button type="submit">Submit Check-in</button>
  </form>
`;
```

## Data Migration

### One-time Migration from localStorage to Backend

```javascript
import backend from './api/backend.js';

async function migrateData() {
  const confirmed = confirm('Migrate localStorage data to backend? This is a one-time operation.');
  if (!confirmed) return;

  try {
    const result = await backend.migrateLocalStorageToBackend();

    alert(`✅ Migration complete!\n- Clients: ${result.clients}\n- Tickets: ${result.tickets}`);

    // Optionally clear localStorage after successful migration
    // localStorage.removeItem('fitcrm-data');
  } catch (error) {
    alert('❌ Migration failed: ' + error.message);
  }
}

// Add migration button to settings
const migrationButton = `
  <button onclick="migrateData()">
    Migrate Data to Backend
  </button>
`;
```

## Error Handling

### Global Error Handler

```javascript
// demo/src/utils/error-handler.js

export function handleApiError(error, context = '') {
  console.error(`[API Error] ${context}:`, error);

  if (error.message.includes('not enabled')) {
    showToast('⚠️ Backend feature not configured. Contact admin.', 'warning');
  } else if (error.message.includes('not found')) {
    showToast('❌ Not found', 'error');
  } else if (error.message.includes('Authentication')) {
    showToast('❌ Authentication failed. Check credentials.', 'error');
  } else {
    showToast(`❌ ${error.message}`, 'error');
  }
}

// Usage
try {
  await backend.clients.list();
} catch (error) {
  handleApiError(error, 'Loading clients');
}
```

## Loading States

### Show Loading Indicator

```javascript
// demo/src/ui/loading.js

export function showLoading(message = 'Loading...') {
  const loader = document.getElementById('global-loader');
  if (loader) {
    loader.textContent = message;
    loader.style.display = 'block';
  }
}

export function hideLoading() {
  const loader = document.getElementById('global-loader');
  if (loader) {
    loader.style.display = 'none';
  }
}

// Add to HTML
const loaderHTML = `
  <div id="global-loader" style="display: none; position: fixed; top: 0; left: 0; right: 0; background: rgba(0,0,0,0.8); color: white; padding: 20px; text-align: center; z-index: 9999;">
    Loading...
  </div>
`;
```

## Testing

### Test Each Integration

```javascript
// demo/src/tests/backend-integration.test.js

async function testBackendIntegration() {
  console.log('🧪 Testing backend integration...');

  try {
    // Test 1: Health check
    console.log('Test 1: Health check');
    const health = await backend.system.health();
    console.assert(health.ok === true, 'Health check failed');
    console.log('✅ Health check passed');

    // Test 2: List clients
    console.log('Test 2: List clients');
    const clients = await backend.clients.list();
    console.assert(Array.isArray(clients.clients), 'Clients not array');
    console.log(`✅ Loaded ${clients.clients.length} clients`);

    // Test 3: Create client
    console.log('Test 3: Create client');
    const newClient = await backend.clients.create({
      name: 'Test Client',
      email: `test-${Date.now()}@example.com`,
      age: 25,
      goal: 'Weight Loss'
    });
    console.assert(newClient.ok === true, 'Create client failed');
    console.log('✅ Client created');

    console.log('🎉 All tests passed!');
  } catch (error) {
    console.error('❌ Test failed:', error);
  }
}

// Run tests
testBackendIntegration();
```

## Progressive Enhancement

Keep the app working even if backend is unavailable:

```javascript
// demo/src/store.js

class Store {
  constructor() {
    this.useBackend = true;
    this.checkBackend();
  }

  async checkBackend() {
    try {
      await backend.system.health();
      this.useBackend = true;
      console.log('✅ Backend available');
    } catch (error) {
      this.useBackend = false;
      console.warn('⚠️ Backend unavailable, using localStorage');
    }
  }

  async getClients() {
    if (this.useBackend) {
      try {
        const result = await backend.clients.list();
        return result.clients;
      } catch (error) {
        console.warn('Backend call failed, falling back to localStorage');
        this.useBackend = false;
      }
    }

    // Fallback to localStorage
    const data = JSON.parse(localStorage.getItem('fitcrm-data'));
    return data?.clients || [];
  }
}

export const store = new Store();
```

## Next Steps

1. **Update Store Layer** - Replace localStorage with backend calls
2. **Add Loading States** - Show spinners during API calls
3. **Error Handling** - Display user-friendly error messages
4. **Add New Features** - Use new backend capabilities (email automation, progress tracking)
5. **Test Thoroughly** - Test each page with backend integration
6. **Deploy** - Push to production and test end-to-end

## Recommended Order

1. ✅ Setup backend (done)
2. ✅ Test APIs with curl (done)
3. 🔄 Update Clients page (high priority)
4. 🔄 Update Mailbox page (high priority)
5. 🔄 Add Progress submission page (new feature)
6. 🔄 Update Training/Nutrition plan pages
7. 🔄 Test automation workflows
8. 🔄 Remove localStorage (when ready)

---

**Questions?** Check [BACKEND_DOCUMENTATION.md](./BACKEND_DOCUMENTATION.md) for detailed API docs.

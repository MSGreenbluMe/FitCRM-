import { store } from "../store.js";
import { showToast } from "../ui/toast.js";
import { t } from "../i18n.js";

function escapeHtml(s) {
  return String(s ?? "")
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#039;");
}

export class SettingsPage {
  constructor() {
    this.el = null;
    this.unsub = null;
    this.activeTab = 'profile';
    this.settings = this.loadSettings();
    // Remember the language at mount so we can reload the app when it changes.
    this.initialLang = this.settings?.profile?.language || 'en';
  }

  loadSettings() {
    // Load from localStorage
    const saved = localStorage.getItem('fitcrm-settings');
    return saved ? JSON.parse(saved) : this.getDefaultSettings();
  }

  getDefaultSettings() {
    return {
      profile: {
        name: 'Alex Trainer',
        email: 'alex@fitcoach.pro',
        phone: '+421 900 123 456',
        avatar: '', // base64 or URL
        bio: 'Certified fitness coach with passion for helping clients reach their goals.',
        certifications: 'NASM CPT, Precision Nutrition L1',
        yearsExperience: '5',
        specialties: 'Weight Loss, Strength Training, Nutrition',
        timezone: 'Europe/Bratislava',
        language: 'en'
      },
      email: {
        imapEnabled: false,
        imapHost: 'imap.gmail.com',
        imapPort: '993',
        imapUser: '',
        imapPassword: '',
        smtpHost: 'smtp.gmail.com',
        smtpPort: '587',
        smtpUser: '',
        smtpPassword: '',
        fromName: 'FitCoach Pro',
        replyTo: '',
        checkInterval: '30'
      },
      ai: {
        provider: 'gemini',
        model: 'gemini-2.5-flash',
        geminiApiKey: '',
        maxRetries: '3',
        timeout: '30000',
        cacheDuration: '600'
      },
      automation: {
        autoProcessEmails: true,
        autoRespondProgress: true,
        autoGeneratePlans: false,
        sendWeeklyReminders: true,
        requirePlanApproval: true
      },
      business: {
        businessName: 'FitCoach Pro',
        currency: 'EUR',
        sessionPrice: '50',
        planPrice: '120',
        nutritionPrice: '80',
        taxRate: '20'
      }
    };
  }

  async saveSettings() {
    try {
      // Save to localStorage
      localStorage.setItem('fitcrm-settings', JSON.stringify(this.settings));

      // Trigger UI update (update user name in header/sidebar)
      window.dispatchEvent(new CustomEvent('settings-updated', {
        detail: this.settings
      }));

      showToast({
        title: t('settings.toastSuccessTitle'),
        message: t('settings.toastSaved'),
        variant: 'success'
      });

      // If the UI language changed, reload so every page re-renders translated.
      const newLang = this.settings?.profile?.language || 'en';
      if (newLang !== this.initialLang) {
        setTimeout(() => window.location.reload(), 300);
      }
    } catch (error) {
      console.error('Failed to save settings:', error);
      showToast({
        title: t('settings.toastErrorTitle'),
        message: t('settings.toastSaveFailed'),
        variant: 'danger'
      });
    }
  }

  handleAvatarUpload(e) {
    const file = e.target.files[0];
    if (!file) return;

    // Validate file type
    if (!file.type.startsWith('image/')) {
      showToast({
        title: t('settings.toastErrorTitle'),
        message: t('settings.toastPickImage'),
        variant: 'danger'
      });
      return;
    }

    // Validate file size (max 2MB)
    if (file.size > 2 * 1024 * 1024) {
      showToast({
        title: t('settings.toastErrorTitle'),
        message: t('settings.toastImageTooLarge'),
        variant: 'danger'
      });
      return;
    }

    // Read as base64
    const reader = new FileReader();
    reader.onload = (event) => {
      this.settings.profile.avatar = event.target.result;
      this.render();
      this.attachEventListeners();

      showToast({
        title: t('settings.toastSuccessTitle'),
        message: t('settings.toastAvatarUploaded'),
        variant: 'success'
      });
    };
    reader.readAsDataURL(file);
  }

  mount(container) {
    this.el = document.createElement("div");
    this.el.className = "h-full overflow-y-auto p-6 lg:p-10";
    container.appendChild(this.el);

    this.render();
    this.attachEventListeners();
  }

  unmount() {
    if (this.el) {
      this.el.remove();
    }
  }

  render() {
    this.el.innerHTML = `
      <div class="max-w-[1200px] mx-auto flex flex-col gap-6">
        <!-- Header -->
        <div class="flex items-center justify-between">
          <div>
            <h1 class="text-white text-3xl lg:text-4xl font-extrabold">${t('settings.title')}</h1>
            <p class="text-gray-400 mt-2">${t('settings.subtitle')}</p>
          </div>
          <button id="save-settings-btn" class="flex items-center gap-2 px-6 py-3 bg-primary hover:bg-primary/90 text-white font-bold rounded-lg transition-colors">
            <span class="material-symbols-outlined">save</span>
            ${t('settings.save')}
          </button>
        </div>

        <!-- Tabs -->
        <div class="border-b border-gray-700">
          <nav class="flex gap-6">
            ${this.renderTab('profile', 'person', t('settings.tabProfile'))}
            ${this.renderTab('email', 'mail', t('settings.tabEmail'))}
            ${this.renderTab('ai', 'psychology', t('settings.tabAi'))}
            ${this.renderTab('automation', 'automation', t('settings.tabAutomation'))}
            ${this.renderTab('business', 'business', t('settings.tabBusiness'))}
          </nav>
        </div>

        <!-- Tab Content -->
        <div class="bg-gray-800/50 rounded-xl p-6 border border-gray-700">
          ${this.renderTabContent()}
        </div>
      </div>
    `;
  }

  renderTab(id, icon, label) {
    const isActive = this.activeTab === id;
    return `
      <button
        data-tab="${id}"
        class="tab-btn flex items-center gap-2 py-3 px-1 border-b-2 transition-colors ${
          isActive
            ? 'border-primary text-primary'
            : 'border-transparent text-gray-400 hover:text-white'
        }"
      >
        <span class="material-symbols-outlined text-xl">${icon}</span>
        <span class="font-semibold">${label}</span>
      </button>
    `;
  }

  renderTabContent() {
    switch (this.activeTab) {
      case 'profile':
        return this.renderProfileTab();
      case 'email':
        return this.renderEmailTab();
      case 'ai':
        return this.renderAITab();
      case 'automation':
        return this.renderAutomationTab();
      case 'business':
        return this.renderBusinessTab();
      default:
        return '';
    }
  }

  renderProfileTab() {
    const { profile } = this.settings;
    const avatarUrl = profile.avatar || '';

    return `
      <div class="flex flex-col gap-6">
        <!-- Avatar Upload -->
        <div class="flex items-center gap-6">
          <div class="relative">
            <div class="h-24 w-24 rounded-full bg-gray-700 border-2 border-gray-600 flex items-center justify-center overflow-hidden">
              ${avatarUrl
                ? `<img src="${escapeHtml(avatarUrl)}" alt="Avatar" class="w-full h-full object-cover" />`
                : `<span class="material-symbols-outlined text-4xl text-gray-400">person</span>`
              }
            </div>
            <label class="absolute bottom-0 right-0 bg-primary hover:bg-primary/90 rounded-full p-2 cursor-pointer transition-colors">
              <span class="material-symbols-outlined text-white text-sm">photo_camera</span>
              <input type="file" id="avatar-upload" accept="image/*" class="hidden" />
            </label>
          </div>
          <div>
            <h3 class="text-white font-semibold mb-1">${t('settings.profilePhoto')}</h3>
            <p class="text-sm text-gray-400">${t('settings.photoHint')}</p>
          </div>
        </div>

        <div>
          <h3 class="text-white text-xl font-bold mb-4">${t('settings.personalInfo')}</h3>
          <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
            ${this.renderInput('profile.name', t('settings.fieldName'), profile.name, 'text', 'person')}
            ${this.renderInput('profile.email', t('settings.fieldEmail'), profile.email, 'email', 'mail')}
            ${this.renderInput('profile.phone', t('settings.fieldPhone'), profile.phone, 'tel', 'phone')}
            ${this.renderInput('profile.yearsExperience', t('settings.fieldYears'), profile.yearsExperience, 'number', 'workspace_premium')}
          </div>
        </div>

        <div>
          <h3 class="text-white text-lg font-semibold mb-3">${t('settings.aboutMe')}</h3>
          ${this.renderTextarea('profile.bio', t('settings.fieldBio'), profile.bio, t('settings.bioPlaceholder'))}
        </div>

        <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
          ${this.renderInput('profile.certifications', t('settings.fieldCertifications'), profile.certifications, 'text', 'verified')}
          ${this.renderInput('profile.specialties', t('settings.fieldSpecialties'), profile.specialties, 'text', 'fitness_center')}
        </div>

        <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
          ${this.renderSelect('profile.timezone', t('settings.fieldTimezone'), profile.timezone, [
            { value: 'Europe/Bratislava', label: 'Europe/Bratislava (CET)' },
            { value: 'Europe/Prague', label: 'Europe/Prague (CET)' },
            { value: 'UTC', label: 'UTC' }
          ], 'schedule')}
          ${this.renderSelect('profile.language', t('settings.fieldLanguage'), profile.language, [
            { value: 'en', label: 'English' },
            { value: 'sk', label: 'Slovenčina' },
            { value: 'cs', label: 'Čeština' }
          ], 'language')}
        </div>
      </div>
    `;
  }

  renderEmailTab() {
    const { email } = this.settings;
    return `
      <div class="flex flex-col gap-6">
        <div class="bg-blue-900/30 border border-blue-600/30 rounded-lg p-4">
          <div class="flex items-start gap-3">
            <span class="material-symbols-outlined text-blue-400">info</span>
            <div class="text-sm text-gray-300">
              <p class="font-semibold text-white mb-1">${t('settings.emailHowTitle')}</p>
              <p>${t('settings.emailHowBody')}</p>
            </div>
          </div>
        </div>

        <!-- Enable Toggle -->
        <div class="flex items-center justify-between p-4 bg-gray-700/50 rounded-lg">
          <div class="flex items-center gap-3">
            <span class="material-symbols-outlined text-2xl text-primary">mail</span>
            <div>
              <h4 class="text-white font-semibold">${t('settings.emailEnableTitle')}</h4>
              <p class="text-sm text-gray-400">${t('settings.emailEnableDesc')}</p>
            </div>
          </div>
          ${this.renderToggle('email.imapEnabled', email.imapEnabled)}
        </div>

        ${email.imapEnabled ? `
          <div>
            <h3 class="text-white text-lg font-semibold mb-3 flex items-center gap-2">
              <span class="material-symbols-outlined">download</span>
              ${t('settings.imapSettings')}
            </h3>
            <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
              ${this.renderInput('email.imapHost', t('settings.fieldImapServer'), email.imapHost, 'text', 'dns')}
              ${this.renderInput('email.imapPort', t('settings.fieldPort'), email.imapPort, 'number', 'router')}
              ${this.renderInput('email.imapUser', t('settings.fieldEmailUser'), email.imapUser, 'email', 'person')}
              ${this.renderInput('email.imapPassword', t('settings.fieldPassword'), email.imapPassword, 'password', 'key')}
            </div>
          </div>

          <div>
            <h3 class="text-white text-lg font-semibold mb-3 flex items-center gap-2">
              <span class="material-symbols-outlined">upload</span>
              ${t('settings.smtpSettings')}
            </h3>
            <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
              ${this.renderInput('email.smtpHost', t('settings.fieldSmtpServer'), email.smtpHost, 'text', 'dns')}
              ${this.renderInput('email.smtpPort', t('settings.fieldPort'), email.smtpPort, 'number', 'router')}
              ${this.renderInput('email.smtpUser', t('settings.fieldEmailUser'), email.smtpUser, 'email', 'person')}
              ${this.renderInput('email.smtpPassword', t('settings.fieldPassword'), email.smtpPassword, 'password', 'key')}
            </div>
          </div>

          <div class="bg-amber-900/30 border border-amber-600/30 rounded-lg p-4">
            <div class="flex items-start gap-3">
              <span class="material-symbols-outlined text-amber-400">help</span>
              <div class="text-sm text-gray-300">
                <p class="font-semibold text-white mb-2">${t('settings.gmailSetupTitle')}</p>
                <ol class="list-decimal list-inside space-y-1">
                  <li>${t('settings.gmailStep1')}</li>
                  <li>${t('settings.gmailStep2')}</li>
                  <li>${t('settings.gmailStep3')}</li>
                  <li>${t('settings.gmailStep4')}</li>
                </ol>
              </div>
            </div>
          </div>
        ` : `
          <div class="text-center py-8 text-gray-400">
            <span class="material-symbols-outlined text-6xl mb-4 opacity-20">mail_off</span>
            <p>${t('settings.emailDisabled')}</p>
          </div>
        `}
      </div>
    `;
  }

  renderAITab() {
    const { ai } = this.settings;
    return `
      <div class="flex flex-col gap-6">
        <div>
          <h3 class="text-white text-xl font-bold mb-4 flex items-center gap-2">
            <span class="material-symbols-outlined">psychology</span>
            ${t('settings.aiConfig')}
          </h3>
          <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
            ${this.renderSelect('ai.provider', t('settings.fieldProvider'), ai.provider, [
              { value: 'gemini', label: 'Google Gemini' }
            ], 'cloud')}
            ${this.renderSelect('ai.model', t('settings.fieldModel'), ai.model, [
              { value: 'gemini-2.5-flash', label: t('settings.modelFlash') },
              { value: 'gemini-2.5-flash-lite', label: 'Gemini 2.5 Flash Lite' },
              { value: 'gemini-3-flash', label: 'Gemini 3 Flash' }
            ], 'model_training')}
          </div>
        </div>

        <div>
          <h3 class="text-white text-lg font-semibold mb-3">${t('settings.apiKeyHeading')}</h3>
          ${this.renderInput('ai.geminiApiKey', 'Gemini API Key', ai.geminiApiKey, 'password', 'key', t('settings.apiKeyPlaceholder'))}
        </div>

        <div>
          <h3 class="text-white text-lg font-semibold mb-3">${t('settings.advancedSettings')}</h3>
          <div class="grid grid-cols-1 md:grid-cols-3 gap-4">
            ${this.renderInput('ai.maxRetries', t('settings.fieldMaxRetries'), ai.maxRetries, 'number', 'replay')}
            ${this.renderInput('ai.timeout', t('settings.fieldTimeout'), ai.timeout, 'number', 'timer')}
            ${this.renderInput('ai.cacheDuration', t('settings.fieldCacheDuration'), ai.cacheDuration, 'number', 'cached')}
          </div>
        </div>

        <div class="bg-green-900/30 border border-green-600/30 rounded-lg p-4">
          <div class="flex items-start gap-3">
            <span class="material-symbols-outlined text-green-400">lightbulb</span>
            <div class="text-sm text-gray-300">
              <p class="font-semibold text-white mb-1">${t('settings.aiTipTitle')}</p>
              <p>${t('settings.aiTipBody')}</p>
            </div>
          </div>
        </div>
      </div>
    `;
  }

  renderAutomationTab() {
    const { automation } = this.settings;
    return `
      <div class="flex flex-col gap-4">
        <div>
          <h3 class="text-white text-xl font-bold mb-4 flex items-center gap-2">
            <span class="material-symbols-outlined">automation</span>
            ${t('settings.automationRules')}
          </h3>
          <p class="text-gray-400 text-sm mb-6">${t('settings.automationSubtitle')}</p>
        </div>

        ${this.renderToggleOption(
          'automation.autoProcessEmails',
          automation.autoProcessEmails,
          t('settings.autoProcessTitle'),
          t('settings.autoProcessDesc'),
          'mail'
        )}

        ${this.renderToggleOption(
          'automation.autoRespondProgress',
          automation.autoRespondProgress,
          t('settings.autoRespondTitle'),
          t('settings.autoRespondDesc'),
          'auto_awesome'
        )}

        ${this.renderToggleOption(
          'automation.autoGeneratePlans',
          automation.autoGeneratePlans,
          t('settings.autoGenerateTitle'),
          t('settings.autoGenerateDesc'),
          'fitness_center'
        )}

        ${this.renderToggleOption(
          'automation.requirePlanApproval',
          automation.requirePlanApproval,
          t('settings.requireApprovalTitle'),
          t('settings.requireApprovalDesc'),
          'approval'
        )}

        ${this.renderToggleOption(
          'automation.sendWeeklyReminders',
          automation.sendWeeklyReminders,
          t('settings.weeklyRemindersTitle'),
          t('settings.weeklyRemindersDesc'),
          'notifications_active'
        )}
      </div>
    `;
  }

  renderBusinessTab() {
    const { business } = this.settings;
    return `
      <div class="flex flex-col gap-6">
        <div>
          <h3 class="text-white text-xl font-bold mb-4 flex items-center gap-2">
            <span class="material-symbols-outlined">business</span>
            ${t('settings.businessInfo')}
          </h3>
          <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
            ${this.renderInput('business.businessName', t('settings.fieldBusinessName'), business.businessName, 'text', 'storefront')}
            ${this.renderSelect('business.currency', t('settings.fieldCurrency'), business.currency, [
              { value: 'EUR', label: 'EUR (€)' },
              { value: 'USD', label: 'USD ($)' },
              { value: 'CZK', label: 'CZK (Kč)' }
            ], 'euro')}
          </div>
        </div>

        <div>
          <h3 class="text-white text-lg font-semibold mb-3">${t('settings.pricing')}</h3>
          <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
            ${this.renderInput('business.sessionPrice', t('settings.fieldSessionPrice'), business.sessionPrice, 'number', 'payments', '€')}
            ${this.renderInput('business.planPrice', t('settings.fieldPlanPrice'), business.planPrice, 'number', 'payments', '€')}
            ${this.renderInput('business.nutritionPrice', t('settings.fieldNutritionPrice'), business.nutritionPrice, 'number', 'payments', '€')}
            ${this.renderInput('business.taxRate', t('settings.fieldTaxRate'), business.taxRate, 'number', 'percent', '%')}
          </div>
        </div>
      </div>
    `;
  }

  renderInput(name, label, value, type = 'text', icon = '', placeholder = '') {
    return `
      <div>
        <label class="block text-sm font-medium text-gray-300 mb-2">
          ${label}
        </label>
        <div class="relative">
          ${icon ? `<span class="material-symbols-outlined absolute left-3 top-1/2 -translate-y-1/2 text-gray-400 text-xl">${icon}</span>` : ''}
          <input
            type="${type}"
            name="${name}"
            value="${escapeHtml(value || '')}"
            placeholder="${escapeHtml(placeholder || label)}"
            class="w-full bg-gray-900 border border-gray-600 rounded-lg px-4 py-2.5 ${icon ? 'pl-11' : ''} text-white placeholder-gray-500 focus:outline-none focus:border-primary focus:ring-1 focus:ring-primary transition-colors"
          />
        </div>
      </div>
    `;
  }

  renderTextarea(name, label, value, placeholder = '') {
    return `
      <div>
        <label class="block text-sm font-medium text-gray-300 mb-2">
          ${label}
        </label>
        <textarea
          name="${name}"
          rows="4"
          placeholder="${placeholder || label}"
          class="w-full bg-gray-900 border border-gray-600 rounded-lg px-4 py-2.5 text-white placeholder-gray-500 focus:outline-none focus:border-primary focus:ring-1 focus:ring-primary transition-colors resize-none"
        >${escapeHtml(value || '')}</textarea>
      </div>
    `;
  }

  renderSelect(name, label, value, options, icon = '') {
    return `
      <div>
        <label class="block text-sm font-medium text-gray-300 mb-2">
          ${label}
        </label>
        <div class="relative">
          ${icon ? `<span class="material-symbols-outlined absolute left-3 top-1/2 -translate-y-1/2 text-gray-400 text-xl">${icon}</span>` : ''}
          <select
            name="${name}"
            class="w-full bg-gray-900 border border-gray-600 rounded-lg px-4 py-2.5 ${icon ? 'pl-11' : ''} pr-10 text-white focus:outline-none focus:border-primary focus:ring-1 focus:ring-primary transition-colors appearance-none"
          >
            ${options.map(opt => `
              <option value="${opt.value}" ${value === opt.value ? 'selected' : ''}>
                ${opt.label}
              </option>
            `).join('')}
          </select>
          <span class="material-symbols-outlined absolute right-3 top-1/2 -translate-y-1/2 text-gray-400 pointer-events-none">expand_more</span>
        </div>
      </div>
    `;
  }

  renderToggle(name, checked) {
    return `
      <label class="relative inline-flex items-center cursor-pointer">
        <input type="checkbox" name="${name}" class="sr-only peer" ${checked ? 'checked' : ''}>
        <div class="w-11 h-6 bg-gray-600 peer-focus:outline-none peer-focus:ring-2 peer-focus:ring-primary rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-primary"></div>
      </label>
    `;
  }

  renderToggleOption(name, checked, title, description, icon) {
    return `
      <div class="flex items-center justify-between p-4 bg-gray-700/50 rounded-lg border border-gray-600 hover:border-gray-500 transition-colors">
        <div class="flex items-start gap-3 flex-1">
          <span class="material-symbols-outlined text-2xl ${checked ? 'text-primary' : 'text-gray-500'}">${icon}</span>
          <div>
            <h4 class="text-white font-semibold mb-1">${title}</h4>
            <p class="text-sm text-gray-400">${description}</p>
          </div>
        </div>
        ${this.renderToggle(name, checked)}
      </div>
    `;
  }

  attachEventListeners() {
    // Tab switching
    this.el.querySelectorAll('.tab-btn').forEach(btn => {
      btn.addEventListener('click', (e) => {
        this.activeTab = e.currentTarget.dataset.tab;
        this.render();
        this.attachEventListeners();
      });
    });

    // Save button
    const saveBtn = this.el.querySelector('#save-settings-btn');
    if (saveBtn) {
      saveBtn.addEventListener('click', () => this.handleSave());
    }

    // Avatar upload
    const avatarInput = this.el.querySelector('#avatar-upload');
    if (avatarInput) {
      avatarInput.addEventListener('change', (e) => this.handleAvatarUpload(e));
    }

    // Form inputs - update settings on change
    this.el.querySelectorAll('input, select, textarea').forEach(input => {
      if (input.id === 'avatar-upload') return; // Skip avatar input
      input.addEventListener('change', (e) => this.handleInputChange(e));
    });
  }

  handleInputChange(e) {
    const { name, value, type, checked } = e.target;
    const [section, key] = name.split('.');

    if (type === 'checkbox') {
      this.settings[section][key] = checked;
    } else {
      this.settings[section][key] = value;
    }
  }

  handleSave() {
    this.saveSettings();
  }
}

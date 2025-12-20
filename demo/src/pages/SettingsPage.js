import { store } from "../store.js";
import { showToast } from "../ui/toast.js";

export class SettingsPage {
  constructor() {
    this.el = null;
    this.unsub = null;
    this.activeTab = 'profile';
    this.settings = this.loadSettings();
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
        language: 'sk'
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
        model: 'gemini-2.0-flash',
        apiKey: '',
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
        title: 'Úspech',
        message: 'Nastavenia boli uložené',
        variant: 'success'
      });
    } catch (error) {
      console.error('Failed to save settings:', error);
      showToast({
        title: 'Chyba',
        message: 'Nepodarilo sa uložiť nastavenia',
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
        title: 'Chyba',
        message: 'Vyber obrázok (JPG, PNG, atď.)',
        variant: 'danger'
      });
      return;
    }

    // Validate file size (max 2MB)
    if (file.size > 2 * 1024 * 1024) {
      showToast({
        title: 'Chyba',
        message: 'Obrázok je príliš veľký (max 2MB)',
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
        title: 'Úspech',
        message: 'Profilová fotka nahraná',
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
            <h1 class="text-white text-3xl lg:text-4xl font-extrabold">Nastavenia</h1>
            <p class="text-gray-400 mt-2">Spravuj svoj profil a konfiguráciu systému</p>
          </div>
          <button id="save-settings-btn" class="flex items-center gap-2 px-6 py-3 bg-primary hover:bg-primary/90 text-white font-bold rounded-lg transition-colors">
            <span class="material-symbols-outlined">save</span>
            Uložiť
          </button>
        </div>

        <!-- Tabs -->
        <div class="border-b border-gray-700">
          <nav class="flex gap-6">
            ${this.renderTab('profile', 'person', 'Profil')}
            ${this.renderTab('email', 'mail', 'Email')}
            ${this.renderTab('ai', 'psychology', 'AI Nastavenia')}
            ${this.renderTab('automation', 'automation', 'Automatizácia')}
            ${this.renderTab('business', 'business', 'Business')}
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
                ? `<img src="${avatarUrl}" alt="Avatar" class="w-full h-full object-cover" />`
                : `<span class="material-symbols-outlined text-4xl text-gray-400">person</span>`
              }
            </div>
            <label class="absolute bottom-0 right-0 bg-primary hover:bg-primary/90 rounded-full p-2 cursor-pointer transition-colors">
              <span class="material-symbols-outlined text-white text-sm">photo_camera</span>
              <input type="file" id="avatar-upload" accept="image/*" class="hidden" />
            </label>
          </div>
          <div>
            <h3 class="text-white font-semibold mb-1">Profilová fotka</h3>
            <p class="text-sm text-gray-400">JPG, PNG alebo GIF. Max 2MB.</p>
          </div>
        </div>

        <div>
          <h3 class="text-white text-xl font-bold mb-4">Osobné informácie</h3>
          <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
            ${this.renderInput('profile.name', 'Meno a priezvisko', profile.name, 'text', 'person')}
            ${this.renderInput('profile.email', 'Email', profile.email, 'email', 'mail')}
            ${this.renderInput('profile.phone', 'Telefón', profile.phone, 'tel', 'phone')}
            ${this.renderInput('profile.yearsExperience', 'Roky praxe', profile.yearsExperience, 'number', 'workspace_premium')}
          </div>
        </div>

        <div>
          <h3 class="text-white text-lg font-semibold mb-3">O mne</h3>
          ${this.renderTextarea('profile.bio', 'Bio / Popis', profile.bio, 'Popíš svoju skúsenosť a špecializáciu...')}
        </div>

        <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
          ${this.renderInput('profile.certifications', 'Certifikácie', profile.certifications, 'text', 'verified')}
          ${this.renderInput('profile.specialties', 'Špecializácie', profile.specialties, 'text', 'fitness_center')}
        </div>

        <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
          ${this.renderSelect('profile.timezone', 'Časové pásmo', profile.timezone, [
            { value: 'Europe/Bratislava', label: 'Europe/Bratislava (CET)' },
            { value: 'Europe/Prague', label: 'Europe/Prague (CET)' },
            { value: 'UTC', label: 'UTC' }
          ], 'schedule')}
          ${this.renderSelect('profile.language', 'Jazyk', profile.language, [
            { value: 'sk', label: 'Slovenčina' },
            { value: 'cs', label: 'Čeština' },
            { value: 'en', label: 'English' }
          ], 'language')}
        </div>
      </div>
    `;
  }

  renderEmailTab() {
    const { email } = this.settings;
    return `
      <div class="flex flex-col gap-6">
        <!-- Enable Toggle -->
        <div class="flex items-center justify-between p-4 bg-gray-700/50 rounded-lg">
          <div class="flex items-center gap-3">
            <span class="material-symbols-outlined text-2xl text-primary">mail</span>
            <div>
              <h4 class="text-white font-semibold">Povoliť email automatizáciu</h4>
              <p class="text-sm text-gray-400">Automatické sťahovanie a spracovanie emailov</p>
            </div>
          </div>
          ${this.renderToggle('email.imapEnabled', email.imapEnabled)}
        </div>

        ${email.imapEnabled ? `
          <div>
            <h3 class="text-white text-lg font-semibold mb-3 flex items-center gap-2">
              <span class="material-symbols-outlined">download</span>
              IMAP Nastavenia (Príjem emailov)
            </h3>
            <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
              ${this.renderInput('email.imapHost', 'IMAP Server', email.imapHost, 'text', 'dns')}
              ${this.renderInput('email.imapPort', 'Port', email.imapPort, 'number', 'router')}
              ${this.renderInput('email.imapUser', 'Email / Používateľ', email.imapUser, 'email', 'person')}
              ${this.renderInput('email.imapPassword', 'Heslo / App Password', email.imapPassword, 'password', 'key')}
            </div>
          </div>

          <div>
            <h3 class="text-white text-lg font-semibold mb-3 flex items-center gap-2">
              <span class="material-symbols-outlined">upload</span>
              SMTP Nastavenia (Posielanie emailov)
            </h3>
            <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
              ${this.renderInput('email.smtpHost', 'SMTP Server', email.smtpHost, 'text', 'dns')}
              ${this.renderInput('email.smtpPort', 'Port', email.smtpPort, 'number', 'router')}
              ${this.renderInput('email.smtpUser', 'Email / Používateľ', email.smtpUser, 'email', 'person')}
              ${this.renderInput('email.smtpPassword', 'Heslo / App Password', email.smtpPassword, 'password', 'key')}
            </div>
          </div>

          <div class="bg-amber-900/30 border border-amber-600/30 rounded-lg p-4">
            <div class="flex items-start gap-3">
              <span class="material-symbols-outlined text-amber-400">help</span>
              <div class="text-sm text-gray-300">
                <p class="font-semibold text-white mb-2">Gmail Setup:</p>
                <ol class="list-decimal list-inside space-y-1">
                  <li>Zapni 2-Factor Authentication</li>
                  <li>Choď do Security → 2-Step Verification → App passwords</li>
                  <li>Vytvor nový App password pre "Mail"</li>
                  <li>Použi tento 16-znakový kód namiesto bežného hesla</li>
                </ol>
              </div>
            </div>
          </div>
        ` : `
          <div class="text-center py-8 text-gray-400">
            <span class="material-symbols-outlined text-6xl mb-4 opacity-20">mail_off</span>
            <p>Email automatizácia je vypnutá</p>
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
            AI Konfigurácia
          </h3>
          <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
            ${this.renderSelect('ai.provider', 'Provider', ai.provider, [
              { value: 'gemini', label: 'Google Gemini' }
            ], 'cloud')}
            ${this.renderSelect('ai.model', 'Model', ai.model, [
              { value: 'gemini-2.0-flash', label: 'Gemini 2.0 Flash' },
              { value: 'gemini-1.5-pro', label: 'Gemini 1.5 Pro' }
            ], 'model_training')}
          </div>
        </div>

        <div>
          <h3 class="text-white text-lg font-semibold mb-3">API Kľúč</h3>
          ${this.renderInput('ai.apiKey', 'Gemini API Key', ai.apiKey, 'password', 'key', 'Získaj na https://aistudio.google.com/app/apikey')}
        </div>

        <div>
          <h3 class="text-white text-lg font-semibold mb-3">Pokročilé nastavenia</h3>
          <div class="grid grid-cols-1 md:grid-cols-3 gap-4">
            ${this.renderInput('ai.maxRetries', 'Max. počet pokusov', ai.maxRetries, 'number', 'replay')}
            ${this.renderInput('ai.timeout', 'Timeout (ms)', ai.timeout, 'number', 'timer')}
            ${this.renderInput('ai.cacheDuration', 'Cache trvanie (s)', ai.cacheDuration, 'number', 'cached')}
          </div>
        </div>

        <div class="bg-green-900/30 border border-green-600/30 rounded-lg p-4">
          <div class="flex items-start gap-3">
            <span class="material-symbols-outlined text-green-400">lightbulb</span>
            <div class="text-sm text-gray-300">
              <p class="font-semibold text-white mb-1">Tip:</p>
              <p>Gemini 2.0 Flash je najrýchlejší a najlacnejší. Pre komplexnejšie plány použi Gemini 1.5 Pro.</p>
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
            Automatizačné pravidlá
          </h3>
          <p class="text-gray-400 text-sm mb-6">Nastav, čo sa má vykonávať automaticky</p>
        </div>

        ${this.renderToggleOption(
          'automation.autoProcessEmails',
          automation.autoProcessEmails,
          'Automaticky spracovať emaily',
          'Rozpozná dotazníky a progress updaty, vytvorí klientov',
          'mail'
        )}

        ${this.renderToggleOption(
          'automation.autoRespondProgress',
          automation.autoRespondProgress,
          'Automatická odpoveď na progress',
          'Analyzuje pokrok a pošle personalizovaný feedback klientovi',
          'auto_awesome'
        )}

        ${this.renderToggleOption(
          'automation.autoGeneratePlans',
          automation.autoGeneratePlans,
          'Automaticky generovať plány',
          'Vygeneruje tréningové a nutričné plány po onboardingu (bez schválenia)',
          'fitness_center'
        )}

        ${this.renderToggleOption(
          'automation.requirePlanApproval',
          automation.requirePlanApproval,
          'Vyžadovať schválenie plánov',
          'Plány sa vytvoria ako draft a čakajú na tvoje schválenie',
          'approval'
        )}

        ${this.renderToggleOption(
          'automation.sendWeeklyReminders',
          automation.sendWeeklyReminders,
          'Týždenné pripomienky check-inu',
          'Pošle email klientom každý pondelok ráno',
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
            Business informácie
          </h3>
          <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
            ${this.renderInput('business.businessName', 'Názov biznisu', business.businessName, 'text', 'storefront')}
            ${this.renderSelect('business.currency', 'Mena', business.currency, [
              { value: 'EUR', label: 'EUR (€)' },
              { value: 'USD', label: 'USD ($)' },
              { value: 'CZK', label: 'CZK (Kč)' }
            ], 'euro')}
          </div>
        </div>

        <div>
          <h3 class="text-white text-lg font-semibold mb-3">Cenník</h3>
          <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
            ${this.renderInput('business.sessionPrice', 'Cena za tréning', business.sessionPrice, 'number', 'payments', '€')}
            ${this.renderInput('business.planPrice', 'Cena za tréningový plán', business.planPrice, 'number', 'payments', '€')}
            ${this.renderInput('business.nutritionPrice', 'Cena za nutričný plán', business.nutritionPrice, 'number', 'payments', '€')}
            ${this.renderInput('business.taxRate', 'Daňová sadzba (%)', business.taxRate, 'number', 'percent', '%')}
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
            value="${value || ''}"
            placeholder="${placeholder || label}"
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
        >${value || ''}</textarea>
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

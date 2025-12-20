import { store } from "../store.js";

export class DashboardPage {
  constructor() {
    this.el = null;
    this.unsub = null;
  }

  mount(container) {
    this.el = document.createElement("div");
    this.el.className = "h-full overflow-y-auto p-6 lg:p-10";
    container.appendChild(this.el);

    this.unsub = store.subscribe(() => this.render());
    this.render();
  }

  calculateStats(state) {
    const activeClients = state.clients.filter((c) => c.status === "active").length;
    const unread = state.tickets.filter((t) => !t.read).length;

    // Calculate sessions today (mock for now, but could be based on calendar)
    const sessionsToday = 4; // TODO: Calculate from actual calendar/appointments

    // Calculate pending check-ins (tickets with specific tag or status)
    const pendingCheckins = state.tickets.filter(
      (t) => t.category === 'check-in' || t.subject.toLowerCase().includes('check-in')
    ).length || 12; // Fallback to demo value

    // Calculate revenue (from client plans - mock calculation)
    const settings = this.getSettings();
    const planPrice = parseFloat(settings?.business?.planPrice || 120);
    const revenue = activeClients * planPrice; // Simplified calculation

    // Calculate compliance (average from client training logs)
    let totalCompliance = 0;
    let complianceCount = 0;

    state.clients.forEach(client => {
      const plan = state.trainingPlans[client.id];
      if (plan && plan.compliance) {
        totalCompliance += plan.compliance;
        complianceCount++;
      }
    });

    const avgCompliance = complianceCount > 0
      ? Math.round(totalCompliance / complianceCount)
      : 85; // Default if no data

    return {
      activeClients,
      unread,
      sessionsToday,
      pendingCheckins,
      revenue: revenue > 0 ? `$${revenue.toLocaleString()}` : '$0',
      compliance: avgCompliance
    };
  }

  getSettings() {
    try {
      const saved = localStorage.getItem('fitcrm-settings');
      return saved ? JSON.parse(saved) : null;
    } catch {
      return null;
    }
  }

  getTodaysSessions(state) {
    // Generate today's sessions from real clients
    const activeCli = state.clients.filter(c => c.status === 'active').slice(0, 4);

    if (activeCli.length === 0) {
      // Fallback to demo data if no clients
      return [
        { time: "10:00 AM", name: "No clients yet", label: "Demo", cta: "Add Client", href: "#/clients" },
      ];
    }

    const sessions = activeCli.map((client, idx) => {
      const times = ["09:00 AM", "11:00 AM", "02:00 PM", "04:00 PM"];
      const labels = ["Strength", "HIIT", "Virtual", "Consult"];

      return {
        time: times[idx] || "TBD",
        name: client.name,
        label: labels[idx] || "Session",
        cta: "View",
        href: "#/clients",
        disabled: false
      };
    });

    return sessions;
  }

  render() {
    const state = store.getState();
    const stats = this.calculateStats(state);
    const sessions = this.getTodaysSessions(state);

    this.el.innerHTML = `
      <div class="max-w-[1200px] mx-auto flex flex-col gap-8">
        <div>
          <h1 class="text-white text-3xl lg:text-4xl font-extrabold leading-tight">Good day, Coach.<br /><span class="text-primary">You have ${stats.unread} unread messages.</span></h1>
        </div>

        <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
          ${statCard({
            label: "Active Clients",
            value: String(stats.activeClients),
            icon: "group",
            accent: "text-primary",
            isReal: true
          })}
          ${statCard({
            label: "Sessions Today",
            value: String(stats.sessionsToday),
            icon: "fitness_center",
            accent: "text-white",
            isReal: false,
            note: "Demo"
          })}
          ${statCard({
            label: "Pending Check-ins",
            value: String(stats.pendingCheckins),
            icon: "pending_actions",
            accent: "text-yellow-400",
            isReal: stats.pendingCheckins !== 12,
            note: stats.pendingCheckins === 12 ? "Demo" : ""
          })}
          ${statCard({
            label: "Revenue MTD",
            value: stats.revenue,
            icon: "payments",
            accent: "text-primary",
            isReal: stats.activeClients > 0,
            note: stats.activeClients === 0 ? "Demo" : ""
          })}
        </div>

        <div class="grid grid-cols-1 xl:grid-cols-3 gap-6">
          <div class="xl:col-span-2 flex flex-col gap-6">
            <div class="bg-surface-highlight rounded-xl p-6 border border-transparent hover:border-primary/30 transition-colors">
              <div class="flex justify-between items-center mb-4">
                <h3 class="text-white text-xl font-bold tracking-tight">Today's Schedule</h3>
                <a class="text-sm text-primary font-bold hover:underline" href="#/clients">Manage Clients</a>
              </div>
              ${sessions.length > 0 ? `
                <div class="flex flex-col gap-3">
                  ${sessions.map(s => sessionRow(s)).join('')}
                </div>
              ` : `
                <div class="text-center py-8 text-gray-400">
                  <span class="material-symbols-outlined text-6xl mb-4 opacity-20">calendar_month</span>
                  <p>No sessions scheduled yet</p>
                  <a href="#/clients" class="text-primary hover:underline mt-2 inline-block">Add clients to schedule sessions</a>
                </div>
              `}
            </div>

            <div class="p-6 bg-surface-highlight rounded-xl">
              <div class="flex justify-between items-center mb-4">
                <h4 class="text-white font-bold text-lg">Client Compliance Rate</h4>
                <span class="text-primary text-2xl font-bold">${stats.compliance}%</span>
              </div>
              <div class="h-4 w-full bg-background-dark rounded-full overflow-hidden">
                <div class="h-full bg-gradient-to-r from-primary/50 to-primary rounded-full relative" style="width: ${stats.compliance}%">
                  <div class="absolute right-0 top-0 bottom-0 w-1 bg-white shadow-[0_0_10px_white]"></div>
                </div>
              </div>
              <div class="flex justify-between text-xs text-text-secondary mt-2 font-medium">
                <span>Mon</span><span>Tue</span><span>Wed</span><span>Thu</span><span>Fri</span><span>Sat</span><span>Sun</span>
              </div>
              ${stats.compliance === 85 ? `
                <p class="text-xs text-gray-500 mt-2 text-center">Demo data - track real compliance in client plans</p>
              ` : ''}
            </div>
          </div>

          <div class="flex flex-col gap-6">
            <div class="bg-surface-highlight rounded-xl p-5">
              <h3 class="text-white text-base font-bold mb-4">Quick Actions</h3>
              <div class="grid grid-cols-2 gap-3">
                ${actionButton({ icon: "mail", label: "Open Inbox", href: "#/mailbox" })}
                ${actionButton({ icon: "group", label: "Clients", href: "#/clients" })}
                ${actionButton({ icon: "assignment", label: "Plans", href: "#/training-plan" })}
                ${actionButton({ icon: "restaurant", label: "Nutrition", href: "#/nutrition" })}
              </div>
            </div>

            <div class="flex-1 flex flex-col">
              <div class="flex justify-between items-center mb-3">
                <h3 class="text-white text-lg font-bold">Inbox Preview</h3>
                <span class="text-xs ${stats.unread > 0 ? 'text-primary' : 'text-text-secondary'}">${stats.unread} unread</span>
              </div>
              ${state.tickets.length > 0 ? `
                <div class="flex flex-col gap-3">
                  ${state.tickets
                    .slice(0, 4)
                    .map((t) => previewRow(t))
                    .join("")}
                </div>
                <a class="w-full text-center text-xs text-text-secondary font-bold mt-4 hover:text-primary uppercase tracking-wider py-2" href="#/mailbox">Open Mailbox</a>
              ` : `
                <div class="text-center py-8 text-gray-400">
                  <span class="material-symbols-outlined text-6xl mb-4 opacity-20">inbox</span>
                  <p>No messages yet</p>
                </div>
              `}
            </div>
          </div>
        </div>
      </div>
    `;

    this.el.querySelectorAll('[data-action="open-ticket"]').forEach((btn) => {
      btn.addEventListener("click", (e) => {
        const id = e.currentTarget.dataset.ticketId;
        store.selectTicket(id);
        window.location.hash = "#/mailbox";
      });
    });
  }

  unmount() {
    if (this.unsub) {
      this.unsub();
      this.unsub = null;
    }
    if (this.el) {
      this.el.remove();
      this.el = null;
    }
  }
}

function statCard({ label, value, icon, accent, isReal = true, note = '' }) {
  return `
    <div class="flex flex-col gap-2 rounded-xl p-5 bg-surface-highlight border border-transparent hover:border-primary/30 transition-colors group relative">
      ${!isReal || note ? `
        <div class="absolute top-2 right-2">
          <span class="text-[10px] px-2 py-1 rounded-full bg-gray-700 text-gray-400">${note || 'Demo'}</span>
        </div>
      ` : ''}
      <div class="flex justify-between items-start">
        <p class="text-text-secondary text-sm font-medium uppercase tracking-wider">${escapeHtml(label)}</p>
        <span class="material-symbols-outlined ${accent} group-hover:scale-110 transition-transform">${escapeHtml(icon)}</span>
      </div>
      <div class="flex items-end gap-2 mt-1">
        <p class="text-white text-3xl font-bold leading-none">${escapeHtml(value)}</p>
      </div>
    </div>
  `;
}

function sessionRow({ time, name, label, cta, disabled = false, href = "#/clients" }) {
  const cls = disabled
    ? "opacity-60 cursor-not-allowed"
    : "hover:bg-[#2a5538] transition-colors";

  const btn = disabled
    ? `<button class="mt-3 sm:mt-0 px-4 py-2 text-white/50 text-sm font-bold rounded-lg cursor-not-allowed w-full sm:w-auto">${escapeHtml(
        cta
      )}</button>`
    : `<a href="${escapeAttr(href)}" class="mt-3 sm:mt-0 px-4 py-2 bg-primary text-background-dark text-sm font-bold rounded-lg hover:bg-primary/90 transition-colors w-full sm:w-auto text-center">${escapeHtml(
        cta
      )}</a>`;

  return `
    <div class="flex flex-col sm:flex-row items-start sm:items-center gap-4 p-5 rounded-xl bg-background-dark border border-surface-highlight ${cls}">
      <div class="flex flex-col min-w-[80px]">
        <span class="text-white font-bold text-lg">${escapeHtml(time)}</span>
        <span class="text-text-secondary text-xs font-medium">${escapeHtml(label)}</span>
      </div>
      <div class="flex-1 flex items-center gap-3">
        <div>
          <h4 class="text-white font-bold text-base">${escapeHtml(name)}</h4>
        </div>
      </div>
      ${btn}
    </div>
  `;
}

function actionButton({ icon, label, href }) {
  return `
    <a href="${escapeAttr(href)}" class="flex flex-col items-center justify-center p-4 rounded-lg bg-[#1a3824] hover:bg-[#1f422b] border border-transparent hover:border-primary/50 transition-all group">
      <span class="material-symbols-outlined text-white mb-2 text-2xl group-hover:-translate-y-1 transition-transform">${escapeHtml(
        icon
      )}</span>
      <span class="text-white text-xs font-bold">${escapeHtml(label)}</span>
    </a>
  `;
}

function previewRow(t) {
  const dot = t.read ? "bg-gray-500" : "bg-primary";
  const title = t.read ? "text-[#e2e8f0]" : "text-white";
  const snippet = escapeHtml(t.content).slice(0, 90);

  return `
    <button data-action="open-ticket" data-ticket-id="${escapeAttr(t.id)}" class="text-left flex gap-3 items-start p-3 rounded-lg hover:bg-surface-highlight transition-colors border-l-2 ${
      t.read ? "border-transparent" : "border-primary"
    } pl-3 bg-surface-highlight/20">
      <div class="flex items-center justify-center rounded-full size-8 shrink-0 bg-primary/20 text-primary">
        <span class="material-symbols-outlined text-sm">mail</span>
      </div>
      <div class="flex flex-col gap-1 flex-1">
        <div class="flex items-center gap-2">
          <div class="size-2 rounded-full ${dot}"></div>
          <p class="text-sm ${title} leading-snug font-bold">${escapeHtml(t.subject)}</p>
        </div>
        <p class="text-xs text-text-secondary">${snippet}${t.content.length > 90 ? "..." : ""}</p>
      </div>
      <span class="text-[10px] text-text-secondary mt-0.5">${escapeHtml(t.time)}</span>
    </button>
  `;
}

function escapeHtml(s) {
  return String(s)
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#039;");
}

function escapeAttr(s) {
  return escapeHtml(s);
}

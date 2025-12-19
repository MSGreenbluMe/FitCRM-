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

  render() {
    const state = store.getState();
    const activeClients = state.clients.filter((c) => c.status === "active").length;
    const unread = state.tickets.filter((t) => !t.read).length;

    this.el.innerHTML = `
      <div class="max-w-[1200px] mx-auto flex flex-col gap-8">
        <div>
          <h1 class="text-white text-3xl lg:text-4xl font-extrabold leading-tight">Good day, Coach.<br /><span class="text-primary">You have ${unread} unread messages.</span></h1>
        </div>

        <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
          ${statCard({ label: "Active Clients", value: String(activeClients), icon: "group", accent: "text-primary" })}
          ${statCard({ label: "Sessions Today", value: "4", icon: "fitness_center", accent: "text-white" })}
          ${statCard({ label: "Pending Check-ins", value: "12", icon: "pending_actions", accent: "text-yellow-400" })}
          ${statCard({ label: "Revenue MTD", value: "$3,240", icon: "payments", accent: "text-primary" })}
        </div>

        <div class="grid grid-cols-1 xl:grid-cols-3 gap-6">
          <div class="xl:col-span-2 flex flex-col gap-6">
            <div class="bg-surface-highlight rounded-xl p-6 border border-transparent hover:border-primary/30 transition-colors">
              <div class="flex justify-between items-center mb-4">
                <h3 class="text-white text-xl font-bold tracking-tight">Today's Schedule</h3>
                <a class="text-sm text-primary font-bold hover:underline" href="#/clients">View Clients</a>
              </div>
              <div class="flex flex-col gap-3">
                ${sessionRow({ time: "10:00 AM", name: "Sarah Jenkins", label: "HIIT", cta: "Start" })}
                ${sessionRow({ time: "11:30 AM", name: "Mike Ross", label: "Virtual", cta: "Join" })}
                ${sessionRow({ time: "02:00 PM", name: "Alex Rivera", label: "Strength", cta: "Upcoming", disabled: true })}
                ${sessionRow({ time: "04:00 PM", name: "New Consult", label: "Discovery", cta: "Open" })}
              </div>
            </div>

            <div class="p-6 bg-surface-highlight rounded-xl">
              <div class="flex justify-between items-center mb-4">
                <h4 class="text-white font-bold text-lg">Client Compliance Rate</h4>
                <span class="text-primary text-2xl font-bold">92%</span>
              </div>
              <div class="h-4 w-full bg-background-dark rounded-full overflow-hidden">
                <div class="h-full bg-gradient-to-r from-primary/50 to-primary w-[92%] rounded-full relative">
                  <div class="absolute right-0 top-0 bottom-0 w-1 bg-white shadow-[0_0_10px_white]"></div>
                </div>
              </div>
              <div class="flex justify-between text-xs text-text-secondary mt-2 font-medium">
                <span>Mon</span><span>Tue</span><span>Wed</span><span>Thu</span><span>Fri</span><span>Sat</span><span>Sun</span>
              </div>
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
                <span class="text-xs text-text-secondary">Demo</span>
              </div>
              <div class="flex flex-col gap-3">
                ${state.tickets
                  .slice(0, 4)
                  .map((t) => previewRow(t))
                  .join("")}
              </div>
              <a class="w-full text-center text-xs text-text-secondary font-bold mt-4 hover:text-primary uppercase tracking-wider py-2" href="#/mailbox">Open Mailbox</a>
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

function statCard({ label, value, icon, accent }) {
  return `
    <div class="flex flex-col gap-2 rounded-xl p-5 bg-surface-highlight border border-transparent hover:border-primary/30 transition-colors group">
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

function sessionRow({ time, name, label, cta, disabled = false }) {
  const cls = disabled
    ? "opacity-60 cursor-not-allowed"
    : "hover:bg-[#2a5538] transition-colors";

  const btn = disabled
    ? `<button class="mt-3 sm:mt-0 px-4 py-2 text-white/50 text-sm font-bold rounded-lg cursor-not-allowed w-full sm:w-auto">${escapeHtml(
        cta
      )}</button>`
    : `<button class="mt-3 sm:mt-0 px-4 py-2 bg-primary text-background-dark text-sm font-bold rounded-lg hover:bg-primary/90 transition-colors w-full sm:w-auto">${escapeHtml(
        cta
      )}</button>`;

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

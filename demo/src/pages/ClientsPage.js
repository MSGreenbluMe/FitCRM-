import { store } from "../store.js";

export class ClientsPage {
  constructor() {
    this.el = null;
    this.unsub = null;
    this.filter = "all";
  }

  mount(container) {
    this.el = document.createElement("div");
    this.el.className = "h-full flex overflow-hidden";
    container.appendChild(this.el);

    this.unsub = store.subscribe(() => this.render());
    this.render();
  }

  render() {
    const state = store.getState();
    const ui = state.ui;
    const selected = state.clients.find((c) => c.id === ui.selectedClientId) || state.clients[0];

    const visibleClients = state.clients.filter((c) => {
      if (this.filter === "active") return c.status === "active";
      if (this.filter === "pending") return c.status === "pending";
      return true;
    });

    this.el.innerHTML = `
      <div class="w-[400px] flex flex-col bg-surface-darker border-r border-surface-highlight">
        <div class="p-4 pb-2 flex flex-col gap-4">
          <div class="relative">
            <div class="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
              <span class="material-symbols-outlined text-text-secondary">search</span>
            </div>
            <input data-role="search" class="block w-full pl-10 pr-3 py-2.5 border-none rounded-lg bg-surface-highlight text-white placeholder-text-secondary focus:ring-1 focus:ring-primary text-sm" placeholder="Search clients..." type="text"/>
          </div>

          <div class="flex gap-2 overflow-x-auto pb-2">
            ${chip({ id: "all", label: "All Clients", active: this.filter === "all" })}
            ${chip({
              id: "active",
              label: `Active (${state.clients.filter((c) => c.status === "active").length})`,
              active: this.filter === "active",
            })}
            ${chip({
              id: "pending",
              label: `Pending (${state.clients.filter((c) => c.status === "pending").length})`,
              active: this.filter === "pending",
            })}
          </div>
        </div>

        <div class="flex-1 overflow-y-auto" data-role="client-list">
          ${visibleClients
            .map((c) => clientRow({ client: c, selected: selected && c.id === selected.id }))
            .join("")}
        </div>
      </div>

      <div class="flex-1 flex flex-col bg-background-dark overflow-y-auto">
        ${selected ? clientDetails(selected) : emptyState()}
      </div>
    `;

    this.el.querySelectorAll('[data-action="select-client"]').forEach((row) => {
      row.addEventListener("click", (e) => {
        const id = e.currentTarget.dataset.clientId;
        store.selectClient(id);
      });
    });

    this.el.querySelectorAll('[data-action="set-filter"]').forEach((btn) => {
      btn.addEventListener("click", (e) => {
        this.filter = e.currentTarget.dataset.filterId;
        this.render();
      });
    });

    const searchInput = this.el.querySelector('[data-role="search"]');
    if (searchInput) {
      searchInput.addEventListener("input", () => {
        const q = searchInput.value.trim().toLowerCase();
        const list = this.el.querySelector('[data-role="client-list"]');
        list.querySelectorAll('[data-action="select-client"]').forEach((row) => {
          const hay = (row.dataset.searchHay || "").toLowerCase();
          row.style.display = q === "" || hay.includes(q) ? "" : "none";
        });
      });
    }

    this.el.querySelectorAll('[data-action="open-mailbox"]').forEach((btn) => {
      btn.addEventListener("click", () => {
        window.location.hash = "#/mailbox";
      });
    });

    this.el.querySelectorAll('[data-action="open-training"]').forEach((btn) => {
      btn.addEventListener("click", () => {
        window.location.hash = "#/training-plan";
      });
    });

    this.el.querySelectorAll('[data-action="open-nutrition"]').forEach((btn) => {
      btn.addEventListener("click", () => {
        window.location.hash = "#/nutrition";
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

function chip({ id, label, active }) {
  const cls = active
    ? "bg-primary text-background-dark text-xs font-bold"
    : "bg-surface-highlight border border-transparent hover:border-text-secondary text-text-secondary hover:text-white text-xs font-medium";

  return `
    <button data-action="set-filter" data-filter-id="${escapeAttr(id)}" class="whitespace-nowrap px-4 py-1.5 rounded-full ${cls}">
      ${escapeHtml(label)}
    </button>
  `;
}

function clientRow({ client, selected }) {
  const cls = selected
    ? "bg-surface-highlight/50 border-l-4 border-primary"
    : "border-l-4 border-transparent hover:bg-surface-highlight/50";

  const dot = client.status === "active" ? "bg-primary" : "bg-yellow-500";

  return `
    <div data-action="select-client" data-client-id="${escapeAttr(client.id)}" data-search-hay="${escapeAttr(
      `${client.name} ${client.email} ${client.goal} ${client.plan}`
    )}" class="flex items-center gap-3 px-4 py-3 ${cls} cursor-pointer transition-colors border-b border-surface-highlight/50">
      <div class="size-12 rounded-full bg-surface-highlight flex items-center justify-center flex-shrink-0">
        <span class="material-symbols-outlined text-white">person</span>
      </div>
      <div class="flex flex-col flex-1 min-w-0">
        <div class="flex justify-between items-center mb-0.5">
          <p class="text-white text-sm font-bold truncate">${escapeHtml(client.name)}</p>
          <span class="size-2 rounded-full ${dot}"></span>
        </div>
        <p class="text-text-secondary text-xs truncate">Goal: ${escapeHtml(client.goal)} • Last seen ${escapeHtml(
          client.lastSeen
        )}</p>
      </div>
    </div>
  `;
}

function clientDetails(client) {
  return `
    <div class="bg-surface-darker border-b border-surface-highlight px-8 py-6">
      <div class="flex items-start justify-between">
        <div class="flex gap-6">
          <div class="size-24 rounded-2xl bg-surface-highlight border-2 border-primary/20 flex items-center justify-center">
            <span class="material-symbols-outlined text-white text-5xl">person</span>
          </div>
          <div class="flex flex-col justify-center">
            <div class="flex items-center gap-3 mb-1">
              <h2 class="text-2xl font-bold text-white">${escapeHtml(client.name)}</h2>
              <span class="px-2 py-0.5 rounded text-xs font-bold bg-primary/20 text-primary border border-primary/30">${escapeHtml(
                client.status
              )}</span>
            </div>
            <p class="text-text-secondary text-sm mb-4">Plan: ${escapeHtml(client.plan)} • Goal: ${escapeHtml(
              client.goal
            )}</p>
            <div class="flex gap-6">
              ${headerStat({ label: "Weight", value: `${client.weightLbs} lbs` })}
              <div class="w-px bg-surface-highlight"></div>
              ${headerStat({ label: "Body Fat", value: `${client.bodyFatPct}%` })}
              <div class="w-px bg-surface-highlight"></div>
              ${headerStat({ label: "Email", value: client.email })}
            </div>
          </div>
        </div>

        <div class="flex gap-3">
          <button data-action="open-mailbox" class="flex items-center justify-center size-10 rounded-lg bg-surface-highlight text-white hover:bg-surface-highlight/80 transition-colors" title="Open Mailbox">
            <span class="material-symbols-outlined">chat</span>
          </button>
          <button data-action="open-training" class="flex items-center justify-center gap-2 h-10 px-4 rounded-lg bg-primary text-background-dark text-sm font-bold hover:bg-opacity-90 transition-opacity">
            <span class="material-symbols-outlined text-[18px]">assignment</span>
            Training Plan
          </button>
          <button data-action="open-nutrition" class="flex items-center justify-center gap-2 h-10 px-4 rounded-lg bg-surface-highlight text-white text-sm font-bold hover:bg-surface-highlight/80">
            <span class="material-symbols-outlined text-[18px]">restaurant</span>
            Nutrition
          </button>
        </div>
      </div>

      <div class="flex gap-6 mt-8 border-b border-surface-highlight">
        <button class="pb-3 text-sm font-bold text-primary border-b-2 border-primary">Overview</button>
        <button class="pb-3 text-sm font-medium text-text-secondary hover:text-white transition-colors">Training Plan</button>
        <button class="pb-3 text-sm font-medium text-text-secondary hover:text-white transition-colors">Nutrition</button>
        <button class="pb-3 text-sm font-medium text-text-secondary hover:text-white transition-colors">Progress</button>
        <button class="pb-3 text-sm font-medium text-text-secondary hover:text-white transition-colors">History</button>
      </div>
    </div>

    <div class="p-8 grid grid-cols-12 gap-6">
      <div class="col-span-12 lg:col-span-4 flex flex-col gap-6">
        <div class="bg-surface-darker rounded-xl p-5 border border-surface-highlight">
          <div class="flex justify-between items-center mb-4">
            <h3 class="text-white font-bold text-lg">Personal Details</h3>
            <span class="text-primary text-sm font-medium">Edit</span>
          </div>
          <div class="space-y-4">
            ${detailRow({ icon: "mail", label: "Email", value: client.email })}
            ${detailRow({ icon: "call", label: "Phone", value: client.phone })}
            ${detailRow({ icon: "cake", label: "Age", value: `${client.age} years` })}
            ${detailRow({ icon: "height", label: "Height", value: client.height })}
          </div>
        </div>

        <div class="bg-surface-darker rounded-xl p-5 border border-surface-highlight">
          <div class="flex justify-between items-center mb-4">
            <h3 class="text-white font-bold text-lg">Next Session</h3>
            <button class="text-text-secondary hover:text-white"><span class="material-symbols-outlined">more_horiz</span></button>
          </div>
          <div class="bg-surface-highlight/30 rounded-lg p-4 border border-surface-highlight mb-3">
            <div class="flex justify-between items-start">
              <div>
                <p class="text-primary font-bold text-sm mb-1">Tomorrow, 10:00 AM</p>
                <p class="text-white font-medium">Lower Body Power</p>
                <p class="text-text-secondary text-xs mt-1">Leg Press, Squats, Lunges</p>
              </div>
              <div class="size-10 rounded-full bg-surface-highlight flex items-center justify-center">
                <span class="material-symbols-outlined text-white">fitness_center</span>
              </div>
            </div>
          </div>
          <button class="w-full py-2 rounded-lg border border-surface-highlight text-text-secondary hover:text-white hover:bg-surface-highlight text-sm font-medium transition-colors">
            View Full Schedule
          </button>
        </div>
      </div>

      <div class="col-span-12 lg:col-span-8 flex flex-col gap-6">
        <div class="bg-surface-darker rounded-xl p-6 border border-surface-highlight">
          <div class="flex justify-between items-center mb-6">
            <div>
              <h3 class="text-white font-bold text-lg">Weight Progress</h3>
              <p class="text-text-secondary text-sm">Last 6 months</p>
            </div>
            <div class="flex bg-surface-highlight rounded-lg p-0.5">
              <button class="px-3 py-1 rounded-md bg-surface-darker text-white text-xs font-medium shadow-sm">Weight</button>
              <button class="px-3 py-1 rounded-md text-text-secondary text-xs font-medium hover:text-white">Body Fat</button>
              <button class="px-3 py-1 rounded-md text-text-secondary text-xs font-medium hover:text-white">Muscle</button>
            </div>
          </div>
          <div class="w-full h-48 flex items-end justify-between gap-2 px-2">
            ${[80, 75, 70, 65, 60, 55]
              .map(
                (h, idx) => `
                <div class="flex flex-col items-center gap-2 group w-full">
                  <div class="w-full max-w-[40px] ${
                    idx === 5 ? "bg-primary" : "bg-surface-highlight"
                  } rounded-t-sm h-[${h}%] relative group-hover:bg-primary/50 transition-colors"></div>
                  <span class="text-xs ${idx === 5 ? "text-white font-bold" : "text-text-secondary"}">${
                    ["Aug", "Sep", "Oct", "Nov", "Dec", "Jan"][idx]
                  }</span>
                </div>
              `
              )
              .join("")}
          </div>
        </div>

        <div class="bg-surface-darker rounded-xl border border-surface-highlight flex-1 overflow-hidden flex flex-col">
          <div class="p-5 border-b border-surface-highlight flex justify-between items-center">
            <h3 class="text-white font-bold text-lg">Training History</h3>
            <span class="text-primary text-sm font-medium">View All</span>
          </div>
          <div class="overflow-x-auto">
            <table class="w-full text-left border-collapse">
              <thead>
                <tr class="text-text-secondary text-xs border-b border-surface-highlight">
                  <th class="px-6 py-3 font-medium uppercase tracking-wider">Date</th>
                  <th class="px-6 py-3 font-medium uppercase tracking-wider">Workout Name</th>
                  <th class="px-6 py-3 font-medium uppercase tracking-wider">Duration</th>
                  <th class="px-6 py-3 font-medium uppercase tracking-wider">Status</th>
                </tr>
              </thead>
              <tbody class="text-sm">
                ${historyRow({ date: "Jan 24, 2024", name: "Upper Body Hypertrophy", duration: "55 min", status: "Completed" })}
                ${historyRow({ date: "Jan 22, 2024", name: "Cardio & Core", duration: "40 min", status: "Completed" })}
                ${historyRow({ date: "Jan 20, 2024", name: "Leg Day", duration: "--", status: "Missed" })}
              </tbody>
            </table>
          </div>
        </div>
      </div>
    </div>
  `;
}

function headerStat({ label, value }) {
  return `
    <div>
      <p class="text-xs text-text-secondary uppercase tracking-wider font-semibold">${escapeHtml(label)}</p>
      <p class="text-white font-bold text-sm truncate max-w-[220px]">${escapeHtml(value)}</p>
    </div>
  `;
}

function detailRow({ icon, label, value }) {
  return `
    <div class="flex items-center gap-3">
      <div class="size-8 rounded bg-surface-highlight flex items-center justify-center text-text-secondary">
        <span class="material-symbols-outlined text-sm">${escapeHtml(icon)}</span>
      </div>
      <div>
        <p class="text-xs text-text-secondary">${escapeHtml(label)}</p>
        <p class="text-sm text-white">${escapeHtml(value)}</p>
      </div>
    </div>
  `;
}

function historyRow({ date, name, duration, status }) {
  const ok = status === "Completed";
  const pill = ok
    ? "bg-green-900/40 text-green-400 border border-green-800"
    : "bg-red-900/40 text-red-400 border border-red-800";

  return `
    <tr class="border-b border-surface-highlight/50 hover:bg-surface-highlight/30 transition-colors">
      <td class="px-6 py-4 text-white">${escapeHtml(date)}</td>
      <td class="px-6 py-4 text-white font-medium">${escapeHtml(name)}</td>
      <td class="px-6 py-4 text-text-secondary">${escapeHtml(duration)}</td>
      <td class="px-6 py-4">
        <span class="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-medium ${pill}">
          <span class="size-1.5 rounded-full ${ok ? "bg-green-400" : "bg-red-400"}"></span>
          ${escapeHtml(status)}
        </span>
      </td>
    </tr>
  `;
}

function emptyState() {
  return `
    <div class="h-full flex items-center justify-center text-text-secondary">
      <div class="text-center">
        <div class="flex items-center justify-center mb-2">
          <span class="material-symbols-outlined text-4xl">group</span>
        </div>
        <p class="text-sm">No client selected.</p>
      </div>
    </div>
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

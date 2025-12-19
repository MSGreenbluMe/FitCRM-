import { store } from "../store.js";
import { showToast } from "../ui/toast.js";

const FOLDERS = [
  { id: "inbox", label: "Inbox", statuses: ["new"] },
  { id: "assigned", label: "Assigned", statuses: ["assigned"] },
  { id: "done", label: "Done", statuses: ["done"] },
  { id: "all", label: "All", statuses: ["new", "assigned", "done"] },
];

export class MailboxPage {
  constructor() {
    this.el = null;
    this.unsub = null;
    this.folder = "inbox";
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
    const selected = state.tickets.find((t) => t.id === ui.selectedTicketId) || state.tickets[0];
    const selectedClient =
      state.clients.find((c) => c.id === selected?.clientId) ||
      state.clients.find((c) => c.id === ui.selectedClientId) ||
      state.clients[0];

    const folderDef = FOLDERS.find((f) => f.id === this.folder) || FOLDERS[0];
    const visibleTickets = state.tickets.filter((t) => folderDef.statuses.includes(t.status));

    const unreadCount = state.tickets.filter((t) => !t.read).length;

    this.el.innerHTML = `
      <div class="w-64 bg-surface-darker border-r border-surface-highlight flex flex-col shrink-0">
        <div class="p-4 border-b border-surface-highlight">
          <h2 class="text-white font-bold text-lg">Folders</h2>
        </div>
        <div class="p-2 flex flex-col gap-1">
          ${FOLDERS.map((f) => folderBtn({ folder: f, active: f.id === this.folder })).join("")}
        </div>
      </div>

      <div class="w-80 border-r border-surface-highlight bg-background-dark flex flex-col shrink-0">
        <div class="p-4 border-b border-surface-highlight flex flex-col gap-4">
          <div class="flex justify-between items-center">
            <h2 class="text-xl font-bold text-white">Messages</h2>
            <div class="text-text-secondary text-xs">Unread: <span class="text-primary font-bold">${unreadCount}</span></div>
          </div>
          <div class="relative group">
            <div class="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
              <span class="material-symbols-outlined text-text-secondary group-focus-within:text-white transition-colors">search</span>
            </div>
            <input data-role="search" class="block w-full pl-10 pr-3 py-2 border-none rounded-lg bg-surface-highlight text-white placeholder-text-secondary focus:ring-1 focus:ring-primary focus:bg-[#2f5f3e] sm:text-sm transition-all" placeholder="Search tickets..." type="text"/>
          </div>
        </div>

        <div class="flex-1 overflow-y-auto" data-role="ticket-list">
          ${visibleTickets
            .map((t) => ticketRow({ t, active: selected && selected.id === t.id, clients: state.clients }))
            .join("")}
          ${visibleTickets.length === 0 ? emptyTickets() : ""}
        </div>
      </div>

      <div class="flex-1 flex flex-col bg-surface-darker relative">
        ${selected ? conversationHeader({ selected, client: selectedClient }) : emptyConversation()}
        <div class="flex-1 overflow-y-auto p-6 flex flex-col gap-6" data-role="messages">
          ${selected ? renderConversation(state, selected.id) : ""}
        </div>

        <div class="p-4 border-t border-surface-highlight bg-background-dark">
          <div class="flex items-center gap-2 mb-3">
            <button data-action="assign" class="px-3 py-2 rounded-lg bg-surface-highlight text-white text-xs font-bold hover:bg-[#2f5f3e]">Assign</button>
            <button data-action="done" class="px-3 py-2 rounded-lg bg-surface-highlight text-white text-xs font-bold hover:bg-[#2f5f3e]">Done</button>
          </div>

          <div class="flex flex-col gap-2 bg-surface-dark rounded-xl p-2 border border-surface-highlight focus-within:border-primary/50 transition-colors">
            <textarea data-role="composer" class="w-full bg-transparent border-none text-white placeholder-[#5d7d6a] text-sm focus:ring-0 resize-none h-20 px-2 py-1" placeholder="Type your message..."></textarea>
            <div class="flex justify-end items-center px-2 pb-1">
              <button data-action="send" class="bg-primary hover:bg-[#0fd650] text-background-dark font-bold text-sm px-4 py-2 rounded-lg flex items-center gap-2 transition-colors">
                Send <span class="material-symbols-outlined text-sm">send</span>
              </button>
            </div>
          </div>
        </div>
      </div>

      <div class="w-80 border-l border-surface-highlight bg-background-dark hidden xl:flex flex-col shrink-0 overflow-y-auto">
        ${selectedClient ? clientSidebar(selectedClient) : ""}
      </div>
    `;

    this.el.querySelectorAll('[data-action="folder"]').forEach((b) => {
      b.addEventListener("click", (e) => {
        this.folder = e.currentTarget.dataset.folderId;
        this.render();
      });
    });

    this.el.querySelectorAll('[data-action="select-ticket"]').forEach((row) => {
      row.addEventListener("click", (e) => {
        const id = e.currentTarget.dataset.ticketId;
        store.selectTicket(id);
      });
    });

    const searchInput = this.el.querySelector('[data-role="search"]');
    if (searchInput) {
      searchInput.addEventListener("input", () => {
        const q = searchInput.value.trim().toLowerCase();
        const list = this.el.querySelector('[data-role="ticket-list"]');
        list.querySelectorAll('[data-action="select-ticket"]').forEach((row) => {
          const hay = (row.dataset.searchHay || "").toLowerCase();
          row.style.display = q === "" || hay.includes(q) ? "" : "none";
        });
      });
    }

    const assignBtn = this.el.querySelector('[data-action="assign"]');
    const doneBtn = this.el.querySelector('[data-action="done"]');

    if (selected && assignBtn) {
      assignBtn.addEventListener("click", () => {
        store.updateTicketStatus(selected.id, "assigned");
        showToast({ title: "Ticket updated", message: "Status set to Assigned." });
      });
    }

    if (selected && doneBtn) {
      doneBtn.addEventListener("click", () => {
        store.updateTicketStatus(selected.id, "done");
        showToast({ title: "Ticket updated", message: "Status set to Done." });
      });
    }

    const sendBtn = this.el.querySelector('[data-action="send"]');
    const composer = this.el.querySelector('[data-role="composer"]');

    if (selected && sendBtn && composer) {
      sendBtn.addEventListener("click", () => {
        const text = composer.value.trim();
        if (!text) return;
        store.sendMessage(selected.id, text);
        composer.value = "";
        showToast({ title: "Message sent", message: "Demo message appended to conversation." });
        const messagesEl = this.el.querySelector('[data-role="messages"]');
        messagesEl.scrollTop = messagesEl.scrollHeight;
      });
    }

    this.el.querySelectorAll('[data-action="open-client"]').forEach((btn) => {
      btn.addEventListener("click", () => {
        const id = btn.dataset.clientId;
        store.selectClient(id);
        window.location.hash = "#/clients";
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

function folderBtn({ folder, active }) {
  const cls = active
    ? "bg-surface-highlight text-primary"
    : "text-text-secondary hover:bg-surface-highlight hover:text-white";

  return `
    <button data-action="folder" data-folder-id="${escapeAttr(folder.id)}" class="flex items-center gap-3 px-3 py-2.5 rounded-lg ${cls} transition-colors text-left">
      <span class="material-symbols-outlined">folder</span>
      <span class="text-sm font-medium">${escapeHtml(folder.label)}</span>
    </button>
  `;
}

function ticketRow({ t, active, clients }) {
  const cls = active
    ? "bg-[#1a3525] border-l-4 border-l-primary"
    : "hover:bg-surface-dark";

  const fromClient = clients.find((c) => c.id === t.clientId);
  const title = fromClient ? fromClient.name : t.from;
  const dot = t.read ? "bg-gray-500" : "bg-primary";

  return `
    <div data-action="select-ticket" data-ticket-id="${escapeAttr(t.id)}" data-search-hay="${escapeAttr(
      `${t.subject} ${t.from} ${t.content} ${title}`
    )}" class="p-4 border-b border-surface-highlight cursor-pointer transition-colors ${cls}">
      <div class="flex justify-between items-start mb-1">
        <div class="flex items-center gap-3">
          <div class="relative">
            <div class="h-10 w-10 rounded-full bg-surface-highlight flex items-center justify-center">
              <span class="material-symbols-outlined text-white">person</span>
            </div>
            <span class="absolute bottom-0 right-0 block h-2.5 w-2.5 rounded-full ${dot} ring-2 ring-background-dark"></span>
          </div>
          <div>
            <h3 class="text-white font-bold text-sm">${escapeHtml(title)}</h3>
            <span class="text-text-secondary text-xs">${escapeHtml(t.subject)}</span>
          </div>
        </div>
        <span class="text-text-secondary text-xs whitespace-nowrap">${escapeHtml(t.time)}</span>
      </div>
      <p class="text-white text-sm mt-2 line-clamp-2">${escapeHtml(t.content)}</p>
      <div class="mt-2 flex items-center gap-2">
        <span class="text-[10px] font-bold px-2 py-1 rounded bg-surface-highlight text-text-secondary">${escapeHtml(
          t.status.toUpperCase()
        )}</span>
        <span class="text-[10px] font-bold px-2 py-1 rounded bg-surface-highlight text-text-secondary">${escapeHtml(
          t.priority.toUpperCase()
        )}</span>
      </div>
    </div>
  `;
}

function conversationHeader({ selected, client }) {
  const statusDot = selected.status === "done" ? "bg-gray-500" : "bg-primary";

  return `
    <div class="h-16 border-b border-surface-highlight flex items-center justify-between px-6 shrink-0 bg-background-dark/95 backdrop-blur">
      <div class="flex items-center gap-4">
        <div class="h-9 w-9 rounded-full bg-surface-highlight flex items-center justify-center">
          <span class="material-symbols-outlined text-white">person</span>
        </div>
        <div>
          <h2 class="text-white font-bold text-base leading-tight">${escapeHtml(client?.name || selected.from)}</h2>
          <div class="flex items-center gap-1.5">
            <span class="w-2 h-2 rounded-full ${statusDot}"></span>
            <span class="text-text-secondary text-xs">${escapeHtml(selected.subject)}</span>
          </div>
        </div>
      </div>

      <div class="flex items-center gap-2">
        <button data-action="open-client" data-client-id="${escapeAttr(
          client?.id || ""
        )}" class="p-2 text-text-secondary hover:text-white hover:bg-surface-highlight rounded-lg transition-colors" title="Open Client">
          <span class="material-symbols-outlined">open_in_new</span>
        </button>
      </div>
    </div>
  `;
}

function renderConversation(state, ticketId) {
  const messages = state.conversations[ticketId] || [];
  if (messages.length === 0) return emptyConversation();

  return messages
    .map((m) => {
      if (m.role === "system") {
        return `
          <div class="flex justify-center w-full">
            <div class="flex items-center gap-2 bg-surface-dark border border-surface-highlight px-4 py-2 rounded-lg max-w-md">
              <span class="material-symbols-outlined text-primary text-sm">check_circle</span>
              <p class="text-text-secondary text-sm">${escapeHtml(m.text)}</p>
            </div>
          </div>
        `;
      }

      if (m.role === "trainer") {
        return `
          <div class="flex justify-end">
            <div class="flex flex-col items-end max-w-[70%]">
              <div class="bg-surface-highlight text-white p-4 rounded-2xl rounded-tr-sm">
                <p class="text-sm">${escapeHtml(m.text)}</p>
              </div>
            </div>
          </div>
        `;
      }

      return `
        <div class="flex justify-start">
          <div class="flex flex-col items-start max-w-[70%]">
            <div class="bg-[#2f2f2f] border border-[#333] text-white p-4 rounded-2xl rounded-tl-sm">
              <p class="text-sm">${escapeHtml(m.text)}</p>
            </div>
          </div>
        </div>
      `;
    })
    .join("");
}

function clientSidebar(client) {
  return `
    <div class="p-6 border-b border-surface-highlight flex flex-col items-center text-center">
      <div class="h-24 w-24 rounded-full bg-surface-highlight mb-3 ring-4 ring-surface-highlight flex items-center justify-center">
        <span class="material-symbols-outlined text-white text-4xl">person</span>
      </div>
      <h2 class="text-white text-xl font-bold">${escapeHtml(client.name)}</h2>
      <p class="text-text-secondary text-sm">Age ${escapeHtml(client.age)} • ${escapeHtml(client.city)}</p>
      <div class="grid grid-cols-3 gap-2 w-full mt-6">
        ${miniStat({ label: "Weight", value: `${client.weightLbs} lbs` })}
        ${miniStat({ label: "Height", value: client.height })}
        ${miniStat({ label: "Fat %", value: `${client.bodyFatPct}%` })}
      </div>
    </div>

    <div class="p-6 border-b border-surface-highlight">
      <div class="flex justify-between items-center mb-3">
        <h3 class="text-white font-bold text-sm">Current Goal</h3>
        <span class="text-primary text-xs font-bold bg-primary/20 px-2 py-0.5 rounded">${escapeHtml(
          client.goal
        )}</span>
      </div>
      <p class="text-xs text-text-secondary leading-relaxed">Plan: ${escapeHtml(client.plan)}</p>
    </div>

    <div class="p-6">
      <h3 class="text-white font-bold text-sm mb-4">Quick Links</h3>
      <div class="flex flex-col gap-2">
        <a class="w-full bg-surface-highlight text-white hover:bg-[#2f5f3e] py-2 rounded-lg text-sm font-medium transition-colors border border-[#395c46] text-center" href="#/clients">Client Profile</a>
        <a class="w-full bg-surface-highlight text-white hover:bg-[#2f5f3e] py-2 rounded-lg text-sm font-medium transition-colors border border-[#395c46] text-center" href="#/training-plan">Training Plan</a>
        <a class="w-full bg-surface-highlight text-white hover:bg-[#2f5f3e] py-2 rounded-lg text-sm font-medium transition-colors border border-[#395c46] text-center" href="#/nutrition">Nutrition</a>
      </div>
    </div>
  `;
}

function miniStat({ label, value }) {
  return `
    <div class="bg-surface-highlight p-2 rounded-lg flex flex-col">
      <span class="text-text-secondary text-xs uppercase">${escapeHtml(label)}</span>
      <span class="text-white font-bold text-sm">${escapeHtml(value)}</span>
    </div>
  `;
}

function emptyTickets() {
  return `
    <div class="p-6 text-center text-text-secondary">
      <div class="flex items-center justify-center mb-2">
        <span class="material-symbols-outlined text-3xl">inbox</span>
      </div>
      <p class="text-sm">No tickets in this folder.</p>
    </div>
  `;
}

function emptyConversation() {
  return `
    <div class="p-10 text-center text-text-secondary">
      <div class="flex items-center justify-center mb-2">
        <span class="material-symbols-outlined text-3xl">chat</span>
      </div>
      <p class="text-sm">Select a message to view conversation.</p>
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

import { store } from "../store.js";

function navItem({ icon, label, path }) {
  return {
    icon,
    label,
    path,
  };
}

const NAV_ITEMS = [
  navItem({ icon: "dashboard", label: "Dashboard", path: "/dashboard" }),
  navItem({ icon: "mail", label: "Mailbox", path: "/mailbox" }),
  navItem({ icon: "group", label: "Clients", path: "/clients" }),
  navItem({ icon: "assignment", label: "Plans", path: "/training-plan" }),
  navItem({ icon: "restaurant", label: "Nutrition", path: "/nutrition" }),
];

export class Layout {
  constructor({ onNavigate }) {
    this.onNavigate = onNavigate;
    this.el = null;
    this.pageContainerEl = null;
    this.page = null;
    this.unsub = null;
  }

  mount(container) {
    this.el = document.createElement("div");
    this.el.className = "h-full flex";

    this.el.innerHTML = `
      <nav class="w-64 bg-surface-darker border-r border-surface-highlight flex flex-col justify-between shrink-0 z-20">
        <div class="flex flex-col p-4 gap-6">
          <div class="flex items-center gap-3 px-2">
            <div class="bg-primary/20 p-2 rounded-lg text-primary">
              <span class="material-symbols-outlined text-2xl">fitness_center</span>
            </div>
            <div class="flex flex-col">
              <h1 class="text-white text-lg font-bold leading-none">FitCRM</h1>
              <p class="text-text-secondary text-xs font-normal">Demo</p>
            </div>
          </div>

          <div class="flex flex-col gap-1" data-role="nav"></div>

          <div class="mt-2">
            <button data-action="reset" class="w-full flex items-center justify-center gap-2 h-11 rounded-lg bg-surface-highlight hover:bg-[#2f5f3e] text-white text-sm font-bold transition-colors border border-[#395c46]">
              <span class="material-symbols-outlined text-[18px]">restart_alt</span>
              Reset demo state
            </button>
          </div>
        </div>

        <div class="p-4 border-t border-surface-highlight">
          <div class="flex items-center gap-3">
            <div class="h-10 w-10 rounded-full bg-surface-highlight border border-surface-highlight flex items-center justify-center">
              <span class="material-symbols-outlined text-white">person</span>
            </div>
            <div class="flex flex-col overflow-hidden">
              <p class="text-sm font-bold text-white truncate">Alex Trainer</p>
              <p class="text-xs text-text-secondary truncate">Pro Account</p>
            </div>
          </div>
        </div>
      </nav>

      <main class="flex flex-1 overflow-hidden relative">
        <div class="flex-1 flex flex-col min-w-0 h-full">
          <header class="flex items-center justify-between border-b border-surface-highlight px-6 py-4 bg-background-dark/95 backdrop-blur-sm sticky top-0 z-10">
            <div class="flex-1 max-w-md">
              <label class="flex items-center w-full h-10 rounded-lg bg-surface-highlight border border-transparent focus-within:border-primary/50 transition-colors">
                <div class="pl-3 text-text-secondary flex items-center justify-center">
                  <span class="material-symbols-outlined text-[20px]">search</span>
                </div>
                <input data-role="global-search" class="w-full bg-transparent border-none text-white placeholder-text-secondary text-sm px-3 focus:ring-0" placeholder="Search (demo only)" />
              </label>
            </div>

            <div class="flex items-center gap-4 ml-4">
              <a class="text-text-secondary hover:text-white text-sm font-bold" href="../docs/FITCRM_PROJECT_SUMMARY.md" target="_blank" rel="noreferrer">Docs</a>
              <div class="h-8 w-px bg-surface-highlight mx-1"></div>
              <div class="flex items-center gap-3">
                <div class="text-right hidden sm:block">
                  <p class="text-sm font-bold text-white leading-tight">Coach Mike</p>
                  <p class="text-xs text-text-secondary">Demo User</p>
                </div>
                <div class="bg-surface-highlight rounded-full size-10 border-2 border-surface-highlight flex items-center justify-center">
                  <span class="material-symbols-outlined text-white">person</span>
                </div>
              </div>
            </div>
          </header>

          <section data-role="page" class="flex-1 overflow-hidden"></section>
        </div>
      </main>
    `;

    container.appendChild(this.el);

    const navEl = this.el.querySelector('[data-role="nav"]');
    for (const item of NAV_ITEMS) {
      const a = document.createElement("a");
      a.href = `#${item.path}`;
      a.className =
        "flex items-center gap-3 px-3 py-2.5 rounded-lg text-text-secondary hover:bg-surface-highlight hover:text-white transition-colors";
      a.dataset.path = item.path;
      a.innerHTML = `
        <span class="material-symbols-outlined">${item.icon}</span>
        <span class="text-sm font-medium">${item.label}</span>
      `;
      a.addEventListener("click", (e) => {
        e.preventDefault();
        this.onNavigate(item.path);
      });
      navEl.appendChild(a);
    }

    this.pageContainerEl = this.el.querySelector('[data-role="page"]');

    const resetBtn = this.el.querySelector('[data-action="reset"]');
    resetBtn.addEventListener("click", () => {
      store.reset();
      window.location.hash = "#/dashboard";
    });

    this.unsub = store.subscribe(() => {
      this.renderNavActive();
    });

    this.renderNavActive();
  }

  setPage(page) {
    if (!this.pageContainerEl) return;

    if (this.page) {
      this.page.unmount();
      this.page = null;
    }

    this.pageContainerEl.innerHTML = "";
    this.page = page;
    this.page.mount(this.pageContainerEl);

    this.renderNavActive();
  }

  renderNavActive() {
    const path = (window.location.hash || "#/dashboard").replace(/^#/, "");
    const navLinks = this.el.querySelectorAll('[data-role="nav"] a');

    for (const link of navLinks) {
      const isActive = link.dataset.path === path;
      link.className = isActive
        ? "flex items-center gap-3 px-3 py-2.5 rounded-lg bg-surface-highlight text-primary"
        : "flex items-center gap-3 px-3 py-2.5 rounded-lg text-text-secondary hover:bg-surface-highlight hover:text-white transition-colors";
    }
  }

  unmount() {
    if (this.page) {
      this.page.unmount();
      this.page = null;
    }
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

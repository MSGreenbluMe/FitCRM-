import { store } from "../store.js";
import { showToast } from "../ui/toast.js";

const EXERCISE_LIBRARY = [
  { id: "lib_bench", name: "Barbell Bench Press", sets: 4, reps: "8-10", rpe: 8 },
  { id: "lib_squat", name: "Back Squat", sets: 4, reps: "6-8", rpe: 8 },
  { id: "lib_pullups", name: "Pull Ups", sets: 3, reps: "AMRAP", rpe: 8 },
  { id: "lib_row", name: "Dumbbell Row", sets: 3, reps: "10-12", rpe: 9 },
];

const DAY_ORDER = [
  { key: "mon", label: "Monday" },
  { key: "tue", label: "Tuesday" },
  { key: "wed", label: "Wednesday" },
  { key: "thu", label: "Thursday" },
];

export class TrainingPlanPage {
  constructor() {
    this.el = null;
    this.unsub = null;
    this.selectedLibId = EXERCISE_LIBRARY[0].id;
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
    const clientId = state.ui.selectedClientId;
    const client = state.clients.find((c) => c.id === clientId) || state.clients[0];
    const plan = state.trainingPlans[client.id];

    this.el.innerHTML = `
      <aside class="w-[320px] flex-none flex flex-col border-r border-surface-highlight bg-background-dark z-10">
        <div class="p-4 border-b border-surface-highlight">
          <h3 class="text-white text-lg font-bold mb-3 flex items-center gap-2">
            <span class="material-symbols-outlined text-primary">library_books</span>
            Exercise Library
          </h3>
          <div class="relative mb-3">
            <span class="material-symbols-outlined absolute left-3 top-2.5 text-text-secondary text-[20px]">search</span>
            <input data-role="search" class="w-full bg-surface-dark border-transparent focus:border-primary focus:ring-0 rounded-lg py-2 pl-10 pr-4 text-sm text-white placeholder:text-text-secondary transition-colors" placeholder="Search exercises..." type="text" />
          </div>
        </div>

        <div class="flex-1 overflow-y-auto p-4 space-y-3" data-role="library">
          ${EXERCISE_LIBRARY.map((ex) => libraryItem({ ex, active: ex.id === this.selectedLibId })).join("")}
        </div>

        <div class="p-4 border-t border-surface-highlight">
          <button data-action="add-to-mon" class="w-full bg-primary text-background-dark font-bold py-3 rounded-lg shadow-lg flex justify-center items-center gap-2 hover:brightness-110 transition-all">
            <span class="material-symbols-outlined">add_circle</span>
            Add to Monday
          </button>
        </div>
      </aside>

      <section class="flex-1 flex flex-col h-full overflow-hidden relative bg-background-dark">
        <div class="flex-none p-6 pb-2 border-b border-surface-highlight">
          <div class="flex flex-wrap gap-2 mb-4 items-center">
            <a class="text-text-secondary hover:text-primary text-sm font-medium leading-normal" href="#/dashboard">Dashboard</a>
            <span class="text-text-secondary text-sm">/</span>
            <a class="text-text-secondary hover:text-primary text-sm font-medium leading-normal" href="#/clients">Clients</a>
            <span class="text-text-secondary text-sm">/</span>
            <span class="text-white text-sm font-medium leading-normal">${escapeHtml(client.name)}</span>
          </div>

          <div class="flex flex-col xl:flex-row xl:items-end justify-between gap-6 mb-2">
            <div class="flex flex-col gap-1 w-full max-w-2xl">
              <div class="flex items-center gap-3">
                <h1 class="text-white text-3xl font-black leading-tight tracking-tight">${escapeHtml(
                  plan?.name || "Training Plan"
                )}</h1>
                <span class="px-2 py-0.5 rounded bg-green-900/40 text-primary text-xs font-bold uppercase tracking-wider border border-primary/20">Active Draft</span>
              </div>
              <p class="text-text-secondary text-sm">Designing for <span class="text-white font-bold">${escapeHtml(
                client.name
              )}</span> • Goal: ${escapeHtml(client.goal)}</p>
            </div>
            <div class="flex items-center gap-3">
              <button data-action="save" class="flex items-center gap-2 px-6 h-10 rounded-lg bg-primary text-black text-sm font-bold hover:brightness-110 transition-all shadow-[0_0_15px_rgba(19,236,91,0.3)]">
                <span class="material-symbols-outlined text-[18px]">save</span>
                Save Plan
              </button>
            </div>
          </div>
        </div>

        <div class="flex-1 overflow-x-auto overflow-y-hidden p-6 pt-4">
          <div class="flex h-full gap-4 min-w-[1200px]">
            ${DAY_ORDER.map((d) => dayColumn({ clientId: client.id, dayKey: d.key, label: d.label, plan })).join("")}
          </div>
        </div>
      </section>
    `;

    this.el.querySelectorAll('[data-action="select-lib"]').forEach((row) => {
      row.addEventListener("click", () => {
        this.selectedLibId = row.dataset.exerciseId;
        this.render();
      });
    });

    const search = this.el.querySelector('[data-role="search"]');
    if (search) {
      search.addEventListener("input", () => {
        const q = search.value.trim().toLowerCase();
        const list = this.el.querySelector('[data-role="library"]');
        list.querySelectorAll('[data-action="select-lib"]').forEach((row) => {
          const hay = (row.dataset.searchHay || "").toLowerCase();
          row.style.display = q === "" || hay.includes(q) ? "" : "none";
        });
      });
    }

    const addBtn = this.el.querySelector('[data-action="add-to-mon"]');
    if (addBtn && plan) {
      addBtn.addEventListener("click", () => {
        const ex = EXERCISE_LIBRARY.find((e) => e.id === this.selectedLibId);
        if (!ex) return;
        store.addExerciseToDay({ clientId: client.id, dayKey: "mon", exercise: ex });
        showToast({ title: "Exercise added", message: `Added ${ex.name} to Monday.` });
      });
    }

    const saveBtn = this.el.querySelector('[data-action="save"]');
    if (saveBtn) {
      saveBtn.addEventListener("click", () => {
        showToast({ title: "Saved", message: "Demo save (stored in localStorage)." });
      });
    }

    this.el.querySelectorAll('[data-action="update-ex"]').forEach((input) => {
      input.addEventListener("change", () => {
        const { clientId: cId, dayKey, exId, field } = input.dataset;
        const val = input.value;
        const patch = field === "sets" || field === "rpe" ? { [field]: Number(val) } : { [field]: val };
        store.updateExercise({ clientId: cId, dayKey, exerciseId: exId, patch });
      });
    });

    this.el.querySelectorAll('[data-action="remove-ex"]').forEach((btn) => {
      btn.addEventListener("click", () => {
        const { clientId: cId, dayKey, exId } = btn.dataset;
        store.removeExercise({ clientId: cId, dayKey, exerciseId: exId });
        showToast({ title: "Removed", message: "Exercise removed from day." });
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

function libraryItem({ ex, active }) {
  const cls = active ? "border-primary bg-surface-dark" : "border-border-dark bg-surface-dark";

  return `
    <div data-action="select-lib" data-exercise-id="${escapeAttr(ex.id)}" data-search-hay="${escapeAttr(
      ex.name
    )}" class="group cursor-pointer ${cls} border rounded-lg p-3 hover:border-primary transition-all shadow-sm">
      <div class="flex gap-3">
        <div class="w-10 h-10 rounded bg-black/30 flex-none flex items-center justify-center">
          <span class="material-symbols-outlined text-text-secondary">fitness_center</span>
        </div>
        <div class="flex-1 min-w-0">
          <h4 class="text-sm font-bold text-white truncate">${escapeHtml(ex.name)}</h4>
          <p class="text-xs text-text-secondary">Sets ${ex.sets} • Reps ${escapeHtml(ex.reps)} • RPE ${ex.rpe}</p>
        </div>
      </div>
    </div>
  `;
}

function dayColumn({ clientId, dayKey, label, plan }) {
  const day = plan?.days?.[dayKey];
  const title = day?.title || "Workout";
  const items = day?.items || [];

  const isRest = dayKey === "wed";

  return `
    <div class="flex flex-col w-[340px] flex-none bg-surface-dark/50 rounded-xl border border-border-dark h-full overflow-hidden ring-1 ring-transparent hover:ring-primary/30 transition-shadow">
      <div class="p-4 border-b border-border-dark bg-surface-dark sticky top-0 z-10">
        <div class="flex justify-between items-center mb-2">
          <h3 class="text-white font-black text-lg tracking-tight">${escapeHtml(label).toUpperCase()}</h3>
          <button class="text-text-secondary hover:text-primary"><span class="material-symbols-outlined text-[20px]">more_horiz</span></button>
        </div>
        <input class="w-full bg-transparent border-none p-0 text-sm font-medium text-primary placeholder:text-text-secondary focus:ring-0 mb-1" value="${escapeAttr(
          title
        )}" disabled />
        <div class="text-xs text-text-secondary flex justify-between">
          <span>${items.length} Exercises</span>
          <span>Est. ${Math.max(0, items.length * 12)} min</span>
        </div>
      </div>

      <div class="flex-1 overflow-y-auto p-2 space-y-2">
        ${isRest ? restState() : items.map((ex) => exerciseCard({ clientId, dayKey, ex })).join("")}
        ${!isRest ? addDropZone() : ""}
      </div>
    </div>
  `;
}

function exerciseCard({ clientId, dayKey, ex }) {
  return `
    <div class="bg-[#15281e] rounded-lg p-3 border border-border-dark shadow-sm group">
      <div class="flex justify-between items-start mb-2">
        <h4 class="font-bold text-white text-sm">${escapeHtml(ex.name)}</h4>
        <button data-action="remove-ex" data-client-id="${escapeAttr(clientId)}" data-day-key="${escapeAttr(
          dayKey
        )}" data-ex-id="${escapeAttr(ex.id)}" class="text-text-secondary hover:text-red-400 opacity-0 group-hover:opacity-100 transition-opacity">
          <span class="material-symbols-outlined text-[16px]">close</span>
        </button>
      </div>
      <div class="grid grid-cols-3 gap-2 mb-2">
        ${numberField({ clientId, dayKey, exId: ex.id, field: "sets", label: "Sets", value: ex.sets })}
        ${textField({ clientId, dayKey, exId: ex.id, field: "reps", label: "Reps", value: ex.reps })}
        ${numberField({ clientId, dayKey, exId: ex.id, field: "rpe", label: "RPE", value: ex.rpe })}
      </div>
    </div>
  `;
}

function numberField({ clientId, dayKey, exId, field, label, value }) {
  return `
    <label class="flex flex-col">
      <span class="text-[10px] text-text-secondary uppercase">${escapeHtml(label)}</span>
      <input data-action="update-ex" data-client-id="${escapeAttr(clientId)}" data-day-key="${escapeAttr(
        dayKey
      )}" data-ex-id="${escapeAttr(exId)}" data-field="${escapeAttr(
        field
      )}" class="h-7 w-full bg-black/20 border border-border-dark rounded text-center text-sm font-mono text-white focus:border-primary focus:ring-0 p-0" type="number" value="${escapeAttr(
        value
      )}" />
    </label>
  `;
}

function textField({ clientId, dayKey, exId, field, label, value }) {
  return `
    <label class="flex flex-col">
      <span class="text-[10px] text-text-secondary uppercase">${escapeHtml(label)}</span>
      <input data-action="update-ex" data-client-id="${escapeAttr(clientId)}" data-day-key="${escapeAttr(
        dayKey
      )}" data-ex-id="${escapeAttr(exId)}" data-field="${escapeAttr(
        field
      )}" class="h-7 w-full bg-black/20 border border-border-dark rounded text-center text-sm font-mono text-white focus:border-primary focus:ring-0 p-0" type="text" value="${escapeAttr(
        value
      )}" />
    </label>
  `;
}

function addDropZone() {
  return `
    <div class="border-2 border-dashed border-border-dark rounded-lg p-4 flex flex-col items-center justify-center text-text-secondary min-h-[90px] transition-colors hover:border-primary hover:text-primary hover:bg-primary/5 cursor-not-allowed">
      <span class="material-symbols-outlined mb-1">add</span>
      <span class="text-xs font-medium">Drag & drop (not implemented)</span>
    </div>
  `;
}

function restState() {
  return `
    <div class="p-6 flex flex-col items-center justify-center text-center opacity-70">
      <div class="mb-3">
        <span class="material-symbols-outlined text-5xl text-text-secondary">self_improvement</span>
      </div>
      <h4 class="text-white font-bold text-lg mb-2">Rest Day</h4>
      <p class="text-sm text-text-secondary">Light stretching or mobility recommended.</p>
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

import { store } from "../store.js";
import { showToast } from "../ui/toast.js";
import { sendEmail, generatePlan } from "../api.js";

const DAYS = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"];

const QUICK_ADD = [
  { name: "Avocado Toast", desc: "Simple snack", kcal: 280, protein: 8, carbs: 26, fats: 14 },
  { name: "Whey Protein Shake", desc: "Fast protein", kcal: 140, protein: 25, carbs: 4, fats: 2 },
  { name: "Greek Yogurt Bowl", desc: "Yogurt + fruit", kcal: 220, protein: 18, carbs: 20, fats: 6 },
];

function buildLocalFallbackNutrition({ client, goal }) {
  const g = String(goal || client?.goal || "General Fitness");
  return {
    weekLabel: "This Week",
    day: "Tue",
    meals: {
      breakfast: [
        { name: "Greek yogurt + berries", desc: "High protein start", kcal: 320, protein: 28, carbs: 30, fats: 8 },
      ],
      lunch: [
        { name: "Chicken + rice + veggies", desc: "Balanced meal", kcal: 620, protein: 45, carbs: 70, fats: 14 },
      ],
      dinner: [
        { name: "Salmon + potatoes + salad", desc: "Omega-3 + carbs", kcal: 650, protein: 42, carbs: 55, fats: 26 },
      ],
    },
    notes: `Goal: ${g}. Keep it simple, hit protein target, hydrate.`,
    targets: { kcal: 2100, protein: 170, carbs: 220, fats: 65, waterLiters: 3.5 },
  };
}

export class NutritionPage {
  constructor() {
    this.el = null;
    this.unsub = null;
    this.day = "Tue";
    this.aiInFlight = false;
    this.aiCooldownUntil = 0;
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
    const n = state.nutrition[client.id] || null;

    const totals = calcTotals(n);

    this.el.innerHTML = `
      <main class="flex-1 flex flex-col min-w-0 overflow-hidden bg-background-dark relative">
        <header class="flex-shrink-0 border-b border-surface-highlight p-6 pb-2">
          <div class="flex flex-wrap gap-2 mb-4">
            <a class="text-text-secondary text-sm font-medium hover:text-white" href="#/clients">Clients</a>
            <span class="text-text-secondary text-sm">/</span>
            <span class="text-text-secondary text-sm font-medium">${escapeHtml(client.name)}</span>
            <span class="text-text-secondary text-sm">/</span>
            <span class="text-primary text-sm font-bold">Nutrition Plan</span>
          </div>

          <div class="flex flex-col md:flex-row justify-between items-start md:items-center gap-4">
            <div class="flex gap-4 items-center">
              <div class="bg-surface-highlight rounded-full h-16 w-16 ring-2 ring-surface-highlight flex items-center justify-center">
                <span class="material-symbols-outlined text-white text-4xl">person</span>
              </div>
              <div>
                <h2 class="text-white text-2xl font-bold tracking-tight">${escapeHtml(client.name)}</h2>
                <div class="flex items-center gap-2 mt-1">
                  <span class="px-2 py-0.5 rounded bg-surface-highlight text-text-secondary text-xs">${escapeHtml(
                    client.goal
                  )}</span>
                  <span class="px-2 py-0.5 rounded bg-surface-highlight text-text-secondary text-xs">Demo</span>
                </div>
              </div>
            </div>

            <div class="flex gap-3">
              <button data-action="ai-generate" ${this.aiInFlight ? "disabled" : ""} class="h-10 px-5 rounded-lg bg-surface-highlight text-white text-sm font-bold flex items-center gap-2 transition-colors border border-[#395c46] ${this.aiInFlight ? "opacity-60 cursor-not-allowed" : "hover:bg-[#2f5f3e]"}">
                <span class="material-symbols-outlined text-[18px]">auto_awesome</span>
                ${this.aiInFlight ? "Generating..." : "AI Generate"}
              </button>
              <button data-action="send" class="h-10 px-6 rounded-lg bg-primary hover:bg-opacity-90 text-background-dark text-sm font-bold flex items-center gap-2 transition-colors shadow-[0_0_15px_rgba(19,236,91,0.3)]">
                <span class="material-symbols-outlined text-[18px]">send</span>
                Send to Client
              </button>
            </div>
          </div>
        </header>

        <div class="flex-shrink-0 px-6 pt-4 pb-2">
          <div class="flex items-center justify-between mb-2">
            <span class="text-white font-bold">${escapeHtml(n?.weekLabel || "Week")}</span>
          </div>

          <div class="grid grid-cols-7 gap-2">
            ${DAYS.map((d) => dayBtn({ day: d, active: d === this.day })).join("")}
          </div>
        </div>

        <div class="flex-1 overflow-y-auto p-6 flex flex-col gap-6">
          ${
            n
              ? [
                  mealSection({ mealType: "breakfast", title: "Breakfast", rec: "400-600 kcal", items: n.meals.breakfast }),
                  mealSection({ mealType: "lunch", title: "Lunch", rec: "600-800 kcal", items: n.meals.lunch }),
                  mealSection({ mealType: "dinner", title: "Dinner", rec: "500-700 kcal", items: n.meals.dinner }),
                ].join("")
              : emptyNutritionState()
          }

          <div class="mt-2 p-4 rounded-xl bg-surface-dark border border-surface-highlight">
            <h3 class="text-white text-sm font-bold mb-2 flex items-center gap-2">
              <span class="material-symbols-outlined text-text-secondary text-lg">notes</span>
              Daily Notes
            </h3>
            <textarea data-role="notes" class="w-full bg-surface-darker border border-surface-highlight rounded-lg p-3 text-text-secondary focus:ring-1 focus:ring-primary focus:border-primary outline-none text-sm resize-none" placeholder="Add instructions..." rows="3">${escapeHtml(
              n?.notes || ""
            )}</textarea>
          </div>
        </div>
      </main>

      <aside class="w-96 bg-surface-darker border-l border-surface-highlight flex-shrink-0 flex flex-col h-full">
        <div class="p-5 border-b border-surface-highlight">
          <h3 class="text-white text-lg font-bold mb-4">Quick Add</h3>
          <div class="flex flex-col gap-2">
            ${QUICK_ADD.map((i) => quickAddItem(i)).join("")}
          </div>
        </div>

        <div class="p-5 flex-1 overflow-y-auto">
          <div class="flex items-center justify-between mb-4">
            <h3 class="text-white font-bold">Daily Targets</h3>
            <span class="text-xs text-primary bg-primary/10 px-2 py-1 rounded font-bold">In Progress</span>
          </div>

          <div class="bg-surface-highlight rounded-xl p-5 mb-4 relative overflow-hidden">
            <p class="text-text-secondary text-sm font-medium mb-1">Calories</p>
            <div class="flex items-end gap-2 mb-2">
              <span class="text-3xl font-bold text-white tracking-tight">${totals.kcal}</span>
              <span class="text-text-secondary text-sm mb-1.5">/ ${n?.targets?.kcal || 0} kcal</span>
            </div>
            <div class="w-full h-2 bg-surface-darker rounded-full overflow-hidden">
              <div class="h-full bg-primary rounded-full" style="width: ${
                n?.targets?.kcal ? Math.min(100, Math.round((totals.kcal / n.targets.kcal) * 100)) : 0
              }%"></div>
            </div>
          </div>

          <div class="grid grid-cols-2 gap-3 mb-6">
            ${macroCard({ label: "Protein", value: `${totals.protein}g`, goal: `${n?.targets?.protein || 0}g`, pct: pct(totals.protein, n?.targets?.protein), bar: "bg-blue-400" })}
            ${macroCard({ label: "Carbs", value: `${totals.carbs}g`, goal: `${n?.targets?.carbs || 0}g`, pct: pct(totals.carbs, n?.targets?.carbs), bar: "bg-orange-400" })}
            ${macroCard({ label: "Fats", value: `${totals.fats}g`, goal: `${n?.targets?.fats || 0}g`, pct: pct(totals.fats, n?.targets?.fats), bar: "bg-yellow-400" })}
            ${macroCard({ label: "Water", value: `1.2L`, goal: `${n?.targets?.waterLiters || 0}L`, pct: 40, bar: "bg-cyan-400" })}
          </div>
        </div>
      </aside>
    `;

    this.el.querySelectorAll('[data-action="set-day"]').forEach((btn) => {
      btn.addEventListener("click", () => {
        this.day = btn.dataset.day;
        this.render();
      });
    });

    const aiBtn = this.el.querySelector('[data-action="ai-generate"]');
    if (aiBtn && client) {
      aiBtn.addEventListener("click", async () => {
        const now = Date.now();
        if (now < this.aiCooldownUntil) {
          const secs = Math.max(1, Math.ceil((this.aiCooldownUntil - now) / 1000));
          showToast({
            title: "Please wait",
            message: `AI generation is cooling down (${secs}s).`,
            variant: "danger",
          });
          return;
        }
        if (this.aiInFlight) return;

        try {
          this.aiInFlight = true;
          this.render();
          showToast({ title: "Generating", message: "Requesting AI nutrition plan..." });

          const res = await generatePlan({
            client,
            goal: client.goal,
            type: "nutrition_plan",
            currentPlan: n || null,
          });

          if (res && res.plan) {
            store.setNutritionPlan({ clientId: client.id, nutrition: res.plan });
            if (res.fallback) {
              const warn = res.warning ? String(res.warning) : "";
              showToast({
                title: "Fallback plan",
                message: warn
                  ? `AI unavailable (${warn}). Applied a safe default nutrition plan.`
                  : "AI unavailable. Applied a safe default nutrition plan.",
                variant: "success",
              });
            } else {
              showToast({ title: "Updated", message: "AI nutrition plan applied to this client." });
            }
          } else {
            showToast({
              title: "AI response",
              message: "Received text response (no structured plan).",
              variant: "danger",
            });
          }
        } catch (e) {
          const fallback = buildLocalFallbackNutrition({ client, goal: client.goal });
          store.setNutritionPlan({ clientId: client.id, nutrition: fallback });
          showToast({
            title: "Fallback plan",
            message: `AI unavailable (${e && e.message ? e.message : "Unknown error"}). Applied a safe default nutrition plan.`,
            variant: "success",
          });
        } finally {
          this.aiInFlight = false;
          this.aiCooldownUntil = Date.now() + 5000;
          this.render();
        }
      });
    }

    this.el.querySelectorAll('[data-action="quick-add"]').forEach((btn) => {
      btn.addEventListener("click", () => {
        const payload = JSON.parse(btn.dataset.payload);
        store.addMeal({ clientId: client.id, mealType: "breakfast", item: payload });
        showToast({ title: "Added", message: `Added ${payload.name} to Breakfast.` });
      });
    });

    this.el.querySelectorAll('[data-action="add-meal"]').forEach((btn) => {
      btn.addEventListener("click", () => {
        const mealType = btn.dataset.mealType;
        store.addMeal({
          clientId: client.id,
          mealType,
          item: {
            name: "New meal item",
            desc: "Edit details later",
            kcal: 250,
            protein: 15,
            carbs: 20,
            fats: 8,
          },
        });
        showToast({ title: "Added", message: `Added placeholder item to ${mealType}.` });
      });
    });

    const notes = this.el.querySelector('[data-role="notes"]');
    if (notes) {
      notes.addEventListener("input", () => {
        store.updateNutritionNotes({ clientId: client.id, notes: notes.value });
      });
    }

    const sendBtn = this.el.querySelector('[data-action="send"]');
    if (sendBtn) {
      sendBtn.addEventListener("click", async () => {
        if (!client?.email) {
          showToast({
            title: "Missing email",
            message: "Selected client has no email address in demo data.",
            variant: "danger",
          });
          return;
        }

        const summaryLines = [
          `Client: ${client.name}`,
          `Goal: ${client.goal}`,
          "",
          `Week: ${n?.weekLabel || ""}`,
          `Totals: ${totals.kcal} kcal, P ${totals.protein}g / C ${totals.carbs}g / F ${totals.fats}g`,
          "",
          "Notes:",
          String(n?.notes || "(none)"),
        ];

        try {
          sendBtn.disabled = true;
          await sendEmail({
            to: String(client.email),
            subject: `FitCRM Nutrition Plan – ${client.name}`,
            text: summaryLines.join("\n"),
            fromName: "FitCRM",
          });
          showToast({ title: "Sent", message: "Nutrition summary sent via email." });
        } catch (e) {
          showToast({
            title: "Send failed",
            message: e && e.message ? e.message : "Unknown error",
            variant: "danger",
          });
        } finally {
          sendBtn.disabled = false;
        }
      });
    }
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

function dayBtn({ day, active }) {
  const cls = active
    ? "bg-primary text-background-dark shadow-lg shadow-primary/20 transform scale-105 ring-2 ring-primary ring-offset-2 ring-offset-background-dark"
    : "bg-surface-highlight text-text-secondary hover:bg-opacity-80";

  return `
    <button data-action="set-day" data-day="${escapeAttr(day)}" class="flex flex-col items-center justify-center p-3 rounded-lg ${cls}">
      <span class="text-xs font-bold">${escapeHtml(day)}</span>
    </button>
  `;
}

function mealSection({ mealType, title, rec, items }) {
  return `
    <div class="flex flex-col gap-3">
      <div class="flex items-center justify-between">
        <h3 class="text-white text-lg font-bold flex items-center gap-2">
          <span class="material-symbols-outlined text-primary text-xl">restaurant_menu</span>
          ${escapeHtml(title)}
        </h3>
        <span class="text-text-secondary text-sm">Recommended: ${escapeHtml(rec)}</span>
      </div>

      ${items.map((it) => mealCard(it)).join("")}

      <button data-action="add-meal" data-meal-type="${escapeAttr(
        mealType
      )}" class="w-full py-3 border-2 border-dashed border-surface-highlight rounded-xl text-text-secondary hover:text-primary hover:border-primary hover:bg-surface-highlight/40 transition-all flex items-center justify-center gap-2 font-medium">
        <span class="material-symbols-outlined">add</span>
        Add Meal Item
      </button>
    </div>
  `;
}

function mealCard(it) {
  return `
    <div class="group bg-surface-dark p-4 rounded-xl border border-surface-highlight hover:border-primary/50 transition-all flex items-center justify-between gap-4">
      <div class="flex items-center gap-4">
        <div class="size-12 rounded-lg bg-surface-highlight flex items-center justify-center">
          <span class="material-symbols-outlined text-white">restaurant</span>
        </div>
        <div>
          <h4 class="text-white font-bold text-base">${escapeHtml(it.name)}</h4>
          <p class="text-text-secondary text-xs mt-1">${escapeHtml(it.desc || "")}</p>
          <div class="flex gap-3 mt-2">
            <span class="text-[11px] font-bold text-primary bg-primary/10 px-1.5 py-0.5 rounded">${escapeHtml(
              it.kcal
            )} kcal</span>
            <span class="text-[11px] text-text-secondary">${escapeHtml(it.protein)}g Protein</span>
            <span class="text-[11px] text-text-secondary">${escapeHtml(it.carbs)}g Carbs</span>
          </div>
        </div>
      </div>
    </div>
  `;
}

function quickAddItem(i) {
  return `
    <button data-action="quick-add" data-payload='${escapeAttr(JSON.stringify(i))}' class="text-left flex items-center gap-3 p-2 rounded-lg hover:bg-surface-highlight cursor-pointer group">
      <div class="size-10 rounded bg-surface-highlight flex items-center justify-center">
        <span class="material-symbols-outlined text-text-secondary">add_circle</span>
      </div>
      <div class="flex-1">
        <p class="text-white text-sm font-medium">${escapeHtml(i.name)}</p>
        <p class="text-text-secondary text-xs">${escapeHtml(i.kcal)} kcal</p>
      </div>
      <span class="text-primary opacity-0 group-hover:opacity-100 transition-opacity">
        <span class="material-symbols-outlined">add</span>
      </span>
    </button>
  `;
}

function macroCard({ label, value, goal, pct: pctValue, bar }) {
  const safePct = Math.max(0, Math.min(100, Number.isFinite(pctValue) ? pctValue : 0));

  return `
    <div class="bg-surface-dark p-4 rounded-xl border border-surface-highlight">
      <p class="text-text-secondary text-xs mb-1">${escapeHtml(label)}</p>
      <p class="text-white text-xl font-bold">${escapeHtml(value)}</p>
      <p class="text-xs text-text-secondary mb-2">Goal: ${escapeHtml(goal)}</p>
      <div class="w-full h-1.5 bg-surface-darker rounded-full">
        <div class="h-full ${bar} rounded-full" style="width: ${safePct}%"></div>
      </div>
    </div>
  `;
}

function calcTotals(n) {
  if (!n) return { kcal: 0, protein: 0, carbs: 0, fats: 0 };
  const all = [...(n.meals.breakfast || []), ...(n.meals.lunch || []), ...(n.meals.dinner || [])];
  return all.reduce(
    (acc, it) => {
      acc.kcal += Number(it.kcal || 0);
      acc.protein += Number(it.protein || 0);
      acc.carbs += Number(it.carbs || 0);
      acc.fats += Number(it.fats || 0);
      return acc;
    },
    { kcal: 0, protein: 0, carbs: 0, fats: 0 }
  );
}

function pct(v, goal) {
  if (!goal) return 0;
  return Math.min(100, Math.round((v / goal) * 100));
}

function emptyNutritionState() {
  return `
    <div class="p-6 rounded-xl bg-surface-dark border border-surface-highlight">
      <div class="flex items-center gap-3">
        <span class="material-symbols-outlined text-primary">info</span>
        <div>
          <p class="text-white font-bold">No nutrition data for this client</p>
          <p class="text-text-secondary text-sm">Use Quick Add to start adding items (demo will auto-create a plan).</p>
        </div>
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

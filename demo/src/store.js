const STORAGE_KEY = "fitcrm_demo_state_v1";

function nowIso() {
  return new Date().toISOString();
}

function createDemoState() {
  const clients = [
    {
      id: "c_sarah",
      name: "Sarah Jenkins",
      email: "sarah.j@example.com",
      phone: "+1 (555) 123-4567",
      age: 29,
      city: "New York, NY",
      weightLbs: 145,
      height: "5' 7\"",
      bodyFatPct: 22,
      goal: "Weight Loss",
      plan: "Premium Transformation",
      status: "active",
      lastSeen: "2h ago",
    },
    {
      id: "c_mike",
      name: "Mike Ross",
      email: "mike.r@example.com",
      phone: "+1 (555) 222-3344",
      age: 33,
      city: "Austin, TX",
      weightLbs: 188,
      height: "6' 0\"",
      bodyFatPct: 18,
      goal: "Hypertrophy",
      plan: "Standard Plan",
      status: "active",
      lastSeen: "1d ago",
    },
    {
      id: "c_emily",
      name: "Emily Chen",
      email: "emily.c@example.com",
      phone: "+1 (555) 888-9001",
      age: 27,
      city: "Seattle, WA",
      weightLbs: 132,
      height: "5' 5\"",
      bodyFatPct: 21,
      goal: "Endurance",
      plan: "VIP Plan",
      status: "pending",
      lastSeen: "Yesterday",
    },
  ];

  const tickets = [
    {
      id: "t_001",
      subject: "Macros question",
      from: "Sarah Jenkins <sarah.j@example.com>",
      time: "10m",
      priority: "high",
      status: "new",
      content:
        "Hey, does my macros count include fiber? I'm trying to figure out the dinner for tonight.",
      read: false,
      source: "demo",
      clientId: "c_sarah",
    },
    {
      id: "t_002",
      subject: "Reschedule session",
      from: "Mike Ross <mike.r@example.com>",
      time: "1h",
      priority: "normal",
      status: "assigned",
      content:
        "Can we move Tuesday's session to later in the afternoon? 4pm works best.",
      read: true,
      source: "demo",
      clientId: "c_mike",
    },
    {
      id: "t_003",
      subject: "Check-in completed",
      from: "Emily Chen <emily.c@example.com>",
      time: "Yesterday",
      priority: "low",
      status: "new",
      content: "Completed 'HIIT Cardio' check-in.",
      read: false,
      source: "demo",
      clientId: "c_emily",
    },
  ];

  const conversations = {
    t_001: [
      {
        id: "m_001",
        role: "system",
        text: "Sarah completed 'Glute Focus' workout.",
        ts: "2025-12-19T09:41:00.000Z",
      },
      {
        id: "m_002",
        role: "trainer",
        text: "Great job on hitting that PR last week! For today's session, focus on form over weight. How are you feeling about the new meal prep?",
        ts: "2025-12-19T10:05:00.000Z",
      },
      {
        id: "m_003",
        role: "client",
        text: "Feeling good! The meal prep is easier than I thought. Quick question though...",
        ts: "2025-12-19T10:12:00.000Z",
      },
      {
        id: "m_004",
        role: "client",
        text: "Hey, does my macros count include fiber? I'm trying to figure out the dinner for tonight.",
        ts: "2025-12-19T10:15:00.000Z",
      },
    ],
    t_002: [
      {
        id: "m_005",
        role: "client",
        text: "Can we move Tuesday's session to later in the afternoon? 4pm works best.",
        ts: "2025-12-19T09:10:00.000Z",
      },
    ],
    t_003: [
      {
        id: "m_006",
        role: "system",
        text: "Emily completed 'HIIT Cardio' check-in.",
        ts: "2025-12-18T19:15:00.000Z",
      },
    ],
  };

  const trainingPlans = {
    c_sarah: {
      name: "Hypertrophy Block A",
      startDate: "2023-10-24",
      durationWeeks: 4,
      focus: "Hypertrophy (Muscle Growth)",
      days: {
        mon: {
          title: "Push Day (Chest/Triceps)",
          isRest: false,
          items: [
            { id: "ex_bench", name: "Barbell Bench Press", sets: 4, reps: "8-10", rpe: 8 },
            { id: "ex_incline", name: "Incline DB Press", sets: 3, reps: "12", rpe: 9 },
          ],
        },
        tue: {
          title: "Pull Day (Back/Biceps)",
          isRest: false,
          items: [{ id: "ex_deadlift", name: "Deadlift", sets: 3, reps: "5", rpe: 8 }],
        },
        wed: {
          title: "Active Recovery",
          isRest: true,
          items: [],
        },
        thu: {
          title: "Leg Day",
          isRest: false,
          items: [],
        },
      },
    },
  };

  const nutrition = {
    c_sarah: {
      weekLabel: "Oct 23 - Oct 29, 2023",
      day: "Tue",
      meals: {
        breakfast: [
          {
            id: "meal_oats",
            name: "Overnight Oats & Berries",
            desc: "1 cup oats, 1/2 cup blueberries, chia seeds",
            kcal: 350,
            protein: 12,
            carbs: 45,
            fats: 10,
          },
        ],
        lunch: [
          {
            id: "meal_chicken",
            name: "Grilled Chicken Quinoa Bowl",
            desc: "Chicken breast, quinoa, avocado, spinach",
            kcal: 520,
            protein: 42,
            carbs: 35,
            fats: 18,
          },
        ],
        dinner: [],
      },
      notes: "",
      targets: { kcal: 2150, protein: 180, carbs: 220, fats: 65, waterLiters: 3.5 },
    },
  };

  return {
    version: "0.1.0",
    createdAt: nowIso(),
    ui: {
      selectedClientId: "c_sarah",
      selectedTicketId: "t_001",
    },
    clients,
    tickets,
    conversations,
    trainingPlans,
    nutrition,
  };
}

function loadState() {
  try {
    const raw = localStorage.getItem(STORAGE_KEY);
    if (!raw) return null;
    return JSON.parse(raw);
  } catch {
    return null;
  }
}

function saveState(state) {
  localStorage.setItem(STORAGE_KEY, JSON.stringify(state));
}

function normalizeTrainingPlans(state) {
  const s = state && typeof state === "object" ? state : null;
  if (!s || !s.trainingPlans || typeof s.trainingPlans !== "object") return;

  const order = ["mon", "tue", "wed", "thu"];

  for (const clientId of Object.keys(s.trainingPlans)) {
    const plan = s.trainingPlans[clientId];
    if (!plan || typeof plan !== "object") continue;
    if (!plan.days || typeof plan.days !== "object") plan.days = {};

    for (const dayKey of order) {
      const day = plan.days[dayKey] && typeof plan.days[dayKey] === "object" ? plan.days[dayKey] : { items: [] };
      const items = Array.isArray(day.items) ? day.items : [];
      const srcIsRest = typeof day.isRest === "boolean" ? day.isRest : null;
      const isRest = srcIsRest !== null ? srcIsRest : dayKey === "wed" && items.length === 0;

      day.isRest = isRest;
      day.title = String(day.title || (isRest ? "Active Recovery" : "Workout"));

      if (isRest) {
        day.items = [];
      } else {
        day.items = items.map((it) => ({
          ...it,
          id: String(it?.id || `ex_${Math.random().toString(16).slice(2)}`),
          name: String(it?.name || "Exercise"),
          sets: Number(it?.sets || 3),
          reps: String(it?.reps || "8-12"),
          rpe: Number(it?.rpe || 8),
        }));
      }

      plan.days[dayKey] = day;
    }
  }
}

export const store = {
  _state: null,
  _listeners: new Set(),

  init() {
    const loaded = loadState();
    this._state = loaded || createDemoState();
    normalizeTrainingPlans(this._state);
    saveState(this._state);
  },

  getState() {
    return this._state;
  },

  subscribe(listener) {
    this._listeners.add(listener);
    return () => this._listeners.delete(listener);
  },

  _emit() {
    for (const l of this._listeners) l(this._state);
    saveState(this._state);
  },

  reset() {
    this._state = createDemoState();
    this._emit();
  },

  selectClient(clientId) {
    this._state.ui.selectedClientId = clientId;
    this._emit();
  },

  selectTicket(ticketId) {
    this._state.ui.selectedTicketId = ticketId;
    const t = this._state.tickets.find((x) => x.id === ticketId);
    if (t) t.read = true;
    this._emit();
  },

  updateTicketStatus(ticketId, status) {
    const t = this._state.tickets.find((x) => x.id === ticketId);
    if (!t) return;
    t.status = status;
    this._emit();
  },

  sendMessage(ticketId, text) {
    const msg = {
      id: `m_${Math.random().toString(16).slice(2)}`,
      role: "trainer",
      text,
      ts: nowIso(),
    };

    if (!this._state.conversations[ticketId]) {
      this._state.conversations[ticketId] = [];
    }

    this._state.conversations[ticketId].push(msg);
    this._emit();
  },

  addExerciseToDay({ clientId, dayKey, exercise }) {
    if (!clientId || !dayKey || !exercise) return;

    if (!this._state.trainingPlans[clientId]) {
      const startDate = new Date().toISOString().slice(0, 10);
      this._state.trainingPlans[clientId] = {
        name: "Training Plan",
        startDate,
        durationWeeks: 4,
        focus: "Draft",
        days: {
          mon: { title: "Workout", isRest: false, items: [] },
          tue: { title: "Workout", isRest: false, items: [] },
          wed: { title: "Active Recovery", isRest: true, items: [] },
          thu: { title: "Workout", isRest: false, items: [] },
        },
      };
    }

    const day = this._state.trainingPlans[clientId].days[dayKey];
    if (!day) return;

    if (day.isRest) {
      day.isRest = false;
      if (!day.title || day.title === "Active Recovery") {
        day.title = "Workout";
      }
    }

    day.items.push({
      id: `ex_${Math.random().toString(16).slice(2)}`,
      name: exercise.name,
      sets: exercise.sets,
      reps: exercise.reps,
      rpe: exercise.rpe,
    });

    this._emit();
  },

  updateTrainingDayTitle({ clientId, dayKey, title }) {
    const plan = this._state.trainingPlans[clientId];
    if (!plan) return;
    const day = plan.days[dayKey];
    if (!day) return;
    day.title = String(title || "");
    this._emit();
  },

  setTrainingDayRest({ clientId, dayKey, isRest }) {
    const plan = this._state.trainingPlans[clientId];
    if (!plan) return;
    const day = plan.days[dayKey];
    if (!day) return;

    const nextIsRest = Boolean(isRest);
    day.isRest = nextIsRest;

    if (nextIsRest) {
      day.items = [];
      if (!day.title || day.title === "Workout") {
        day.title = "Active Recovery";
      }
    } else {
      if (!day.title || day.title === "Active Recovery") {
        day.title = "Workout";
      }
    }

    this._emit();
  },

  updateExercise({ clientId, dayKey, exerciseId, patch }) {
    const plan = this._state.trainingPlans[clientId];
    if (!plan) return;
    const day = plan.days[dayKey];
    if (!day) return;
    const ex = day.items.find((x) => x.id === exerciseId);
    if (!ex) return;
    Object.assign(ex, patch);
    this._emit();
  },

  removeExercise({ clientId, dayKey, exerciseId }) {
    const plan = this._state.trainingPlans[clientId];
    if (!plan) return;
    const day = plan.days[dayKey];
    if (!day) return;
    day.items = day.items.filter((x) => x.id !== exerciseId);
    this._emit();
  },

  setTrainingPlan({ clientId, plan }) {
    if (!clientId || !plan) return;

    const startDate = new Date().toISOString().slice(0, 10);
    const days = {};
    const order = ["mon", "tue", "wed", "thu"];

    for (const dayKey of order) {
      const srcDay = plan.days && plan.days[dayKey] ? plan.days[dayKey] : null;
      const srcItems = srcDay && Array.isArray(srcDay.items) ? srcDay.items : [];

      const srcIsRest = srcDay && typeof srcDay.isRest === "boolean" ? srcDay.isRest : null;
      const isRest = srcIsRest !== null ? srcIsRest : dayKey === "wed" && srcItems.length === 0;

      days[dayKey] = {
        title: (srcDay && srcDay.title) || (isRest ? "Active Recovery" : "Workout"),
        isRest,
        items: isRest
          ? []
          : srcItems.map((it) => ({
              id: `ex_${Math.random().toString(16).slice(2)}`,
              name: String(it.name || "Exercise"),
              sets: Number(it.sets || 3),
              reps: String(it.reps || "8-12"),
              rpe: Number(it.rpe || 8),
            })),
      };
    }

    this._state.trainingPlans[clientId] = {
      name: String(plan.name || "AI Training Plan"),
      startDate,
      durationWeeks: Number(plan.durationWeeks || 4),
      focus: String(plan.focus || "AI Generated"),
      days,
    };

    this._emit();
  },

  addMeal({ clientId, mealType, item }) {
    let n = this._state.nutrition[clientId];
    if (!n) {
      n = {
        weekLabel: "Oct 23 - Oct 29, 2023",
        day: "Tue",
        meals: { breakfast: [], lunch: [], dinner: [] },
        notes: "",
        targets: { kcal: 2100, protein: 170, carbs: 220, fats: 65, waterLiters: 3.5 },
      };
      this._state.nutrition[clientId] = n;
    }
    n.meals[mealType].push({
      ...item,
      id: `meal_${Math.random().toString(16).slice(2)}`,
    });
    this._emit();
  },

  updateNutritionNotes({ clientId, notes }) {
    let n = this._state.nutrition[clientId];
    if (!n) {
      n = {
        weekLabel: "Oct 23 - Oct 29, 2023",
        day: "Tue",
        meals: { breakfast: [], lunch: [], dinner: [] },
        notes: "",
        targets: { kcal: 2100, protein: 170, carbs: 220, fats: 65, waterLiters: 3.5 },
      };
      this._state.nutrition[clientId] = n;
    }
    n.notes = notes;
    this._emit();
  },

  setNutritionPlan({ clientId, nutrition }) {
    if (!clientId || !nutrition) return;

    const safeMeals = (meals) => {
      const m = meals && typeof meals === "object" ? meals : {};
      const norm = (arr) =>
        (Array.isArray(arr) ? arr : []).map((it) => ({
          id: `meal_${Math.random().toString(16).slice(2)}`,
          name: String(it?.name || "Meal"),
          desc: String(it?.desc || ""),
          kcal: Number(it?.kcal || 0),
          protein: Number(it?.protein || 0),
          carbs: Number(it?.carbs || 0),
          fats: Number(it?.fats || 0),
        }));

      return {
        breakfast: norm(m.breakfast),
        lunch: norm(m.lunch),
        dinner: norm(m.dinner),
      };
    };

    const targets = nutrition.targets && typeof nutrition.targets === "object" ? nutrition.targets : {};

    this._state.nutrition[clientId] = {
      weekLabel: String(nutrition.weekLabel || "Week"),
      day: String(nutrition.day || "Tue"),
      meals: safeMeals(nutrition.meals),
      notes: String(nutrition.notes || ""),
      targets: {
        kcal: Number(targets.kcal || 2100),
        protein: Number(targets.protein || 170),
        carbs: Number(targets.carbs || 220),
        fats: Number(targets.fats || 65),
        waterLiters: Number(targets.waterLiters || 3.5),
      },
    };

    this._emit();
  },
};

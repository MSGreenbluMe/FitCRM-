function json(statusCode, body) {
  return {
    statusCode,
    headers: {
      "content-type": "application/json; charset=utf-8",
      "cache-control": "no-store",
      "access-control-allow-origin": "*",
      "access-control-allow-headers": "content-type",
      "access-control-allow-methods": "POST, OPTIONS",
    },
    body: JSON.stringify(body),
  };
}

function buildFallbackNutrition({ client, goal }) {
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

function getRequiredEnv(name) {
  const v = process.env[name];
  if (!v) throw new Error(`Missing env var: ${name}`);
  return v;
}

function safeParseJson(raw) {
  try {
    return { ok: true, value: JSON.parse(raw) };
  } catch (e) {
    return { ok: false, error: e };
  }
}

function extractRetryAfterSeconds(errObj) {
  if (!errObj) return null;
  try {
    if (typeof errObj.retryDelay === "string") {
      const m = errObj.retryDelay.match(/(\d+)s/);
      return m ? Number(m[1]) : null;
    }

    const s = JSON.stringify(errObj);
    const m = s.match(/"retryDelay"\s*:\s*"(\d+)s"/);
    if (m) return Number(m[1]);
    return null;
  } catch {
    return null;
  }
}

function compactGeminiError(errObj, statusCode) {
  if (!errObj || typeof errObj !== "object") return `Gemini HTTP ${statusCode}`;
  const msg = errObj.message ? String(errObj.message) : "Gemini error";
  const code = errObj.code ? String(errObj.code) : String(statusCode || "");
  const status = errObj.status ? String(errObj.status) : "";
  return [code ? `code:${code}` : "", status ? `status:${status}` : "", msg].filter(Boolean).join(" ");
}

function extractJsonObject(text) {
  const s = String(text || "");
  const start = s.indexOf("{");
  const end = s.lastIndexOf("}");
  if (start === -1 || end === -1 || end <= start) return null;
  const candidate = s.slice(start, end + 1);
  const parsed = safeParseJson(candidate);
  return parsed.ok ? parsed.value : null;
}

function buildFallbackPlan({ client, goal }) {
  const g = String(goal || client?.goal || "General Fitness");
  const name = `AI Plan (${g})`;

  return {
    name,
    durationWeeks: 4,
    focus: g,
    days: {
      mon: {
        title: "Upper (Push/Pull)",
        items: [
          { name: "Barbell Bench Press", sets: 4, reps: "6-10", rpe: 8 },
          { name: "Dumbbell Row", sets: 4, reps: "8-12", rpe: 8 },
          { name: "Incline DB Press", sets: 3, reps: "10-12", rpe: 8 },
          { name: "Lat Pulldown", sets: 3, reps: "10-12", rpe: 8 },
        ],
      },
      tue: {
        title: "Lower (Strength)",
        items: [
          { name: "Back Squat", sets: 4, reps: "5-8", rpe: 8 },
          { name: "Romanian Deadlift", sets: 3, reps: "8-10", rpe: 8 },
          { name: "Walking Lunges", sets: 3, reps: "10/leg", rpe: 8 },
          { name: "Calf Raises", sets: 3, reps: "12-15", rpe: 8 },
        ],
      },
      wed: {
        title: "Active Recovery",
        items: [],
      },
      thu: {
        title: "Full Body (Hypertrophy)",
        items: [
          { name: "Deadlift (Technique)", sets: 3, reps: "4-6", rpe: 7 },
          { name: "Pull Ups", sets: 3, reps: "AMRAP", rpe: 8 },
          { name: "Leg Press", sets: 3, reps: "10-12", rpe: 8 },
          { name: "Shoulder Press", sets: 3, reps: "8-12", rpe: 8 },
        ],
      },
    },
  };
}

exports.handler = async (event) => {
  if (event.httpMethod === "OPTIONS") {
    return json(200, { ok: true });
  }

  if (event.httpMethod !== "POST") {
    return json(405, { ok: false, error: "Method not allowed" });
  }

  const parsed = safeParseJson(event.body || "{}");
  if (!parsed.ok) {
    return json(400, { ok: false, error: "Invalid JSON body" });
  }

  const { client, goal, constraints, type, currentPlan } = parsed.value || {};

  if (!client || typeof client !== "object") {
    return json(400, { ok: false, error: "Missing 'client'" });
  }

  const normalizedType = String(type || "training_plan");
  const fallbackPlan =
    normalizedType === "nutrition_plan" ? buildFallbackNutrition({ client, goal }) : buildFallbackPlan({ client, goal });
  const apiKey = process.env.GEMINI_API_KEY;

  const schemaTraining =
    "{\"name\":string,\"durationWeeks\":number,\"focus\":string,\"days\":{\"mon\":{\"title\":string,\"items\":[{\"name\":string,\"sets\":number,\"reps\":string,\"rpe\":number}]},\"tue\":{...},\"wed\":{...},\"thu\":{...}}}";
  const schemaNutrition =
    "{\"weekLabel\":string,\"day\":string,\"meals\":{\"breakfast\":[{\"name\":string,\"desc\":string,\"kcal\":number,\"protein\":number,\"carbs\":number,\"fats\":number}],\"lunch\":[...],\"dinner\":[...]},\"notes\":string,\"targets\":{\"kcal\":number,\"protein\":number,\"carbs\":number,\"fats\":number,\"waterLiters\":number}}";

  const prompt = [
    "You are FitCRM assistant.",
    "Return STRICT JSON only (no markdown, no extra text).",
    normalizedType === "nutrition_plan" ? "Task: generate a simple nutrition plan." : "Task: generate a training plan.",
    "Schema:",
    normalizedType === "nutrition_plan" ? schemaNutrition : schemaTraining,
    normalizedType === "nutrition_plan"
      ? "Provide meals for breakfast/lunch/dinner and realistic macro targets."
      : "Provide 4 days (mon,tue,wed,thu). Wed can be a rest day with empty items.",
    "Client:",
    JSON.stringify(client),
    goal ? `Goal: ${goal}` : "",
    `Type: ${normalizedType}`,
    constraints ? `Constraints: ${JSON.stringify(constraints)}` : "",
    currentPlan ? `Current plan: ${JSON.stringify(currentPlan)}` : "",
  ]
    .filter(Boolean)
    .join("\n");

  try {
    if (!apiKey) {
      return json(200, { ok: true, plan: fallbackPlan, fallback: true, warning: "Missing GEMINI_API_KEY" });
    }

    const url = `https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key=${encodeURIComponent(
      apiKey
    )}`;

    const res = await fetch(url, {
      method: "POST",
      headers: { "content-type": "application/json" },
      body: JSON.stringify({
        contents: [{ parts: [{ text: prompt }] }],
        generationConfig: {
          temperature: 0.4,
          maxOutputTokens: 700,
          responseMimeType: "application/json",
        },
      }),
    });

    const text = await res.text();
    const bodyParsed = safeParseJson(text);

    if (!res.ok) {
      const errObj = bodyParsed.ok && bodyParsed.value ? bodyParsed.value.error : null;
      const retryAfterSeconds = extractRetryAfterSeconds(errObj);
      return json(200, {
        ok: true,
        plan: fallbackPlan,
        fallback: true,
        warning: compactGeminiError(errObj, res.status),
        retryAfterSeconds,
      });
    }

    if (!bodyParsed.ok) {
      return json(200, {
        ok: true,
        plan: fallbackPlan,
        fallback: true,
        warning: "Invalid Gemini response JSON",
      });
    }

    const candidate = bodyParsed.value?.candidates?.[0]?.content?.parts
      ?.map((p) => p.text)
      .filter(Boolean)
      .join("\n");

    const planFromJsonMode = candidate ? safeParseJson(candidate) : { ok: false };
    const plan = planFromJsonMode.ok ? planFromJsonMode.value : extractJsonObject(candidate);

    if (!plan || typeof plan !== "object") {
      return json(200, {
        ok: true,
        plan: fallbackPlan,
        fallback: true,
        warning: "Gemini did not return a valid plan JSON",
      });
    }

    return json(200, { ok: true, plan });
  } catch (e) {
    return json(200, {
      ok: true,
      plan: fallbackPlan,
      fallback: true,
      warning: e && e.message ? e.message : String(e),
    });
  }
};

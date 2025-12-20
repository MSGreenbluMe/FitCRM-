function safeParseJson(raw) {
  try {
    return { ok: true, value: JSON.parse(raw) };
  } catch (e) {
    return { ok: false, error: e };
  }
}

const AI_CACHE_STORAGE_KEY = "fitcrm_ai_cache_v2";
const AI_COOLDOWN_UNTIL_KEY = "fitcrm_ai_cooldown_until_v1";
const inFlight = new Map();
const memCache = new Map();
let globalQueue = Promise.resolve();
let lastAiRequestAt = 0;

function makeCacheKey(url, body) {
  return `${url}::${JSON.stringify(body)}`;
}

function sanitizeGeneratePlanPayload(payload) {
  const p = payload && typeof payload === "object" ? payload : {};
  const client = p.client && typeof p.client === "object" ? p.client : {};
  const currentPlan = p.currentPlan && typeof p.currentPlan === "object" ? p.currentPlan : null;

  return {
    type: String(p.type || ""),
    goal: String(p.goal || client.goal || ""),
    client: {
      id: String(client.id || ""),
      goal: String(client.goal || ""),
    },
    currentPlanMeta: currentPlan
      ? {
          name: String(currentPlan.name || ""),
          focus: String(currentPlan.focus || ""),
          durationWeeks: Number(currentPlan.durationWeeks || 0),
        }
      : null,
  };
}

function loadAiCache() {
  try {
    const raw = localStorage.getItem(AI_CACHE_STORAGE_KEY);
    if (!raw) return {};
    const parsed = JSON.parse(raw);
    return parsed && typeof parsed === "object" ? parsed : {};
  } catch {
    return {};
  }
}

function saveAiCache(obj) {
  try {
    localStorage.setItem(AI_CACHE_STORAGE_KEY, JSON.stringify(obj));
  } catch {
    // ignore
  }
}

function getCooldownUntil() {
  try {
    const raw = localStorage.getItem(AI_COOLDOWN_UNTIL_KEY);
    const n = raw ? Number(raw) : 0;
    return Number.isFinite(n) ? n : 0;
  } catch {
    return 0;
  }
}

function setCooldownUntil(tsMs) {
  try {
    localStorage.setItem(AI_COOLDOWN_UNTIL_KEY, String(Math.max(0, Number(tsMs || 0))));
  } catch {
    // ignore
  }
}

function isQuotaExhaustedMessage(s) {
  const msg = String(s || "").toLowerCase();
  return (
    msg.includes("resource_exhausted") ||
    msg.includes("quota") ||
    msg.includes("exceeded") ||
    msg.includes("429")
  );
}

function enqueueGlobal(fn) {
  const p = globalQueue.then(fn, fn);
  globalQueue = p.catch(() => undefined);
  return p;
}

async function postJson(url, body) {
  const res = await fetch(url, {
    method: "POST",
    headers: { "content-type": "application/json" },
    body: JSON.stringify(body),
  });

  const text = await res.text();
  const parsed = safeParseJson(text);

  if (!res.ok) {
    const message = parsed.ok && parsed.value && parsed.value.error ? parsed.value.error : `HTTP ${res.status}`;
    const detail = parsed.ok && parsed.value && parsed.value.detail ? parsed.value.detail : undefined;
    const err = new Error(detail ? `${message}: ${detail}` : message);
    err.status = res.status;
    err.detail = detail;
    throw err;
  }

  if (!parsed.ok) {
    throw new Error("Invalid JSON response");
  }

  return parsed.value;
}

export async function sendEmail(payload) {
  return postJson("/.netlify/functions/send_email", payload);
}

export async function generatePlan(payload) {
  const url = "/.netlify/functions/generate_plan";
  const ttlMs = 10 * 60 * 1000;
  const key = makeCacheKey(url, sanitizeGeneratePlanPayload(payload));
  const now = Date.now();

  const cooldownUntil = getCooldownUntil();
  if (cooldownUntil && now < cooldownUntil) {
    const secs = Math.max(1, Math.ceil((cooldownUntil - now) / 1000));
    const err = new Error(`AI cooldown active (${secs}s).`);
    err.status = 429;
    err.retryAfterSeconds = secs;
    throw err;
  }

  const mem = memCache.get(key);
  if (mem && now - mem.ts < ttlMs) return mem.value;

  const disk = loadAiCache();
  const hit = disk[key];
  if (hit && hit.ts && now - hit.ts < ttlMs && hit.value) {
    memCache.set(key, { ts: hit.ts, value: hit.value });
    return hit.value;
  }

  if (inFlight.has(key)) return inFlight.get(key);

  const p = enqueueGlobal(async () => {
    const minGapMs = 3000;
    const gap = Date.now() - lastAiRequestAt;
    if (gap > 0 && gap < minGapMs) {
      await new Promise((r) => setTimeout(r, minGapMs - gap));
    }

    let val;
    try {
      val = await postJson(url, payload);
    } catch (e) {
      if (e && e.status === 429) {
        setCooldownUntil(Math.max(getCooldownUntil() || 0, Date.now() + 10 * 60 * 1000));
      }
      throw e;
    }
    lastAiRequestAt = Date.now();

    if (val && val.fallback) {
      const retry = Number(val.retryAfterSeconds || 0);
      const warn = val.warning ? String(val.warning) : "";
      if (retry > 0) {
        setCooldownUntil(Date.now() + retry * 1000);
      } else if (isQuotaExhaustedMessage(warn)) {
        setCooldownUntil(Math.max(getCooldownUntil() || 0, Date.now() + 10 * 60 * 1000));
      }
    }

    memCache.set(key, { ts: Date.now(), value: val });
    const next = loadAiCache();
    next[key] = { ts: Date.now(), value: val };
    saveAiCache(next);
    return val;
  }).finally(() => {
    inFlight.delete(key);
  });

  inFlight.set(key, p);
  return p;
}

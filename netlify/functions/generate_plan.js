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

function extractJsonObject(text) {
  const s = String(text || "");
  const start = s.indexOf("{");
  const end = s.lastIndexOf("}");
  if (start === -1 || end === -1 || end <= start) return null;
  const candidate = s.slice(start, end + 1);
  const parsed = safeParseJson(candidate);
  return parsed.ok ? parsed.value : null;
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

  const apiKey = getRequiredEnv("GEMINI_API_KEY");

  const prompt = [
    "You are FitCRM assistant.",
    "Return STRICT JSON only (no markdown, no extra text).",
    "Schema:",
    "{\"name\":string,\"durationWeeks\":number,\"days\":{\"mon\":{\"title\":string,\"items\":[{\"name\":string,\"sets\":number,\"reps\":string,\"rpe\":number}]},\"tue\":{...},\"wed\":{...},\"thu\":{...}}}",
    "Provide 4 days (mon,tue,wed,thu). Wed can be a rest day with empty items.",
    "Client:",
    JSON.stringify(client),
    goal ? `Goal: ${goal}` : "",
    type ? `Type: ${type}` : "",
    constraints ? `Constraints: ${JSON.stringify(constraints)}` : "",
    currentPlan ? `Current plan: ${JSON.stringify(currentPlan)}` : "",
  ]
    .filter(Boolean)
    .join("\n");

  try {
    const url = `https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key=${encodeURIComponent(
      apiKey
    )}`;

    const res = await fetch(url, {
      method: "POST",
      headers: { "content-type": "application/json" },
      body: JSON.stringify({
        contents: [{ role: "user", parts: [{ text: prompt }] }],
        generationConfig: {
          temperature: 0.4,
          maxOutputTokens: 1200,
        },
      }),
    });

    const text = await res.text();
    const bodyParsed = safeParseJson(text);

    if (!res.ok) {
      return json(500, {
        ok: false,
        error: "Gemini request failed",
        detail:
          bodyParsed.ok && bodyParsed.value && bodyParsed.value.error
            ? JSON.stringify(bodyParsed.value.error)
            : `HTTP ${res.status}`,
      });
    }

    if (!bodyParsed.ok) {
      return json(500, { ok: false, error: "Invalid Gemini response" });
    }

    const candidate = bodyParsed.value?.candidates?.[0]?.content?.parts
      ?.map((p) => p.text)
      .filter(Boolean)
      .join("\n");

    const plan = extractJsonObject(candidate);
    if (!plan) {
      return json(200, { ok: true, planText: candidate || "", plan: null });
    }

    return json(200, { ok: true, plan });
  } catch (e) {
    return json(500, {
      ok: false,
      error: "Plan generation failed",
      detail: e && e.message ? e.message : String(e),
    });
  }
};

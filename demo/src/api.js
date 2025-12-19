function safeParseJson(raw) {
  try {
    return { ok: true, value: JSON.parse(raw) };
  } catch (e) {
    return { ok: false, error: e };
  }
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
  return postJson("/.netlify/functions/generate_plan", payload);
}

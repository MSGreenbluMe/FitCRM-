const nodemailer = require("nodemailer");

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

  const { to, subject, text, html, fromName, replyTo } = parsed.value || {};

  if (!to || typeof to !== "string") {
    return json(400, { ok: false, error: "Missing 'to'" });
  }
  if (!subject || typeof subject !== "string") {
    return json(400, { ok: false, error: "Missing 'subject'" });
  }
  if ((!text || typeof text !== "string") && (!html || typeof html !== "string")) {
    return json(400, { ok: false, error: "Provide either 'text' or 'html'" });
  }

  let transporter;
  try {
    const host = getRequiredEnv("SMTP_HOST");
    const port = Number(getRequiredEnv("SMTP_PORT"));
    const user = getRequiredEnv("SMTP_USER");
    const pass = getRequiredEnv("SMTP_PASS");

    transporter = nodemailer.createTransport({
      host,
      port,
      secure: port === 465,
      auth: { user, pass },
    });

    const from = fromName ? `${fromName} <${user}>` : user;

    const info = await transporter.sendMail({
      from,
      to,
      subject,
      text,
      html,
      replyTo: replyTo || undefined,
    });

    return json(200, {
      ok: true,
      messageId: info.messageId,
    });
  } catch (e) {
    return json(500, {
      ok: false,
      error: "Email send failed",
      detail: e && e.message ? e.message : String(e),
    });
  }
};

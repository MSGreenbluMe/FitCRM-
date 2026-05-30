/**
 * Shared auth guard for backend (data) endpoints.
 *
 * These endpoints expose client PII and let callers mutate stored data, but the
 * static demo frontend never calls them. To avoid shipping an open, public CRUD
 * API the moment the site is deployed, they are gated behind a shared secret:
 *
 *   - If FITCRM_API_TOKEN is NOT set in the environment, the endpoint is
 *     DISABLED (fail closed) and returns 503.
 *   - If it IS set, the caller must send a matching `x-api-token` header,
 *     otherwise the request is rejected with 401.
 *
 * This keeps a fresh Netlify deploy safe by default while leaving the
 * (future) automation backend usable once an owner opts in.
 */

function json(statusCode, body) {
  return {
    statusCode,
    headers: {
      "content-type": "application/json; charset=utf-8",
      "cache-control": "no-store",
    },
    body: JSON.stringify(body),
  };
}

/**
 * Returns a response object when the request should be blocked, or null when
 * the caller is authorized and the handler may proceed.
 */
export function requireApiToken(event) {
  const expected = process.env.FITCRM_API_TOKEN;

  if (!expected) {
    return json(503, {
      ok: false,
      error:
        "This endpoint is disabled. Set the FITCRM_API_TOKEN environment variable to enable it.",
    });
  }

  const headers = (event && event.headers) || {};
  // Netlify lowercases header keys; check a couple of variants defensively.
  const provided = headers["x-api-token"] || headers["X-Api-Token"] || "";

  if (provided !== expected) {
    return json(401, { ok: false, error: "Unauthorized" });
  }

  return null;
}

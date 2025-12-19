exports.handler = async () => {
  return {
    statusCode: 501,
    headers: {
      "content-type": "application/json; charset=utf-8",
      "cache-control": "no-store",
    },
    body: JSON.stringify({
      ok: false,
      error: "Not implemented yet",
      hint: "Implement Gemini call here and store GEMINI_API_KEY in Netlify env vars.",
    }),
  };
};

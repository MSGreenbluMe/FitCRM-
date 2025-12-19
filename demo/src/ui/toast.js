let toastRoot;

function ensureRoot() {
  if (toastRoot) return;
  toastRoot = document.createElement("div");
  toastRoot.className =
    "fixed bottom-6 left-1/2 -translate-x-1/2 z-50 flex flex-col gap-2 items-center";
  document.body.appendChild(toastRoot);
}

export function showToast({ title, message, variant = "success" }) {
  ensureRoot();

  const colors =
    variant === "success"
      ? "border-primary/30 bg-surface-highlight"
      : variant === "danger"
        ? "border-red-500/30 bg-surface-highlight"
        : "border-white/10 bg-surface-highlight";

  const el = document.createElement("div");
  el.className = `max-w-[520px] w-[92vw] border ${colors} shadow-lg rounded-xl px-4 py-3 backdrop-blur`;
  el.innerHTML = `
    <div class="flex gap-3 items-start">
      <div class="mt-0.5">
        <span class="material-symbols-outlined text-primary">check_circle</span>
      </div>
      <div class="flex-1">
        <div class="text-white font-bold text-sm">${escapeHtml(title)}</div>
        <div class="text-text-secondary text-sm mt-0.5">${escapeHtml(message)}</div>
      </div>
      <button class="text-text-secondary hover:text-white" aria-label="Close">
        <span class="material-symbols-outlined">close</span>
      </button>
    </div>
  `;

  const closeBtn = el.querySelector("button");
  closeBtn.addEventListener("click", () => el.remove());

  toastRoot.appendChild(el);

  window.setTimeout(() => {
    el.remove();
  }, 2500);
}

function escapeHtml(s) {
  return String(s)
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#039;");
}

import { Router } from "./router.js";
import { store } from "./store.js";
import { Layout } from "./components/Layout.js";
import { DashboardPage } from "./pages/DashboardPage.js";
import { MailboxPage } from "./pages/MailboxPage.js";
import { ClientsPage } from "./pages/ClientsPage.js";
import { TrainingPlanPage } from "./pages/TrainingPlanPage.js";
import { NutritionPage } from "./pages/NutritionPage.js";

const appEl = document.getElementById("app");

store.init();

const layout = new Layout({
  onNavigate: (path) => {
    window.location.hash = `#${path}`;
  },
});

layout.mount(appEl);

const router = new Router({
  getPath: () => {
    const raw = window.location.hash || "#/dashboard";
    const normalized = raw.startsWith("#") ? raw.slice(1) : raw;
    return normalized.startsWith("/") ? normalized : `/${normalized}`;
  },
});

router.register("/dashboard", () => layout.setPage(new DashboardPage()));
router.register("/mailbox", () => layout.setPage(new MailboxPage()));
router.register("/clients", () => layout.setPage(new ClientsPage()));
router.register("/training-plan", () => layout.setPage(new TrainingPlanPage()));
router.register("/nutrition", () => layout.setPage(new NutritionPage()));

router.register("/", () => {
  window.location.hash = "#/dashboard";
});

router.start();

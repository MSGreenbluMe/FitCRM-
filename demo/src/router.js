export class Router {
  constructor({ getPath }) {
    this.getPath = getPath;
    this.routes = new Map();
    this.onHashChange = this.onHashChange.bind(this);
  }

  register(path, handler) {
    this.routes.set(path, handler);
  }

  start() {
    window.addEventListener("hashchange", this.onHashChange);
    this.onHashChange();
  }

  stop() {
    window.removeEventListener("hashchange", this.onHashChange);
  }

  onHashChange() {
    const path = this.getPath();
    const handler = this.routes.get(path);

    if (handler) {
      handler();
      return;
    }

    const root = this.routes.get("/");
    if (root) root();
  }
}

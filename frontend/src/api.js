// Client delle API Tabula.
// L'URL base si legge da VITE_API_URL, ma può essere sovrascritto a runtime
// (campo nell'header dell'app) e viene ricordato in localStorage.

const DEFAULT_BASE =
  import.meta.env.VITE_API_URL || "http://localhost:9955";

let base = (() => {
  try {
    return localStorage.getItem("tabula-api-url") || DEFAULT_BASE;
  } catch {
    return DEFAULT_BASE;
  }
})();

export function getБaseUrl() {
  return base;
}
export function getBaseUrl() {
  return base;
}
export function setBaseUrl(url) {
  base = url.replace(/\/+$/, "");
  try {
    localStorage.setItem("tabula-api-url", base);
  } catch {}
}

async function request(method, path, body) {
  const opts = { method, headers: {} };
  if (body !== undefined) {
    opts.headers["Content-Type"] = "application/json";
    opts.body = JSON.stringify(body);
  }
  const res = await fetch(`${base}${path}`, opts);
  if (!res.ok) {
    let detail = res.statusText;
    try {
      const j = await res.json();
      detail = j.detail || detail;
    } catch {}
    throw new Error(`${res.status} ${detail}`);
  }
  if (res.status === 204) return null;
  return res.json();
}

// Snapshot completo
export const getState = () => request("GET", "/state");

// Generatore CRUD per una risorsa
function resource(name) {
  return {
    list: (params = {}) => {
      const qs = new URLSearchParams(
        Object.entries(params).filter(([, v]) => v != null && v !== "")
      ).toString();
      return request("GET", `/${name}${qs ? `?${qs}` : ""}`);
    },
    get: (id) => request("GET", `/${name}/${id}`),
    create: (data) => request("POST", `/${name}`, data),
    update: (id, patch) => request("PATCH", `/${name}/${id}`, patch),
    remove: (id) => request("DELETE", `/${name}/${id}`),
  };
}

export const projects = resource("projects");
export const epics = resource("epics");
export const stories = resource("stories");
export const tasks = resource("tasks");
export const agents = resource("agents");

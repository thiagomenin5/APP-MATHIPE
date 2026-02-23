/**
 * Cliente API para ERPNext (Frappe). Uso en SPA con mismo origen (producción)
 * o con proxy en desarrollo (Vite proxy a app.graficamathipe.com.ar).
 * Envía X-Frappe-CSRF-Token en POST para evitar 400 Bad Request.
 */

const API = "/api";

/** Token CSRF para peticiones POST (se obtiene con getSession). */
let csrfToken = null;

export async function login(usr, pwd) {
  const res = await fetch(`${API}/method/login`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ usr, pwd }),
    credentials: "same-origin",
  });
  const data = await res.json().catch(() => ({}));
  if (!res.ok || (data.exc_type && data.exc_type !== "null")) {
    throw new Error(data.message || data.exc || "Error al iniciar sesión");
  }
  csrfToken = null;
  return data;
}

/**
 * Obtiene usuario y token CSRF (GET, no requiere CSRF). Guarda el token para call().
 * @returns {Promise<string|null>} usuario o null si no hay sesión
 */
export async function getSession() {
  const res = await fetch(`${API}/method/mathipe_ui.api.get_session_data`, {
    method: "GET",
    credentials: "same-origin",
  });
  if (!res.ok) return null;
  const data = await res.json().catch(() => ({}));
  const payload = data.message ?? data;
  if (payload && typeof payload === "object") {
    csrfToken = payload.csrf_token ?? null;
    return payload.user ?? null;
  }
  csrfToken = null;
  return null;
}

/** Branding del tenant (público, no requiere sesión). */
export async function getBranding() {
  const res = await fetch(`${API}/method/mathipe_ui.api.get_branding`, {
    method: "GET",
    credentials: "same-origin",
  });
  if (!res.ok) return { display_name: "APP Mathipe", logo_url: null, primary_color: null, support_email: null, timezone: null, currency: "ARS" };
  const data = await res.json().catch(() => ({}));
  const msg = data.message ?? data;
  return msg && typeof msg === "object" ? msg : { display_name: "APP Mathipe", logo_url: null, primary_color: null, support_email: null, timezone: null, currency: "ARS" };
}

export async function call(method, args = {}, options = {}) {
  const { signal } = options;
  const headers = { "Content-Type": "application/json" };
  if (csrfToken) headers["X-Frappe-CSRF-Token"] = csrfToken;
  const res = await fetch(`${API}/method/${method}`, {
    method: "POST",
    headers,
    body: JSON.stringify(args),
    credentials: "same-origin",
    signal,
  });
  const data = await res.json().catch(() => ({}));
  if (!res.ok && data.exc_type) throw new Error(data.message || data.exc || "Error en la API");
  return data;
}

/**
 * Sube un archivo y lo asocia a un documento (ej: Sales Order).
 * @param {File} file - archivo del input
 * @param {{ doctype: string, docname: string, is_private?: 0|1 }} opts
 */
export async function uploadFile(file, opts = {}) {
  const form = new FormData();
  form.append("file", file);
  form.append("doctype", opts.doctype || "");
  form.append("docname", opts.docname || "");
  form.append("is_private", String(opts.is_private ?? 0));
  const headers = {};
  if (csrfToken) headers["X-Frappe-CSRF-Token"] = csrfToken;
  const res = await fetch(`${API}/method/upload_file`, {
    method: "POST",
    headers,
    body: form,
    credentials: "same-origin",
  });
  const data = await res.json().catch(() => ({}));
  if (!res.ok && data.exc_type) throw new Error(data.message || data.exc || "Error al subir");
  return data;
}

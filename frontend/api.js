// Client for /api/v1 (functional design 11). Errors come back as
// {"fout": Dutch text, "code": fixed code}; the UI translates the code.
export const API = "/api/v1";

export class ApiError extends Error {
  constructor(status, body) {
    super(body?.fout || `HTTP ${status}`);
    this.status = status;
    this.code = body?.code || "error";
    this.body = body || {};
  }
}

export async function request(method, path, body, { fetchImpl = fetch } = {}) {
  const options = { method, headers: { Accept: "application/json" } };
  if (body !== undefined) {
    options.headers["Content-Type"] = "application/json";
    options.body = JSON.stringify(body);
  }
  const response = await fetchImpl(path.startsWith("/") ? path : `${API}/${path}`, options);
  const data = await response.json().catch(() => null);
  if (!response.ok) throw new ApiError(response.status, data);
  return data;
}

export const get = (path, options) => request("GET", path, undefined, options);
export const post = (path, body = {}, options) => request("POST", path, body, options);
export const patch = (path, body = {}, options) => request("PATCH", path, body, options);
export const put = (path, body = {}, options) => request("PUT", path, body, options);
export const del = (path, body, options) => request("DELETE", path, body, options);

export function query(params) {
  const entries = Object.entries(params).filter(([, value]) => value !== undefined && value !== null && value !== "");
  return entries.length ? "?" + new URLSearchParams(entries).toString() : "";
}

// Paths of a file, a page and an object.
export const filePath = (mid) => `${API}/bestand/${encodeURIComponent(mid)}`;
export const pagePath = (mid, n) => `${filePath(mid)}/pagina/${n}`;
export const objectPath = (mid, n, id) => `${pagePath(mid, n)}/objecten/${encodeURIComponent(id)}`;

// A translated message for an error: the code's text when there is one,
// otherwise the API's own (Dutch) message.
export function errorText(t, error) {
  // The server writes its messages in Dutch, specific to the case: in the Dutch
  // interface they are shown as they are. Otherwise the translation of the code,
  // or a general message, so no Dutch text appears in another language.
  const serverText = error?.body?.fout;
  if (t("meta.language") === "nl" && serverText) return serverText;
  const key = `error.${error.code}`;
  const text = t(key);
  if (text !== key) return text;
  return error instanceof ApiError ? t("error.error") : error.message;
}

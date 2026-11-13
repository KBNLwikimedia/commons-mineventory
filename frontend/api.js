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

// The code of an answer without one of its own (an HTML page of a proxy, a bare 404, a server that
// restarts): by its HTTP status, so the message still says what happened.
const STATUS_CODES = {
  400: "bad_request",
  401: "session_expired",
  403: "forbidden",
  404: "not_found",
  405: "method_not_allowed",
  409: "conflict",
  410: "gone",
  413: "request_too_large",
  429: "too_many_requests",
  500: "server_error",
  502: "server_unavailable",
  503: "server_unavailable",
  504: "server_unavailable",
};
export const statusCode = (status) => STATUS_CODES[status] || (status >= 500 ? "server_error" : "error");

// Only a GET is tried again, and only when the server could not be reached or was briefly away
// (502-504: restarting, a proxy in between). Never a POST, PUT, PATCH or DELETE: a paid call or a
// change must not happen twice.
const RETRY_STATUSES = new Set([502, 503, 504]);
export const RETRY_DELAYS = [600, 1800];
// A GET that has not answered after this long is given up (a paid POST waits as long as it takes:
// stopping it here would not stop the server, and the costs).
export const GET_TIMEOUT = 120000;

const wait = (ms) => new Promise((resolve) => setTimeout(resolve, ms));

/* An error of an aborted request (by the caller, e.g. a newer search): not something to show. */
export const isAbort = (error) => error?.name === "AbortError";

/* The body as JSON: null when empty, {unreadable: true} when it is not JSON (an HTML error page). */
async function readBody(response) {
  if (typeof response.text !== "function") return response.json().catch(() => ({ unreadable: true }));
  const text = await response.text().catch(() => "");
  if (!text.trim()) return null;
  try {
    return JSON.parse(text);
  } catch {
    return { unreadable: true };
  }
}

async function once(method, url, options, { fetchImpl, signal, timeout }) {
  const controller = typeof AbortController === "function" ? new AbortController() : null;
  let timedOut = false;
  const timer = controller && timeout ? setTimeout(() => ((timedOut = true), controller.abort()), timeout) : null;
  const onAbort = () => controller?.abort();
  signal?.addEventListener?.("abort", onAbort);
  try {
    let response;
    try {
      response = await fetchImpl(url, { ...options, ...(controller ? { signal: controller.signal } : {}) });
    } catch (error) {
      if (timedOut) throw new ApiError(0, { code: "timeout" });
      if (isAbort(error) || signal?.aborted) throw error;
      throw new ApiError(0, { code: "network" }); // the server could not be reached at all
    }
    const data = await readBody(response);
    if (timedOut) throw new ApiError(0, { code: "timeout" });
    const json = data && !data.unreadable && typeof data === "object" ? data : null;
    if (!response.ok) throw new ApiError(response.status, { ...(json || {}), code: json?.code || statusCode(response.status) });
    // A 200 that is not JSON (e.g. a login page of a proxy): the action may or may not have happened.
    if (data?.unreadable) throw new ApiError(response.status, { code: "bad_response" });
    return data;
  } finally {
    clearTimeout(timer);
    signal?.removeEventListener?.("abort", onAbort);
  }
}

/* One request to the API. Options: `signal` to abort it, `timeout` (ms; GET only by default),
   `retries` (GET only; default 2). Every failure is an ApiError with a code (network, timeout,
   server_unavailable, …), except an abort by the caller, which stays an AbortError. */
export async function request(method, path, body, { fetchImpl = fetch, signal, timeout, retries, delays = RETRY_DELAYS } = {}) {
  const options = { method, headers: { Accept: "application/json" } };
  if (body !== undefined) {
    options.headers["Content-Type"] = "application/json";
    options.body = JSON.stringify(body);
  }
  const url = path.startsWith("/") ? path : `${API}/${path}`;
  const isGet = method === "GET";
  const tries = 1 + (isGet ? (retries ?? delays.length) : 0);
  for (let attempt = 1; ; attempt += 1) {
    try {
      return await once(method, url, options, { fetchImpl, signal, timeout: timeout ?? (isGet ? GET_TIMEOUT : 0) });
    } catch (error) {
      const again = error instanceof ApiError && (error.code === "network" || RETRY_STATUSES.has(error.status));
      if (!again || attempt >= tries || signal?.aborted) throw error;
      await wait(delays[Math.min(attempt - 1, delays.length - 1)] ?? 0);
    }
  }
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

/* Only the newest of a series counts (two quick searches, page after page, tick after tick):
   `const current = newest()` before the request, `if (!current()) return` after it. */
export function newestOnly() {
  let last = 0;
  return () => {
    const mine = ++last;
    return () => mine === last;
  };
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
  const key = `error.${error?.code}`;
  const text = t(key);
  if (text !== key) return text;
  if (error instanceof ApiError) return t("error.error");
  // The browser could not reach the server at all (e.g. "Failed to fetch"): say so plainly.
  // Another TypeError is a fault in the app itself: no technical English in the interface.
  if (error instanceof TypeError) return /fetch|network|load failed/i.test(error.message) ? t("error.network") : t("error.error");
  return error?.message || t("error.error");
}

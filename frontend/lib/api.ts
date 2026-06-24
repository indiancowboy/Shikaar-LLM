// Thin client for the Shikaar FastAPI backend. The API is the source of truth
// for inventory (so cook-first / meal-plan, which read the server store, stay
// consistent). Swapping to an authenticated DB later is a backend-only change.

import type {
  CandidatesResponse,
  CookFirstResponse,
  FreezerItemCreate,
  FreezerItemRead,
  MealPlanResponse,
  YieldResponse,
} from "./types";

const BASE =
  process.env.NEXT_PUBLIC_API_URL?.replace(/\/$/, "") ?? "http://127.0.0.1:8000";

const ACCESS_KEY_STORAGE = "shikaar_key";
const CLIENT_ID_STORAGE = "shikaar_client";

// Free-tier hosts (Render) sleep when idle and take ~30-60s to wake, returning
// network errors or 502/503/504 during boot. Retry those transparently so a
// cold start looks like a slightly slow load instead of a "can't reach" error.
const TRANSIENT = new Set([502, 503, 504]);
const RETRIES = 8;
const RETRY_DELAY_MS = 3000;

const sleep = (ms: number) => new Promise((r) => setTimeout(r, ms));

// Shared-password header (typed by the user, stored locally — never in the bundle).
function authHeaders(): Record<string, string> {
  if (typeof window === "undefined") return {};
  const k = window.localStorage.getItem(ACCESS_KEY_STORAGE);
  return k ? { "X-Access-Password": k } : {};
}

// Per-browser id so each tester gets a private freezer (generated once, stored locally).
function clientId(): string {
  if (typeof window === "undefined") return "";
  let id = window.localStorage.getItem(CLIENT_ID_STORAGE);
  if (!id) {
    id = window.crypto?.randomUUID?.() ?? `c_${Math.random().toString(36).slice(2)}`;
    window.localStorage.setItem(CLIENT_ID_STORAGE, id);
  }
  return id;
}

async function rawFetch(path: string, init: RequestInit = {}): Promise<Response> {
  const headers = { ...(init.headers || {}), ...authHeaders(), "X-Client-Id": clientId() };
  let lastErr: unknown;
  for (let attempt = 0; attempt <= RETRIES; attempt++) {
    try {
      const res = await fetch(`${BASE}${path}`, { ...init, headers });
      if (TRANSIENT.has(res.status) && attempt < RETRIES) {
        await sleep(RETRY_DELAY_MS);
        continue;
      }
      return res;
    } catch (e) {
      // network error (incl. cold-start connection drop) — retry
      lastErr = e;
      if (attempt < RETRIES) {
        await sleep(RETRY_DELAY_MS);
        continue;
      }
    }
  }
  throw lastErr instanceof Error ? lastErr : new Error("network error");
}

async function asJson<T>(res: Response): Promise<T> {
  if (!res.ok) {
    let detail = res.statusText;
    try {
      const body = await res.json();
      detail = body?.detail ? JSON.stringify(body.detail) : detail;
    } catch {
      /* non-JSON error body */
    }
    throw new Error(`${res.status}: ${detail}`);
  }
  return res.json() as Promise<T>;
}

const jsonHeaders = { "Content-Type": "application/json" };

export const api = {
  // --- access gate ---
  checkAccess: async (): Promise<void> => {
    const r = await rawFetch("/auth/check");
    if (!r.ok) throw new Error(String(r.status));
  },
  setAccessKey: async (key: string): Promise<void> => {
    const r = await rawFetch("/auth/check", { headers: { "X-Access-Password": key } });
    if (!r.ok) throw new Error("invalid");
    if (typeof window !== "undefined") {
      window.localStorage.setItem(ACCESS_KEY_STORAGE, key);
    }
  },

  // --- inventory + features ---
  list: () => rawFetch("/freezer").then(asJson<FreezerItemRead[]>),

  add: (item: FreezerItemCreate) =>
    rawFetch("/freezer", {
      method: "POST",
      headers: jsonHeaders,
      body: JSON.stringify(item),
    }).then(asJson<FreezerItemRead>),

  remove: async (id: string) => {
    const res = await rawFetch(`/freezer/${id}`, { method: "DELETE" });
    if (!res.ok && res.status !== 204) throw new Error(`delete failed: ${res.status}`);
  },

  parseText: (text: string) =>
    rawFetch("/freezer/parse", {
      method: "POST",
      headers: jsonHeaders,
      body: JSON.stringify({ text }),
    }).then(asJson<CandidatesResponse>),

  parseImage: (file: File) => {
    const fd = new FormData();
    fd.append("file", file);
    return rawFetch("/freezer/parse-image", { method: "POST", body: fd }).then(
      asJson<CandidatesResponse>,
    );
  },

  estimateYield: (species: string, weight: number, dressed: boolean) =>
    rawFetch("/freezer/estimate-yield", {
      method: "POST",
      headers: jsonHeaders,
      body: JSON.stringify({ species, weight, dressed }),
    }).then(asJson<YieldResponse>),

  cookFirst: () => rawFetch("/freezer/cook-first").then(asJson<CookFirstResponse>),

  mealPlan: (query?: string) =>
    rawFetch("/freezer/meal-plan", {
      method: "POST",
      headers: jsonHeaders,
      body: JSON.stringify({ query: query ?? null }),
    }).then(asJson<MealPlanResponse>),
};

export { BASE as API_BASE };

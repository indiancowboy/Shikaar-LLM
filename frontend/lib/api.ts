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

// Shared-password header (typed by the user, stored locally — never in the bundle).
function authHeaders(): Record<string, string> {
  if (typeof window === "undefined") return {};
  const k = window.localStorage.getItem(ACCESS_KEY_STORAGE);
  return k ? { "X-Access-Password": k } : {};
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
    const r = await fetch(`${BASE}/auth/check`, { headers: authHeaders() });
    if (!r.ok) throw new Error(String(r.status));
  },
  setAccessKey: async (key: string): Promise<void> => {
    const r = await fetch(`${BASE}/auth/check`, {
      headers: { "X-Access-Password": key },
    });
    if (!r.ok) throw new Error("invalid");
    if (typeof window !== "undefined") {
      window.localStorage.setItem(ACCESS_KEY_STORAGE, key);
    }
  },

  // --- inventory + features ---
  list: () => fetch(`${BASE}/freezer`, { headers: authHeaders() }).then(asJson<FreezerItemRead[]>),

  add: (item: FreezerItemCreate) =>
    fetch(`${BASE}/freezer`, {
      method: "POST",
      headers: { ...jsonHeaders, ...authHeaders() },
      body: JSON.stringify(item),
    }).then(asJson<FreezerItemRead>),

  remove: async (id: string) => {
    const res = await fetch(`${BASE}/freezer/${id}`, {
      method: "DELETE",
      headers: authHeaders(),
    });
    if (!res.ok && res.status !== 204) throw new Error(`delete failed: ${res.status}`);
  },

  parseText: (text: string) =>
    fetch(`${BASE}/freezer/parse`, {
      method: "POST",
      headers: { ...jsonHeaders, ...authHeaders() },
      body: JSON.stringify({ text }),
    }).then(asJson<CandidatesResponse>),

  parseImage: (file: File) => {
    const fd = new FormData();
    fd.append("file", file);
    return fetch(`${BASE}/freezer/parse-image`, {
      method: "POST",
      headers: authHeaders(),
      body: fd,
    }).then(asJson<CandidatesResponse>);
  },

  estimateYield: (species: string, weight: number, dressed: boolean) =>
    fetch(`${BASE}/freezer/estimate-yield`, {
      method: "POST",
      headers: { ...jsonHeaders, ...authHeaders() },
      body: JSON.stringify({ species, weight, dressed }),
    }).then(asJson<YieldResponse>),

  cookFirst: () =>
    fetch(`${BASE}/freezer/cook-first`, { headers: authHeaders() }).then(
      asJson<CookFirstResponse>,
    ),

  mealPlan: (query?: string) =>
    fetch(`${BASE}/freezer/meal-plan`, {
      method: "POST",
      headers: { ...jsonHeaders, ...authHeaders() },
      body: JSON.stringify({ query: query ?? null }),
    }).then(asJson<MealPlanResponse>),
};

export { BASE as API_BASE };

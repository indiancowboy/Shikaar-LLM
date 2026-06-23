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
  list: () => fetch(`${BASE}/freezer`).then(asJson<FreezerItemRead[]>),

  add: (item: FreezerItemCreate) =>
    fetch(`${BASE}/freezer`, {
      method: "POST",
      headers: jsonHeaders,
      body: JSON.stringify(item),
    }).then(asJson<FreezerItemRead>),

  remove: async (id: string) => {
    const res = await fetch(`${BASE}/freezer/${id}`, { method: "DELETE" });
    if (!res.ok && res.status !== 204) throw new Error(`delete failed: ${res.status}`);
  },

  parseText: (text: string) =>
    fetch(`${BASE}/freezer/parse`, {
      method: "POST",
      headers: jsonHeaders,
      body: JSON.stringify({ text }),
    }).then(asJson<CandidatesResponse>),

  parseImage: (file: File) => {
    const fd = new FormData();
    fd.append("file", file);
    return fetch(`${BASE}/freezer/parse-image`, { method: "POST", body: fd }).then(
      asJson<CandidatesResponse>,
    );
  },

  estimateYield: (species: string, weight: number, dressed: boolean) =>
    fetch(`${BASE}/freezer/estimate-yield`, {
      method: "POST",
      headers: jsonHeaders,
      body: JSON.stringify({ species, weight, dressed }),
    }).then(asJson<YieldResponse>),

  cookFirst: () => fetch(`${BASE}/freezer/cook-first`).then(asJson<CookFirstResponse>),

  mealPlan: (query?: string) =>
    fetch(`${BASE}/freezer/meal-plan`, {
      method: "POST",
      headers: jsonHeaders,
      body: JSON.stringify({ query: query ?? null }),
    }).then(asJson<MealPlanResponse>),
};

export { BASE as API_BASE };

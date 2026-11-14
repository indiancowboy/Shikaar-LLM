"use client";

// Last-loaded freezer, kept on this device so the list shows instantly on open
// (then refreshes in the background). Keyed per signed-in user, or per browser
// in demo mode, and cleared on sign out.
import { getSupabase } from "./supabaseClient";
import type { CookFirstResponse, FreezerItemRead } from "./types";

const PREFIX = "shikaar_freezer_v1:";

export interface FreezerSnapshot {
  items: FreezerItemRead[];
  cookFirst: CookFirstResponse | null;
}

/** Storage key for whoever is signed in; "" when there's no one to key by. */
export async function freezerCacheKey(): Promise<string> {
  const supabase = getSupabase();
  if (supabase) {
    const { data } = await supabase.auth.getSession();
    return data.session ? `${PREFIX}u:${data.session.user.id}` : "";
  }
  try {
    return `${PREFIX}c:${window.localStorage.getItem("shikaar_client") ?? "shared"}`;
  } catch {
    return "";
  }
}

export function readFreezerCache(key: string): FreezerSnapshot | null {
  if (!key) return null;
  try {
    const raw = window.localStorage.getItem(key);
    const data = raw ? (JSON.parse(raw) as FreezerSnapshot) : null;
    return data && Array.isArray(data.items) ? data : null;
  } catch {
    return null;
  }
}

export function writeFreezerCache(key: string, snap: FreezerSnapshot): void {
  if (!key) return;
  try {
    window.localStorage.setItem(key, JSON.stringify(snap));
  } catch {
    /* storage full or blocked: the app still works, just without the cache */
  }
}

export function clearFreezerCaches(): void {
  try {
    for (let i = window.localStorage.length - 1; i >= 0; i--) {
      const k = window.localStorage.key(i);
      if (k?.startsWith(PREFIX)) window.localStorage.removeItem(k);
    }
  } catch {
    /* ignore */
  }
}

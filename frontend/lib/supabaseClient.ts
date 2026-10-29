"use client";

// Supabase browser client — only active when the project env vars are set.
// When unset, the app stays in the shared-password demo mode (no accounts).
import { createClient, type SupabaseClient } from "@supabase/supabase-js";

const url = process.env.NEXT_PUBLIC_SUPABASE_URL;
// Accept either name: the Vercel Supabase integration provisions
// NEXT_PUBLIC_SUPABASE_PUBLISHABLE_KEY (new `sb_publishable_` keys).
// Each is referenced literally so Next.js inlines it at build time.
const anon =
  process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY ||
  process.env.NEXT_PUBLIC_SUPABASE_PUBLISHABLE_KEY;

/** True when real accounts are configured (vs the per-browser demo). */
export const isSupabaseConfigured = Boolean(url && anon);

let client: SupabaseClient | null = null;

// Cached access token so the (synchronous) api.ts header builder can attach it
// without awaiting. Kept fresh via onAuthStateChange below.
let accessToken: string | null = null;

export function getSupabase(): SupabaseClient | null {
  if (!isSupabaseConfigured || typeof window === "undefined") return null;
  if (!client) {
    client = createClient(url as string, anon as string, {
      auth: {
        persistSession: true,
        autoRefreshToken: true,
        detectSessionInUrl: true, // completes magic-link / OAuth redirects
      },
    });
    client.auth.getSession().then(({ data }) => {
      accessToken = data.session?.access_token ?? null;
    });
    client.auth.onAuthStateChange((_event, session) => {
      accessToken = session?.access_token ?? null;
    });
  }
  return client;
}

/** The current Supabase access token (JWT), or null. Used by api.ts. */
export function getAccessToken(): string | null {
  return accessToken;
}

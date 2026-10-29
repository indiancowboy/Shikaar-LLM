"use client";

import { useEffect, useState } from "react";
import { api } from "@/lib/api";
import { getSupabase, isSupabaseConfigured } from "@/lib/supabaseClient";

/** Entry gate. In accounts mode (Supabase configured) it requires real sign-in;
 *  otherwise it falls back to the shared-password demo gate. */
export default function Gate({ children }: { children: React.ReactNode }) {
  return isSupabaseConfigured ? (
    <AccountGate>{children}</AccountGate>
  ) : (
    <PasswordGate>{children}</PasswordGate>
  );
}

/* ------------------------------------------------------------- accounts ----- */

type AuthState = "loading" | "signedout" | "signedin";

function AccountGate({ children }: { children: React.ReactNode }) {
  const [state, setState] = useState<AuthState>("loading");
  const [email, setEmail] = useState("");
  const [sent, setSent] = useState(false);
  const [busy, setBusy] = useState(false);
  const [err, setErr] = useState<string | null>(null);

  useEffect(() => {
    const supabase = getSupabase();
    if (!supabase) return;
    supabase.auth.getSession().then(({ data }) => {
      setState(data.session ? "signedin" : "signedout");
    });
    const { data: sub } = supabase.auth.onAuthStateChange((_e, session) => {
      setState(session ? "signedin" : "signedout");
    });
    return () => sub.subscription.unsubscribe();
  }, []);

  const sendLink = async () => {
    setBusy(true);
    setErr(null);
    const supabase = getSupabase();
    const { error } = (await supabase?.auth.signInWithOtp({
      email: email.trim(),
      options: { emailRedirectTo: window.location.origin },
    })) ?? { error: { message: "not configured" } };
    setBusy(false);
    if (error) setErr(error.message);
    else setSent(true);
  };

  const google = async () => {
    setErr(null);
    const { error } =
      (await getSupabase()?.auth.signInWithOAuth({
        provider: "google",
        options: { redirectTo: window.location.origin },
      })) ?? { error: { message: "not configured" } };
    if (error) setErr(error.message);
  };

  const signOut = async () => {
    await getSupabase()?.auth.signOut();
  };

  if (state === "loading") {
    return (
      <div className="wrap">
        <p className="calm" style={{ marginTop: 40 }}>
          <span className="spinner" /> Loading…
        </p>
      </div>
    );
  }

  if (state === "signedout") {
    return (
      <div className="wrap">
        <div className="ask" style={{ maxWidth: 420, margin: "60px auto" }}>
          <h3>
            <span className="dot" />
            Shikaar — Cold Storage
          </h3>
          {sent ? (
            <p>
              Check your email — we sent a sign-in link to <b>{email}</b>. Open it
              on this device. Your freezer syncs across every device you sign in on.
            </p>
          ) : (
            <>
              <p>Sign in to load your freezer. It follows you across your phone and laptop.</p>
              <button className="btn-ask" onClick={google} style={{ width: "100%" }}>
                Continue with Google
              </button>
              <div className="calm" style={{ textAlign: "center", margin: "10px 0" }}>
                or
              </div>
              <div className="field" style={{ marginBottom: 12 }}>
                <label>Email</label>
                <input
                  type="email"
                  value={email}
                  autoFocus
                  onChange={(e) => setEmail(e.target.value)}
                  onKeyDown={(e) => {
                    if (e.key === "Enter" && email.trim()) sendLink();
                  }}
                  placeholder="you@example.com"
                />
              </div>
              <button
                className="btn-ask"
                onClick={sendLink}
                disabled={busy || !email.trim()}
                style={{ width: "100%" }}
              >
                {busy ? <span className="spinner" /> : null}
                Send magic link
              </button>
            </>
          )}
          {err ? <div className="banner-err">{err}</div> : null}
        </div>
      </div>
    );
  }

  return (
    <>
      <div style={{ textAlign: "right", maxWidth: 1040, margin: "8px auto 0", padding: "0 16px" }}>
        <button
          onClick={signOut}
          style={{
            background: "none",
            border: "none",
            color: "inherit",
            opacity: 0.6,
            cursor: "pointer",
            textDecoration: "underline",
            fontSize: 13,
          }}
        >
          Sign out
        </button>
      </div>
      {children}
    </>
  );
}

/* ------------------------------------------------------------- demo gate ---- */

type PwState = "checking" | "need" | "ok";

/** Shared-password gate (demo mode). Unchanged behaviour from before accounts. */
function PasswordGate({ children }: { children: React.ReactNode }) {
  const [state, setState] = useState<PwState>("checking");
  const [pw, setPw] = useState("");
  const [busy, setBusy] = useState(false);
  const [err, setErr] = useState<string | null>(null);

  useEffect(() => {
    api
      .checkAccess()
      .then(() => setState("ok"))
      .catch(() => setState("need"));
  }, []);

  const submit = async () => {
    setBusy(true);
    setErr(null);
    try {
      await api.setAccessKey(pw.trim());
      setState("ok");
    } catch {
      setErr("That password didn't work.");
    } finally {
      setBusy(false);
    }
  };

  if (state === "checking") {
    return (
      <div className="wrap">
        <p className="calm" style={{ marginTop: 40 }}>
          <span className="spinner" /> Connecting… first load can take ~30s while the
          server wakes up.
        </p>
      </div>
    );
  }

  if (state === "need") {
    return (
      <div className="wrap">
        <div className="ask" style={{ maxWidth: 420, margin: "60px auto" }}>
          <h3>
            <span className="dot" />
            Shikaar — Cold Storage
          </h3>
          <p>This demo is password-protected. Enter the shared password to continue.</p>
          <div className="field" style={{ marginBottom: 12 }}>
            <label>Access password</label>
            <input
              type="password"
              value={pw}
              autoFocus
              onChange={(e) => setPw(e.target.value)}
              onKeyDown={(e) => {
                if (e.key === "Enter" && pw.trim()) submit();
              }}
              placeholder="••••••••"
            />
          </div>
          <button className="btn-ask" onClick={submit} disabled={busy || !pw.trim()}>
            {busy ? <span className="spinner" /> : null}
            Enter
          </button>
          {err ? <div className="banner-err">{err}</div> : null}
        </div>
      </div>
    );
  }

  return <>{children}</>;
}

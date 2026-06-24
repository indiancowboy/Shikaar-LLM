"use client";

import { useEffect, useState } from "react";
import { api } from "@/lib/api";

type State = "checking" | "need" | "ok";

/** Shared-password gate. If the backend gate is disabled (local dev), the
 *  access check passes and children render immediately. Otherwise it shows a
 *  password prompt; the entered password is validated server-side and stored
 *  locally — it never lives in the bundle. */
export default function Gate({ children }: { children: React.ReactNode }) {
  const [state, setState] = useState<State>("checking");
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

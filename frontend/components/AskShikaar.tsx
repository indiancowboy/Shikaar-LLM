"use client";

import { useState } from "react";
import { api } from "@/lib/api";

export default function AskShikaar({ hasItems }: { hasItems: boolean }) {
  const [busy, setBusy] = useState(false);
  const [plan, setPlan] = useState<string | null>(null);
  const [err, setErr] = useState<string | null>(null);

  const plan_ = async () => {
    setBusy(true);
    setErr(null);
    try {
      const res = await api.mealPlan();
      setPlan(res.plan);
    } catch (e) {
      setErr(e instanceof Error ? e.message : "Couldn't reach the planner just now.");
    } finally {
      setBusy(false);
    }
  };

  return (
    <div className="ask">
      <h3>
        <span className="dot" />
        Ask Shikaar what to cook
      </h3>
      <p>
        Shikaar reads your manifest, leads with whatever's aging out, and plans around it —
        TBGH-style, routed through the RAG backend.
      </p>
      <button className="btn-ask" onClick={plan_} disabled={busy || !hasItems}>
        {busy ? <span className="spinner" /> : null}
        {hasItems ? "Plan my week" : "Add items to plan"}
      </button>
      {err ? <div className="banner-err">{err}</div> : null}
      {plan ? (
        <div className="answer fade">
          {plan}
          <div className="sig">— Shikaar · planned around your oldest cuts</div>
        </div>
      ) : null}
    </div>
  );
}

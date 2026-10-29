"use client";

import { Fragment, useState } from "react";
import { api } from "@/lib/api";
import { pretty } from "@/lib/format";
import type { FreezerItemRead, Meal, MealPlanResponse } from "@/lib/types";

export default function AskShikaar({ items }: { items: FreezerItemRead[] }) {
  const [busy, setBusy] = useState(false);
  const [res, setRes] = useState<MealPlanResponse | null>(null);
  const [err, setErr] = useState<string | null>(null);
  const hasItems = items.length > 0;

  const plan_ = async () => {
    setBusy(true);
    setErr(null);
    try {
      setRes(await api.mealPlan());
    } catch (e) {
      setErr(e instanceof Error ? e.message : "Couldn't reach the planner just now.");
    } finally {
      setBusy(false);
    }
  };

  // Label meal ingredients from the plan's own manifest, falling back to the
  // live list (an item may have been used up since the plan was made).
  const byId = new Map<string, FreezerItemRead>();
  for (const it of items) byId.set(it.id, it);
  for (const m of res?.manifest ?? []) byId.set(m.item.id, m.item);

  return (
    <div className="ask">
      <h3>
        <span className="dot" />
        Ask Shikaar what to cook
      </h3>
      <p>
        Shikaar reads your manifest, leads with whatever's aging out, and only reaches for TBGH
        recipes that fit the cuts you actually have — plus a creative riff or two.
      </p>
      <button className="btn-ask" onClick={plan_} disabled={busy || !hasItems}>
        {busy ? <span className="spinner" /> : null}
        {hasItems ? (busy ? "Planning…" : "Plan my week") : "Add items to plan"}
      </button>
      {err ? <div className="banner-err">{err}</div> : null}
      {res && !res.meals?.length ? <div className="answer fade">{res.plan}</div> : null}
      {res?.meals?.length ? (
        <div className="meals fade">
          {res.meals.map((m, i) => (
            <MealCard key={`${m.title}-${i}`} n={i + 1} meal={m} byId={byId} />
          ))}
          <div className="sig">— Shikaar · planned around your oldest cuts</div>
        </div>
      ) : null}
    </div>
  );
}

function MealCard({ n, meal, byId }: { n: number; meal: Meal; byId: Map<string, FreezerItemRead> }) {
  const [open, setOpen] = useState(false);
  const meta = [meal.time, meal.serves ? `serves ${meal.serves}` : null].filter(Boolean).join(" · ");

  return (
    <div className={`meal ${meal.kind}`}>
      <div className="meal-head">
        <div className="meal-n">Meal {n}</div>
        <span className={`meal-badge ${meal.kind}`}>
          {meal.kind === "library" ? "TBGH recipe" : `Creative${meal.cuisine ? ` · ${meal.cuisine}` : ""}`}
        </span>
      </div>
      <div className="meal-title">{meal.title}</div>
      {meta ? <div className="meal-meta">{meta}</div> : null}

      <div className="meal-uses">
        Thaw:{" "}
        {meal.uses
          .map((u) => {
            const it = byId.get(u.item_id);
            const what = it ? `${pretty(it.species)} ${it.cut}` : "freezer item";
            return u.packs ? `${u.packs} ${u.packs === 1 ? "pack" : "packs"} ${what}` : what;
          })
          .join(", ")}
      </div>

      {meal.why ? <p className="meal-why">{meal.why}</p> : null}
      {meal.adaptation ? (
        <div className="meal-adapt">
          <b>Prep:</b> {meal.adaptation}
        </div>
      ) : null}

      <button className="meal-toggle" onClick={() => setOpen((o) => !o)}>
        {open ? "Hide recipe" : "Show recipe"}
      </button>

      {open ? (
        meal.recipe ? (
          <RecipeText text={meal.recipe.text} title={meal.recipe.title} />
        ) : (
          <div className="recipe-text">
            <div className="rt-h">Ingredients</div>
            <ul>
              {meal.ingredients.map((x, i) => (
                <li key={i}>{x}</li>
              ))}
            </ul>
            <div className="rt-h">Steps</div>
            <ol>
              {meal.steps.map((x, i) => (
                <li key={i}>{x.replace(/^\d+[.)]\s*/, "")}</li>
              ))}
            </ol>
          </div>
        )
      ) : null}
    </div>
  );
}

/** Renders a recipe's markdown-ish text safely: headings, list lines, and
 *  **bold** — no raw HTML. */
function RecipeText({ text, title }: { text: string; title: string }) {
  const lines = text.split("\n").map((l) => l.trim());
  return (
    <div className="recipe-text">
      {lines.map((line, i) => {
        if (!line) return null;
        const h = line.match(/^#{1,6}\s+(.*)$/);
        if (h) {
          if (h[1].trim().toLowerCase() === title.toLowerCase()) return null; // card already shows it
          return <div key={i} className="rt-h">{inline(h[1])}</div>;
        }
        if (/^\*\*[^*]+\*\*:?$/.test(line) || /^(ingredients|preparation|instructions|method|directions)\b:?$/i.test(line)) {
          return <div key={i} className="rt-h">{line.replace(/\*\*/g, "").replace(/:$/, "")}</div>;
        }
        const li = line.match(/^(?:[-*•]|\d+[.)])\s+(.*)$/);
        if (li) return <div key={i} className="rt-li">{inline(li[1])}</div>;
        return <p key={i}>{inline(line)}</p>;
      })}
    </div>
  );
}

function inline(s: string) {
  return s.split(/(\*\*[^*]+\*\*)/g).map((part, i) =>
    part.startsWith("**") && part.endsWith("**") ? (
      <strong key={i}>{part.slice(2, -2)}</strong>
    ) : (
      <Fragment key={i}>{part}</Fragment>
    ),
  );
}

"use client";

import {
  GROUP_LABEL,
  GROUP_ORDER,
  pretty,
  STATUS_FILL,
} from "@/lib/format";
import type { CookFirstResponse, FreezerItemRead } from "@/lib/types";

export function StatStrip({ items }: { items: FreezerItemRead[] }) {
  const lbs = items.filter((i) => i.unit === "lbs").reduce((a, i) => a + i.qty, 0);
  const useSoon = items.filter((i) => i.status === "use_soon" || i.status === "past_prime").length;
  const oldest = items.length ? Math.max(...items.map((i) => i.age_months)) : 0;

  return (
    <div className="stats">
      <div className="stat">
        <div className="n">{lbs.toFixed(1)}</div>
        <div className="l">Lbs stored</div>
      </div>
      <div className={`stat ${useSoon ? "alert" : ""}`}>
        <div className="n">{useSoon}</div>
        <div className="l">Use soon</div>
      </div>
      <div className="stat">
        <div className="n">{oldest.toFixed(1)}</div>
        <div className="l">Oldest (mo)</div>
      </div>
    </div>
  );
}

export function CookFirst({ data }: { data: CookFirstResponse | null }) {
  if (!data || !data.urgent) return null;
  return (
    <>
      <div className="eyebrow">Cook first</div>
      <div className="cookfirst">
        {data.cards.map((card) => (
          <div className={`cfcard s-${card.item.status}`} key={card.item.id}>
            <div className="cfname">
              {pretty(card.item.species)} <span style={{ color: "var(--muted)", fontWeight: 300 }}>/ {pretty(card.item.cut)}</span>
            </div>
            <div className="cfmeta">
              {card.item.status.replace("_", " ").toUpperCase()} · {card.item.age_months.toFixed(1)} mo old
            </div>
            <ul className="cflist">
              {card.suggestions.length ? (
                card.suggestions.map((s) => <li key={s}>{s}</li>)
              ) : (
                <li style={{ color: "var(--muted)" }}>No KB match yet</li>
              )}
            </ul>
          </div>
        ))}
      </div>
    </>
  );
}

function Item({ item, onRemove }: { item: FreezerItemRead; onRemove: (id: string) => void }) {
  const fill = STATUS_FILL[item.status];
  const pctW = Math.min(item.pct * 100, 100);
  return (
    <div className={`item s-${item.status}`}>
      <div>
        <div className="name">
          {pretty(item.species)} <span className="cut">/ {pretty(item.cut)}</span>
        </div>
        <div className="meta">
          <span>
            Frozen <b>{item.date_frozen}</b>
          </span>
          <span>
            <b>{item.age_months.toFixed(1)} mo</b> old
          </span>
          <span>
            {item.storage === "vacuum_sealed" ? "Vac-sealed" : "Wrapped"} · {item.shelf_life_months}mo life
          </span>
        </div>
        <div className="gauge">
          <div className="fill" style={{ width: `${pctW}%`, background: fill }} />
          <div className="notch" style={{ left: `${Math.min(item.pct * 100, 99)}%` }} />
        </div>
        <div className="gaugelbl">
          <span>FRESH</span>
          <span className={`tag ${item.status}`}>{item.status.replace("_", " ").toUpperCase()}</span>
          <span>SPENT</span>
        </div>
      </div>
      <div className="right">
        <div className="qty">
          {item.qty}
          <span className="u"> {item.unit}</span>
        </div>
        <button className="del" onClick={() => onRemove(item.id)}>
          Remove
        </button>
      </div>
    </div>
  );
}

export function InventoryList({
  items,
  onRemove,
}: {
  items: FreezerItemRead[];
  onRemove: (id: string) => void;
}) {
  if (!items.length) {
    return (
      <div className="empty">
        <div className="big">Freezer's empty</div>
        Log your first harvest above to see it work.
      </div>
    );
  }

  const sorted = [...items].sort((a, b) => b.pct - a.pct);
  const groups = GROUP_ORDER.map((status) => ({
    status,
    items: sorted.filter((i) => i.status === status),
  })).filter((g) => g.items.length);

  return (
    <>
      {groups.map((g) => (
        <div key={g.status}>
          <div className="group-head">{GROUP_LABEL[g.status]}</div>
          {g.items.map((item) => (
            <Item key={item.id} item={item} onRemove={onRemove} />
          ))}
        </div>
      ))}
    </>
  );
}

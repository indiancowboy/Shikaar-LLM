"use client";

import { useMemo, useState } from "react";
import CandidateEditor, { type EditableEntry } from "@/components/CandidateEditor";
import { useSpeciesCatalog } from "@/lib/useSpeciesCatalog";
import {
  GROUP_LABEL,
  GROUP_ORDER,
  pretty,
  STATUS_FILL,
} from "@/lib/format";
import type { CookFirstResponse, FreezerItemCreate, FreezerItemRead, SpeciesResponse } from "@/lib/types";

const OTHER = "Other";

/** Species key → catalog group ("Big game", "Waterfowl"…); "Other" if unlisted. */
function groupOf(catalog: SpeciesResponse | null, species: string): string {
  return catalog?.species.find((s) => s.key === species)?.group ?? OTHER;
}

/** Everything the search box looks at, lowercased. */
function haystack(catalog: SpeciesResponse | null, i: FreezerItemRead): string {
  const label = catalog?.species.find((s) => s.key === i.species)?.label ?? "";
  return [pretty(i.species), label, i.species, i.cut, i.harvest_location ?? "", i.notes ?? ""]
    .join(" ")
    .toLowerCase();
}

export type EditItem = (id: string, patch: Partial<FreezerItemCreate>) => Promise<void>;

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

function Item({
  item,
  onRemove,
  onUse,
  onEdit,
}: {
  item: FreezerItemRead;
  onRemove: (id: string) => void;
  onUse: (id: string) => void;
  onEdit: EditItem;
}) {
  const [editing, setEditing] = useState(false);
  const catalog = useSpeciesCatalog();

  if (editing) {
    const entry: EditableEntry = {
      species: item.species, category: item.category, cut: item.cut, qty: item.qty,
      unit: item.unit, storage: item.storage, packs: item.packs ?? null,
      pack_size: item.pack_size ?? null, parsed_offline: false, species_unknown: false,
      date_frozen: item.date_frozen,
      harvest_location: item.harvest_location ?? null, notes: item.notes ?? null,
    };
    return (
      <div className="item-edit">
        <CandidateEditor
          candidate={entry}
          catalog={catalog}
          withDate
          saveLabel="Save"
          onCancel={() => setEditing(false)}
          onSave={async (c) => {
            await onEdit(item.id, {
              species: c.species, category: c.category, cut: c.cut, qty: c.qty, unit: c.unit,
              storage: c.storage, packs: c.packs ?? null, pack_size: c.pack_size ?? null,
              date_frozen: c.date_frozen,
              harvest_location: c.harvest_location ?? null, notes: c.notes ?? null,
            });
            setEditing(false);
          }}
        />
      </div>
    );
  }

  const fill = STATUS_FILL[item.status];
  const pctW = Math.min(item.pct * 100, 100);
  const packed = !!(item.packs && item.pack_size);
  const countable = packed || item.unit === "pkgs";
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
        {item.harvest_location || item.notes ? (
          <div className="item-notes">
            {item.harvest_location ? <span className="loc">📍 {item.harvest_location}</span> : null}
            {item.notes ? <span className="note">{item.notes}</span> : null}
          </div>
        ) : null}
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
        {packed ? (
          <div className="qty">
            {item.packs}
            <span className="u">
              {" "}
              {item.packs === 1 ? "pack" : "packs"} × {item.pack_size} {item.unit}
            </span>
            <div className="qty-total">{Math.round(item.qty * 100) / 100} {item.unit} total</div>
          </div>
        ) : (
          <div className="qty">
            {Math.round(item.qty * 100) / 100}
            <span className="u"> {item.unit}</span>
          </div>
        )}
        <div className="item-actions">
          {countable ? (
            <button className="used" onClick={() => onUse(item.id)}>
              Used 1
            </button>
          ) : null}
          <button className="del" onClick={() => setEditing(true)}>
            Edit
          </button>
          <button className="del" onClick={() => onRemove(item.id)}>
            Remove
          </button>
        </div>
      </div>
    </div>
  );
}

/** "Clear freezer" with an inline are-you-sure step before anything is deleted. */
export function ClearFreezer({ count, onClear }: { count: number; onClear: () => Promise<void> }) {
  const [confirming, setConfirming] = useState(false);
  const [busy, setBusy] = useState(false);

  if (!confirming) {
    return (
      <div className="clear-row">
        <button className="clear-btn" onClick={() => setConfirming(true)}>
          Clear freezer
        </button>
      </div>
    );
  }

  return (
    <div className="clear-confirm">
      <div>
        Delete all {count} {count === 1 ? "item" : "items"} from your freezer? This can&apos;t be undone.
      </div>
      <div className="clear-actions">
        <button className="btn-ghost" onClick={() => setConfirming(false)} disabled={busy}>
          Cancel
        </button>
        <button
          className="clear-yes"
          disabled={busy}
          onClick={async () => {
            setBusy(true);
            try {
              await onClear();
            } finally {
              setBusy(false);
              setConfirming(false);
            }
          }}
        >
          {busy ? <span className="spinner" /> : null}
          Delete all
        </button>
      </div>
    </div>
  );
}

export function InventoryList({
  items,
  onRemove,
  onUse,
  onEdit,
}: {
  items: FreezerItemRead[];
  onRemove: (id: string) => void;
  onUse: (id: string) => void;
  onEdit: EditItem;
}) {
  if (!items.length) {
    return (
      <div className="empty">
        <div className="big">Freezer's empty</div>
        Log your first harvest above to see it work.
      </div>
    );
  }

  return <FilteredList items={items} onRemove={onRemove} onUse={onUse} onEdit={onEdit} />;
}

function FilteredList({
  items,
  onRemove,
  onUse,
  onEdit,
}: {
  items: FreezerItemRead[];
  onRemove: (id: string) => void;
  onUse: (id: string) => void;
  onEdit: EditItem;
}) {
  const catalog = useSpeciesCatalog();
  const [q, setQ] = useState("");
  const [group, setGroup] = useState("");

  // Only offer groups that are actually in the freezer, in catalog order.
  const groupsPresent = useMemo(() => {
    const present = new Set(items.map((i) => groupOf(catalog, i.species)));
    const order = [...(catalog?.groups ?? []), OTHER];
    return order.filter((g) => present.has(g));
  }, [items, catalog]);

  const words = q.trim().toLowerCase().split(/\s+/).filter(Boolean);
  const shown = items.filter((i) => {
    if (group && groupOf(catalog, i.species) !== group) return false;
    if (!words.length) return true;
    const h = haystack(catalog, i);
    return words.every((w) => h.includes(w));
  });
  const filtering = !!(words.length || group);

  const sorted = [...shown].sort((a, b) => b.pct - a.pct);
  const groups = GROUP_ORDER.map((status) => ({
    status,
    items: sorted.filter((i) => i.status === status),
  })).filter((g) => g.items.length);

  return (
    <>
      {items.length > 3 ? (
        <div className="inv-filter">
          <input
            type="search"
            value={q}
            onChange={(e) => setQ(e.target.value)}
            placeholder="Search species, cut, notes…"
            aria-label="Search the freezer"
          />
          {groupsPresent.length > 1 ? (
            <select value={group} onChange={(e) => setGroup(e.target.value)} aria-label="Filter by group">
              <option value="">All</option>
              {groupsPresent.map((g) => (
                <option key={g} value={g}>
                  {g}
                </option>
              ))}
            </select>
          ) : null}
        </div>
      ) : null}
      {filtering ? (
        <div className="inv-count">
          Showing {shown.length} of {items.length}
          <button className="clear-btn" onClick={() => { setQ(""); setGroup(""); }}>
            Clear
          </button>
        </div>
      ) : null}
      {filtering && !shown.length ? <div className="empty">Nothing in the freezer matches that.</div> : null}
      {groups.map((g) => (
        <div key={g.status}>
          <div className="group-head">{GROUP_LABEL[g.status]}</div>
          {g.items.map((item) => (
            <Item key={item.id} item={item} onRemove={onRemove} onUse={onUse} onEdit={onEdit} />
          ))}
        </div>
      ))}
    </>
  );
}

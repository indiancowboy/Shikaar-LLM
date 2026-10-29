"use client";

import { useMemo, useState } from "react";
import type { SpeciesResponse } from "@/lib/types";

/** Species text box with a grouped dropdown. Tap to browse every species under
 *  its group heading; typing narrows the list (labels and aliases). Free text
 *  is always allowed — picking an option just fills in its name. */
export default function SpeciesPicker({
  value,
  onChange,
  catalog,
  placeholder,
}: {
  value: string;
  onChange: (text: string) => void;
  catalog: SpeciesResponse | null;
  placeholder?: string;
}) {
  const [open, setOpen] = useState(false);
  const q = value.toLowerCase().trim();

  const groups = useMemo(() => {
    if (!catalog) return [];
    const hit = (label: string, aliases: string[]) =>
      !q || label.toLowerCase().includes(q) || aliases.some((a) => a.includes(q));
    return catalog.groups
      .map((group) => ({
        group,
        items: catalog.species.filter((s) => s.group === group && hit(s.label, s.aliases)),
      }))
      .filter((g) => g.items.length);
  }, [catalog, q]);

  return (
    <div className="sp-picker">
      <input
        value={value}
        autoComplete="off"
        placeholder={placeholder}
        onFocus={() => setOpen(true)}
        onChange={(e) => {
          onChange(e.target.value);
          setOpen(true);
        }}
        onBlur={() => setTimeout(() => setOpen(false), 150)}
        onKeyDown={(e) => {
          if (e.key === "Escape") setOpen(false);
        }}
      />
      {open && groups.length ? (
        // preventDefault keeps focus in the input so the tap lands on the option
        <div className="sp-panel" onMouseDown={(e) => e.preventDefault()}>
          {groups.map((g) => (
            <div key={g.group}>
              <div className="sp-group">{g.group}</div>
              {g.items.map((s) => (
                <button
                  type="button"
                  key={s.key}
                  className="sp-opt"
                  onClick={() => {
                    onChange(s.label);
                    setOpen(false);
                  }}
                >
                  {s.label}
                </button>
              ))}
            </div>
          ))}
        </div>
      ) : null}
    </div>
  );
}

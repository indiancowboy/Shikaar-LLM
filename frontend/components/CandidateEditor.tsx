"use client";

import { useState } from "react";
import SpeciesPicker from "@/components/SpeciesPicker";
import { CAT_LABEL, pretty, resolveSpecies, speciesKey } from "@/lib/format";
import type { Category, ParseCandidate, SpeciesResponse, Storage, Unit } from "@/lib/types";

const CATEGORY_KEYS = Object.keys(CAT_LABEL) as Category[];

/** Inline editor for one parsed entry before it's added. Same fields and pack
 *  math as manual entry: with packs, the amount is the size of one pack. */
export default function CandidateEditor({
  candidate,
  catalog,
  onSave,
  onCancel,
}: {
  candidate: ParseCandidate;
  catalog: SpeciesResponse | null;
  onSave: (c: ParseCandidate) => void;
  onCancel: () => void;
}) {
  const c = candidate;
  const [speciesText, setSpeciesText] = useState(c.species_unknown ? "" : pretty(c.species));
  const [pickedCat, setPickedCat] = useState<Category | "">(c.species_unknown ? "" : c.category);
  const [cut, setCut] = useState(c.cut);
  const [packs, setPacks] = useState(c.packs ? String(c.packs) : "");
  const [amount, setAmount] = useState(String(c.packs && c.pack_size ? c.pack_size : c.qty));
  const [unit, setUnit] = useState<Unit>(c.unit);
  const [storage, setStorage] = useState<Storage>(c.storage);
  const [err, setErr] = useState<string | null>(null);

  const known = resolveSpecies(catalog?.species ?? [], speciesText);
  const packCount = parseInt(packs, 10) > 0 ? parseInt(packs, 10) : null;

  const save = () => {
    const category = known?.category ?? pickedCat;
    const n = parseFloat(amount);
    if (!speciesText.trim()) return setErr("Pick the animal.");
    if (!category) return setErr("Pick a category for this species.");
    if (!(n > 0)) return setErr(packCount ? "Enter the size of one pack." : "Enter a quantity.");
    if (packCount && unit === "pkgs") return setErr("For packs, give the size of one pack in lbs or kg.");
    onSave({
      ...c,
      species: known ? known.key : speciesKey(speciesText),
      category,
      cut: cut.trim() || "whole / mixed",
      qty: packCount ? packCount * n : n,
      unit,
      storage,
      packs: packCount,
      pack_size: packCount ? n : null,
      species_unknown: false,
    });
  };

  return (
    <div className="cand-edit">
      <div className="cand-grid">
        <div className="field">
          <label>Species</label>
          <SpeciesPicker value={speciesText} onChange={setSpeciesText} catalog={catalog} placeholder="wild hog, elk…" />
          {known ? (
            <div className="species-hint">
              {known.label} · {CAT_LABEL[known.category]}
            </div>
          ) : null}
        </div>
        {speciesText.trim() && !known ? (
          <div className="field">
            <label>Category</label>
            <select value={pickedCat} onChange={(e) => setPickedCat(e.target.value as Category)}>
              <option value="" disabled>
                Pick one…
              </option>
              {CATEGORY_KEYS.map((k) => (
                <option key={k} value={k}>
                  {CAT_LABEL[k]}
                </option>
              ))}
            </select>
          </div>
        ) : null}
        <div className="field">
          <label>Cut</label>
          <input value={cut} onChange={(e) => setCut(e.target.value)} />
        </div>
        <div className="field">
          <label>Packs</label>
          <input type="number" inputMode="numeric" min={1} step={1} value={packs} placeholder="—" onChange={(e) => setPacks(e.target.value)} />
        </div>
        <div className="field">
          <label>{packCount ? "Size per pack" : "Qty"}</label>
          <input type="number" inputMode="decimal" min={0} step={0.25} value={amount} onChange={(e) => setAmount(e.target.value)} />
        </div>
        <div className="field">
          <label>Unit</label>
          <select value={unit} onChange={(e) => setUnit(e.target.value as Unit)}>
            <option value="lbs">lbs</option>
            <option value="kg">kg</option>
            <option value="pkgs">pkgs</option>
          </select>
        </div>
        <div className="field">
          <label>Storage</label>
          <select value={storage} onChange={(e) => setStorage(e.target.value as Storage)}>
            <option value="vacuum_sealed">Vac-sealed</option>
            <option value="wrapped">Wrapped</option>
          </select>
        </div>
      </div>
      {err ? <div className="banner-err">{err}</div> : null}
      <div className="cand-actions">
        <button className="btn-ghost" type="button" onClick={onCancel}>
          Cancel
        </button>
        <button className="btn-log" type="button" onClick={save}>
          Done
        </button>
      </div>
    </div>
  );
}

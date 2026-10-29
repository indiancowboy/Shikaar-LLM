"use client";

import { useEffect, useRef, useState } from "react";
import { api } from "@/lib/api";
import CandidateEditor from "@/components/CandidateEditor";
import SpeciesPicker from "@/components/SpeciesPicker";
import { amountLabel, CAT_LABEL, pretty, resolveSpecies, speciesKey, todayISO } from "@/lib/format";
import type { Category, ParseCandidate, SpeciesResponse, Storage, Unit } from "@/lib/types";

type Mode = "text" | "animal";

export default function AddToFreezer({ onChanged }: { onChanged: () => void }) {
  const [mode, setMode] = useState<Mode>("text");
  const [text, setText] = useState("");
  const [species, setSpecies] = useState("black bear");
  const [weight, setWeight] = useState("300");
  const [dressed, setDressed] = useState(false);

  const [busy, setBusy] = useState(false);
  const [err, setErr] = useState<string | null>(null);
  const [candidates, setCandidates] = useState<ParseCandidate[] | null>(null);
  const [offline, setOffline] = useState(false);
  const [note, setNote] = useState<string | null>(null);
  const [editing, setEditing] = useState<number | null>(null);
  const [whichText, setWhichText] = useState("");
  const [whichCat, setWhichCat] = useState<Category | "">("");
  const fileRef = useRef<HTMLInputElement>(null);
  const [catalog, setCatalog] = useState<SpeciesResponse | null>(null);

  useEffect(() => {
    api.species().then(setCatalog).catch(() => setCatalog(null));
  }, []);

  async function run(fn: () => Promise<void>) {
    setBusy(true);
    setErr(null);
    try {
      await fn();
    } catch (e) {
      setErr(e instanceof Error ? e.message : "Something went wrong.");
    } finally {
      setBusy(false);
    }
  }

  const parseText = () =>
    run(async () => {
      if (!text.trim()) {
        setErr("Type what you put away first.");
        return;
      }
      const res = await api.parseText(text);
      showCandidates(res.candidates);
      setOffline(res.parsed_offline);
      setNote(null);
    });

  const parseImage = (file: File) =>
    run(async () => {
      // Whatever's typed in the box rides along as a note ("wild hog").
      const res = await api.parseImage(file, text.trim() || undefined);
      if (!res.candidates.length) {
        setErr("Couldn't read that photo — try a clearer shot or use the manual form.");
        return;
      }
      showCandidates(res.candidates);
      setOffline(res.parsed_offline);
      setNote(null);
    });

  const estimate = () =>
    run(async () => {
      const lbs = parseFloat(weight);
      if (!(lbs > 0)) {
        setErr("Enter the animal's weight in lbs.");
        return;
      }
      const res = await api.estimateYield(species, lbs, dressed);
      showCandidates(res.candidates);
      setOffline(false);
      setNote(`${res.note} ~${res.edible_lbs} lbs edible from a ${weight} lb ${pretty(res.species)}.`);
    });

  // New results: reset the review helpers.
  const showCandidates = (cs: ParseCandidate[] | null) => {
    setCandidates(cs);
    setEditing(null);
    setWhichText("");
    setWhichCat("");
  };

  const unknownCount = candidates?.filter((c) => c.species_unknown).length ?? 0;
  const which = resolveSpecies(catalog?.species ?? [], whichText);

  // "Which animal is this?" -> fill every entry the parser couldn't place.
  const applyWhich = () => {
    const category = which?.category ?? whichCat;
    if (!whichText.trim() || !category) {
      setErr(whichText.trim() ? "Pick a category for this species." : "Pick the animal first.");
      return;
    }
    const key = which ? which.key : speciesKey(whichText);
    setErr(null);
    setCandidates((cs) =>
      cs ? cs.map((c) => (c.species_unknown ? { ...c, species: key, category, species_unknown: false } : c)) : cs,
    );
  };

  const dropCandidate = (i: number) => {
    setEditing(null);
    setCandidates((cs) => (cs ? cs.filter((_, idx) => idx !== i) : cs));
  };

  const commit = () =>
    run(async () => {
      if (!candidates) return;
      if (candidates.some((c) => c.species_unknown)) {
        setErr("Pick the animal for every entry first.");
        return;
      }
      const frozen = todayISO();
      for (const c of candidates) {
        await api.add({
          species: c.species,
          category: c.category,
          cut: c.cut,
          qty: c.qty,
          unit: c.unit,
          storage: c.storage,
          date_frozen: frozen,
          packs: c.packs ?? null,
          pack_size: c.pack_size ?? null,
        });
      }
      showCandidates(null);
      setText("");
      setNote(null);
      onChanged();
    });

  return (
    <>
      <div className="eyebrow">Add to freezer</div>
      <div className="quicklog">
        <div className="row">
          <textarea
            value={text}
            onChange={(e) => setText(e.target.value)}
            placeholder='Just say it — "processed a whitetail, two backstraps, ~8 lbs ground, all vac-sealed"'
          />
          <div className="quicklog-actions">
            <button className="btn-parse" onClick={parseText} disabled={busy}>
              {busy ? <span className="spinner" /> : null}
              Parse it
            </button>
            <button className="btn-file" onClick={() => fileRef.current?.click()} disabled={busy}>
              Photo
            </button>
            <input
              ref={fileRef}
              type="file"
              accept="image/*"
              hidden
              onChange={(e) => {
                const f = e.target.files?.[0];
                if (f) parseImage(f);
                e.target.value = "";
              }}
            />
          </div>
        </div>
        <div className="hint">
          Shikaar reads plain language or a photo of a cut sheet — sorts out species · cut ·
          quantity · storage, and shows you the entries before anything's logged. Photo of a
          cut sheet? Type the animal first (e.g. "wild hog") and it goes along with the photo.
        </div>

        <div className="divider">or estimate from an animal</div>
        <div className="row" style={{ gap: 10, flexWrap: "wrap", alignItems: "end" }}>
          <div className="field" style={{ flex: "1 1 160px" }}>
            <label>Animal / species</label>
            <SpeciesPicker value={species} onChange={setSpecies} catalog={catalog} placeholder="black bear" />
          </div>
          <div className="field" style={{ width: 110 }}>
            <label>Weight (lbs)</label>
            <input
              type="number"
              inputMode="decimal"
              min={1}
              value={weight}
              onChange={(e) => setWeight(e.target.value)}
            />
          </div>
          <div className="field" style={{ width: 130 }}>
            <label>Weight type</label>
            <select value={dressed ? "dressed" : "live"} onChange={(e) => setDressed(e.target.value === "dressed")}>
              <option value="live">Live weight</option>
              <option value="dressed">Field-dressed</option>
            </select>
          </div>
          <button className="btn-parse" onClick={estimate} disabled={busy}>
            Estimate cuts
          </button>
        </div>

        {err ? <div className="banner-err">{err}</div> : null}

        {candidates ? (
          <div className="preview fade">
            <div className="phead">
              Found {candidates.length} {candidates.length === 1 ? "entry" : "entries"} — review, then add
            </div>
            {offline ? (
              <div className="hint warn" style={{ marginBottom: 10 }}>
                Read offline (model was unreachable) — give these a close look before adding.
              </div>
            ) : null}
            {note ? (
              <div className="hint" style={{ marginBottom: 10 }}>
                {note}
              </div>
            ) : null}
            {unknownCount ? (
              <div className="which">
                <div className="which-q">
                  Which animal is this? <span>({unknownCount} {unknownCount === 1 ? "entry" : "entries"})</span>
                </div>
                <div className="which-row">
                  <div className="field" style={{ flex: "1 1 180px" }}>
                    <SpeciesPicker value={whichText} onChange={setWhichText} catalog={catalog} placeholder="wild hog, elk…" />
                    {which ? (
                      <div className="species-hint">
                        {which.label} · {CAT_LABEL[which.category]}
                      </div>
                    ) : null}
                  </div>
                  {whichText.trim() && !which ? (
                    <select value={whichCat} onChange={(e) => setWhichCat(e.target.value as Category)}>
                      <option value="" disabled>
                        Category…
                      </option>
                      {(Object.keys(CAT_LABEL) as Category[]).map((k) => (
                        <option key={k} value={k}>
                          {CAT_LABEL[k]}
                        </option>
                      ))}
                    </select>
                  ) : null}
                  <button className="btn-log" type="button" onClick={applyWhich}>
                    Apply
                  </button>
                </div>
              </div>
            ) : null}
            {candidates.map((c, i) =>
              editing === i ? (
                <CandidateEditor
                  key={i}
                  candidate={c}
                  catalog={catalog}
                  onCancel={() => setEditing(null)}
                  onSave={(updated) => {
                    setCandidates((cs) => (cs ? cs.map((x, j) => (j === i ? updated : x)) : cs));
                    setEditing(null);
                  }}
                />
              ) : (
                <div className={`chip ${c.species_unknown ? "unknown" : ""}`} key={i}>
                  <button className="chip-body" type="button" onClick={() => setEditing(i)} title="Edit">
                    <div className="ctxt">
                      {c.species_unknown ? "Unknown animal" : pretty(c.species)} / {pretty(c.cut)}
                    </div>
                    <div className="cmeta">
                      {amountLabel(c)}
                      {c.packs ? ` (${c.qty} ${c.unit})` : ""} ·{" "}
                      {c.storage === "vacuum_sealed" ? "vac-sealed" : "wrapped"}
                      {c.species_unknown ? "" : ` · ${CAT_LABEL[c.category]}`} · <span className="chip-edit">tap to edit</span>
                    </div>
                  </button>
                  <button className="x" onClick={() => dropCandidate(i)} title="Remove">
                    ✕
                  </button>
                </div>
              ),
            )}
            <div className="pacts">
              <button className="btn-ghost" onClick={() => showCandidates(null)} disabled={busy}>
                Discard
              </button>
              <button className="btn-log" onClick={commit} disabled={busy || !candidates.length}>
                {busy ? <span className="spinner" /> : null}
                Add {candidates.length} to freezer
              </button>
            </div>
          </div>
        ) : null}
      </div>

      <ManualEntry onChanged={onChanged} catalog={catalog} />
    </>
  );
}

// Category picker options when the API catalog isn't loaded yet.
const FALLBACK_CATEGORIES = (Object.keys(CAT_LABEL) as Category[]).map((key) => ({
  key,
  label: CAT_LABEL[key],
  hint: "",
}));

function ManualEntry({ onChanged, catalog }: { onChanged: () => void; catalog: SpeciesResponse | null }) {
  const [speciesText, setSpeciesText] = useState("");
  const [pickedCat, setPickedCat] = useState<Category | "">("");
  const [cut, setCut] = useState("");
  const [packs, setPacks] = useState(""); // blank = not packed
  const [qty, setQty] = useState("1");
  const [unit, setUnit] = useState<Unit>("lbs");
  const [storage, setStorage] = useState<Storage>("vacuum_sealed");
  const [date, setDate] = useState(todayISO());
  const [busy, setBusy] = useState(false);
  const [err, setErr] = useState<string | null>(null);

  const packCount = parseInt(packs, 10) > 0 ? parseInt(packs, 10) : null;
  const known = resolveSpecies(catalog?.species ?? [], speciesText);

  const add = async () => {
    const category = known?.category ?? pickedCat;
    if (!speciesText.trim()) {
      setErr("Type a species first.");
      return;
    }
    if (!category) {
      setErr("Pick a category for this species.");
      return;
    }
    const species = known ? known.key : speciesKey(speciesText);
    const amount = parseFloat(qty);
    if (!(amount > 0)) {
      setErr(packCount ? "Enter the size of one pack." : "Enter a quantity.");
      return;
    }
    if (packCount && unit === "pkgs") {
      setErr("For packs, give the size of one pack in lbs or kg.");
      return;
    }
    setBusy(true);
    setErr(null);
    try {
      await api.add({
        species,
        category,
        cut: cut.trim() || "whole / mixed",
        qty: packCount ? packCount * amount : amount,
        unit,
        storage,
        date_frozen: date,
        packs: packCount,
        pack_size: packCount ? amount : null,
      });
      setCut("");
      setSpeciesText("");
      setPickedCat("");
      setPacks("");
      setQty("1");
      onChanged();
    } catch (e) {
      setErr(e instanceof Error ? e.message : "Couldn't add that item.");
    } finally {
      setBusy(false);
    }
  };

  return (
    <>
      <div className="divider">or enter one manually</div>
      <div className="addbar">
        <div className="field">
          <label>Species</label>
          <SpeciesPicker
            value={speciesText}
            onChange={setSpeciesText}
            catalog={catalog}
            placeholder="elk, chicken, walleye…"
          />
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
              {(catalog?.categories ?? FALLBACK_CATEGORIES).map((c) => (
                <option key={c.key} value={c.key}>
                  {c.label}
                  {c.hint ? ` (${c.hint})` : ""}
                </option>
              ))}
            </select>
          </div>
        ) : null}
        <div className="field">
          <label>Cut</label>
          <input value={cut} onChange={(e) => setCut(e.target.value)} placeholder="backstrap, fillet, ground…" />
        </div>
        <div className="field">
          <label>Packs</label>
          <input
            type="number"
            min={1}
            step={1}
            inputMode="numeric"
            value={packs}
            placeholder="—"
            onChange={(e) => setPacks(e.target.value)}
          />
        </div>
        <div className="field">
          <label>{packCount ? "Size per pack" : "Qty"}</label>
          <input
            type="number"
            inputMode="decimal"
            min={0}
            step={0.25}
            value={qty}
            onChange={(e) => setQty(e.target.value)}
          />
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
        <div className="field" style={{ gridColumn: "1 / 3" }}>
          <label>Date frozen</label>
          <input type="date" value={date} max={todayISO()} onChange={(e) => setDate(e.target.value)} />
        </div>
        <div className="addbtn">
          {err ? <div className="banner-err" style={{ margin: 0 }}>{err}</div> : null}
          <button className="btn-log" onClick={add} disabled={busy}>
            Log it
          </button>
        </div>
      </div>
    </>
  );
}

"use client";

import { useRef, useState } from "react";
import { api } from "@/lib/api";
import { CAT_LABEL, pretty, SPECIES_OPTIONS, todayISO } from "@/lib/format";
import type { Category, ParseCandidate, Storage, Unit } from "@/lib/types";

type Mode = "text" | "animal";

export default function AddToFreezer({ onChanged }: { onChanged: () => void }) {
  const [mode, setMode] = useState<Mode>("text");
  const [text, setText] = useState("");
  const [species, setSpecies] = useState("black bear");
  const [weight, setWeight] = useState(300);
  const [dressed, setDressed] = useState(false);

  const [busy, setBusy] = useState(false);
  const [err, setErr] = useState<string | null>(null);
  const [candidates, setCandidates] = useState<ParseCandidate[] | null>(null);
  const [offline, setOffline] = useState(false);
  const [note, setNote] = useState<string | null>(null);
  const fileRef = useRef<HTMLInputElement>(null);

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
      setCandidates(res.candidates);
      setOffline(res.parsed_offline);
      setNote(null);
    });

  const parseImage = (file: File) =>
    run(async () => {
      const res = await api.parseImage(file);
      if (!res.candidates.length) {
        setErr("Couldn't read that photo — try a clearer shot or use the manual form.");
        return;
      }
      setCandidates(res.candidates);
      setOffline(res.parsed_offline);
      setNote(null);
    });

  const estimate = () =>
    run(async () => {
      const res = await api.estimateYield(species, weight, dressed);
      setCandidates(res.candidates);
      setOffline(false);
      setNote(`${res.note} ~${res.edible_lbs} lbs edible from a ${weight} lb ${pretty(res.species)}.`);
    });

  const dropCandidate = (i: number) =>
    setCandidates((cs) => (cs ? cs.filter((_, idx) => idx !== i) : cs));

  const commit = () =>
    run(async () => {
      if (!candidates) return;
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
        });
      }
      setCandidates(null);
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
          quantity · storage, and shows you the entries before anything's logged.
        </div>

        <div className="divider">or estimate from an animal</div>
        <div className="row" style={{ gap: 10, flexWrap: "wrap", alignItems: "end" }}>
          <div className="field" style={{ flex: "1 1 160px" }}>
            <label>Animal / species</label>
            <input value={species} onChange={(e) => setSpecies(e.target.value)} placeholder="black bear" />
          </div>
          <div className="field" style={{ width: 110 }}>
            <label>Weight (lbs)</label>
            <input
              type="number"
              min={1}
              value={weight}
              onChange={(e) => setWeight(parseFloat(e.target.value) || 0)}
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
            {candidates.map((c, i) => (
              <div className="chip" key={i}>
                <div>
                  <div className="ctxt">
                    {pretty(c.species)} / {pretty(c.cut)}
                  </div>
                  <div className="cmeta">
                    {c.qty} {c.unit} · {c.storage === "vacuum_sealed" ? "vac-sealed" : "wrapped"} ·{" "}
                    {CAT_LABEL[c.category]}
                  </div>
                </div>
                <button className="x" onClick={() => dropCandidate(i)} title="Remove">
                  ✕
                </button>
              </div>
            ))}
            <div className="pacts">
              <button className="btn-ghost" onClick={() => setCandidates(null)} disabled={busy}>
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

      <ManualEntry onChanged={onChanged} />
    </>
  );
}

function ManualEntry({ onChanged }: { onChanged: () => void }) {
  const [sel, setSel] = useState("whitetail|biggame");
  const [cut, setCut] = useState("");
  const [qty, setQty] = useState(1);
  const [unit, setUnit] = useState<Unit>("lbs");
  const [storage, setStorage] = useState<Storage>("vacuum_sealed");
  const [date, setDate] = useState(todayISO());
  const [busy, setBusy] = useState(false);
  const [err, setErr] = useState<string | null>(null);

  const add = async () => {
    const [species, category] = sel.split("|") as [string, Category];
    setBusy(true);
    setErr(null);
    try {
      await api.add({
        species,
        category,
        cut: cut.trim() || "whole / mixed",
        qty,
        unit,
        storage,
        date_frozen: date,
      });
      setCut("");
      setQty(1);
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
          <select value={sel} onChange={(e) => setSel(e.target.value)}>
            {SPECIES_OPTIONS.map((g) => (
              <optgroup key={g.group} label={g.group}>
                {g.items.map(([s, label, cat]) => (
                  <option key={s} value={`${s}|${cat}`}>
                    {label}
                  </option>
                ))}
              </optgroup>
            ))}
          </select>
        </div>
        <div className="field">
          <label>Cut</label>
          <input value={cut} onChange={(e) => setCut(e.target.value)} placeholder="backstrap, fillet, ground…" />
        </div>
        <div className="field">
          <label>Qty</label>
          <input type="number" min={0} step={0.25} value={qty} onChange={(e) => setQty(parseFloat(e.target.value) || 0)} />
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

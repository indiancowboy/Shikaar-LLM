import type { Category, SpeciesEntry, Status } from "./types";

export const pretty = (s: string) =>
  s.replace(/_/g, " ").replace(/\b\w/g, (c) => c.toUpperCase());

export const todayISO = () => new Date().toISOString().slice(0, 10);

const num = (n: number) => String(Math.round(n * 100) / 100);

/** "10 packs × 2 lbs" for packed batches, else "8 lbs" / "2 pkgs". */
export const amountLabel = (a: { qty: number; unit: string; packs?: number | null; pack_size?: number | null }) =>
  a.packs && a.pack_size
    ? `${a.packs} ${a.packs === 1 ? "pack" : "packs"} × ${num(a.pack_size)} ${a.unit}`
    : `${num(a.qty)} ${a.unit}`;

export const STATUS_FILL: Record<Status, string> = {
  prime: "var(--prime)",
  good: "var(--good)",
  use_soon: "var(--soon)",
  past_prime: "var(--past)",
};

export const GROUP_ORDER: Status[] = ["past_prime", "use_soon", "good", "prime"];

export const GROUP_LABEL: Record<Status, string> = {
  past_prime: "PAST PRIME — COOK NOW",
  use_soon: "USE SOON",
  good: "GOOD",
  prime: "PRIME",
};

export const CAT_LABEL: Record<Category, string> = {
  biggame: "BIG GAME",
  hog: "HOG / PORK",
  bear: "BEAR",
  waterfowl: "WATERFOWL",
  upland: "UPLAND",
  smallgame: "SMALL GAME",
  poultry: "POULTRY",
  redmeat: "RED MEAT",
  fishlean: "FISH · LEAN",
  fishoily: "FISH · OILY",
  shellfish: "SHELLFISH",
};

const norm = (s: string) => s.toLowerCase().replace(/_/g, " ").replace(/\s+/g, " ").trim();
const escapeRe = (s: string) => s.replace(/[.*+?^${}()|[\]\\]/g, "\\$&");

/** Match typed text to a known species, like the backend: exact key/label/alias,
 *  else the longest alias found as a whole word ("bull elk" -> Elk). */
export function resolveSpecies(list: SpeciesEntry[], text: string): SpeciesEntry | null {
  const t = norm(text);
  if (!t) return null;
  for (const s of list) {
    if (norm(s.key) === t || norm(s.label) === t || s.aliases.includes(t)) return s;
  }
  let best: SpeciesEntry | null = null;
  let bestLen = 0;
  for (const s of list) {
    for (const a of s.aliases) {
      if (a.length > bestLen && new RegExp(`\\b${escapeRe(a)}(?:e?s)?\\b`).test(t)) {
        best = s;
        bestLen = a.length;
      }
    }
  }
  return best;
}

/** Storage key for a species nobody's catalogued yet. */
export const speciesKey = (text: string) => norm(text).replace(/ /g, "_");

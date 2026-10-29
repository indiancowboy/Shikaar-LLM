import type { Category, Status } from "./types";

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
  hog: "HOG",
  bear: "BEAR",
  waterfowl: "WATERFOWL",
  upland: "UPLAND",
  fishlean: "FISH · LEAN",
  fishoily: "FISH · OILY",
  shellfish: "SHELLFISH",
};

// species options for the manual form, value = "species|category" (brief §11).
export const SPECIES_OPTIONS: { group: string; items: [string, string, Category][] }[] = [
  {
    group: "Big game (lean)",
    items: [
      ["whitetail", "Whitetail deer", "biggame"],
      ["mule_deer", "Mule deer", "biggame"],
      ["elk", "Elk", "biggame"],
      ["nilgai", "Nilgai", "biggame"],
      ["antelope", "Antelope", "biggame"],
    ],
  },
  { group: "Bear (fatty)", items: [["black_bear", "Black bear", "bear"]] },
  { group: "Hog (fatty)", items: [["wild_hog", "Wild hog", "hog"]] },
  {
    group: "Waterfowl (fatty)",
    items: [
      ["duck", "Duck", "waterfowl"],
      ["goose", "Goose", "waterfowl"],
      ["teal", "Teal", "waterfowl"],
    ],
  },
  {
    group: "Upland",
    items: [
      ["dove", "Dove", "upland"],
      ["quail", "Quail", "upland"],
      ["pheasant", "Pheasant", "upland"],
      ["turkey", "Wild turkey", "upland"],
    ],
  },
  {
    group: "Fish (lean)",
    items: [
      ["redfish", "Redfish", "fishlean"],
      ["catfish", "Catfish", "fishlean"],
      ["bass", "Bass", "fishlean"],
      ["walleye", "Walleye", "fishlean"],
      ["snapper", "Snapper", "fishlean"],
    ],
  },
  {
    group: "Fish (oily)",
    items: [
      ["salmon", "Salmon", "fishoily"],
      ["mackerel", "Mackerel", "fishoily"],
      ["tuna", "Tuna", "fishoily"],
    ],
  },
  {
    group: "Shellfish",
    items: [
      ["crab", "Crab (Dungeness, blue…)", "shellfish"],
      ["shrimp", "Shrimp / prawns", "shellfish"],
      ["lobster", "Lobster", "shellfish"],
      ["crawfish", "Crawfish", "shellfish"],
      ["scallops", "Scallops", "shellfish"],
      ["clams", "Clams", "shellfish"],
      ["mussels", "Mussels", "shellfish"],
      ["oysters", "Oysters", "shellfish"],
    ],
  },
];

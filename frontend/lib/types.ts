// Mirrors the FastAPI response models (backend/app/models.py + routers/freezer.py).

export type Status = "prime" | "good" | "use_soon" | "past_prime";
export type Category =
  | "biggame" | "hog" | "bear" | "waterfowl" | "upland" | "fishlean" | "fishoily";
export type Unit = "lbs" | "kg" | "pkgs";
export type Storage = "vacuum_sealed" | "wrapped";

export interface FreezerItemCreate {
  species: string;
  category: Category;
  cut: string;
  qty: number;
  unit: Unit;
  storage: Storage;
  date_frozen: string; // ISO date (YYYY-MM-DD)
  harvest_location?: string | null;
  notes?: string | null;
  // Uniform packs: `packs` × `pack_size` (in `unit`); the server derives `qty`.
  packs?: number | null;
  pack_size?: number | null;
}

export interface FreezerItemRead extends FreezerItemCreate {
  id: string;
  status: Status;
  age_months: number;
  pct: number;
  shelf_life_months: number;
}

export interface ParseCandidate {
  species: string;
  category: Category;
  cut: string;
  qty: number;
  unit: Unit;
  storage: Storage;
  packs?: number | null;
  pack_size?: number | null;
  parsed_offline: boolean;
}

export interface UseResponse {
  removed: boolean;
  item: FreezerItemRead | null;
}

export interface CandidatesResponse {
  candidates: ParseCandidate[];
  parsed_offline: boolean;
}

export interface YieldResponse {
  species: string;
  category: Category;
  edible_lbs: number;
  candidates: ParseCandidate[];
  note: string;
}

export interface CookFirstCard {
  item: FreezerItemRead;
  suggestions: string[];
}

export interface CookFirstResponse {
  urgent: boolean;
  cards: CookFirstCard[];
}

export interface MealUse {
  item_id: string;
  packs: number | null;
}

export interface Meal {
  title: string;
  kind: "library" | "creative";
  why: string;
  time: string | null;
  serves: string | null;
  uses: MealUse[];
  adaptation: string | null;
  cuisine: string | null;
  // library meals: the TBGH recipe, verbatim
  recipe: { id: string; title: string; text: string; prep_time: string; cook_time: string } | null;
  // creative meals: model-written recipe
  ingredients: string[];
  steps: string[];
}

export interface MealPlanResponse {
  plan: string;
  meals: Meal[];
  manifest: { item: FreezerItemRead }[];
}

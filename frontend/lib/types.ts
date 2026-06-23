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
  parsed_offline: boolean;
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

export interface MealPlanResponse {
  plan: string;
  manifest: { item: FreezerItemRead }[];
}

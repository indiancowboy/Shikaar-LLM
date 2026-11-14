"use client";

import { useEffect, useState } from "react";
import { api } from "./api";
import type { SpeciesResponse } from "./types";

// One /species request per page load, shared by every component that needs it
// (manual entry, the review editor, freezer-card editors).
let cached: Promise<SpeciesResponse | null> | null = null;

export function useSpeciesCatalog(): SpeciesResponse | null {
  const [catalog, setCatalog] = useState<SpeciesResponse | null>(null);
  useEffect(() => {
    if (!cached) {
      cached = api.species().catch(() => {
        cached = null; // let a later mount retry
        return null;
      });
    }
    let alive = true;
    cached.then((c) => alive && setCatalog(c));
    return () => {
      alive = false;
    };
  }, []);
  return catalog;
}

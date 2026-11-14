// Undo for freezer changes: put items back exactly as they were before a
// "Used 1", "Remove" or "Cook this".

import { api } from "./api";
import type { FreezerItemCreate, FreezerItemRead } from "./types";

/** The writable fields of a saved item. */
export function toCreate(i: FreezerItemRead): FreezerItemCreate {
  return {
    species: i.species,
    category: i.category,
    cut: i.cut,
    qty: i.qty,
    unit: i.unit,
    storage: i.storage,
    date_frozen: i.date_frozen,
    harvest_location: i.harvest_location ?? null,
    notes: i.notes ?? null,
    packs: i.packs ?? null,
    pack_size: i.pack_size ?? null,
  };
}

/** Restore snapshots: write the old fields back if the item still exists,
 *  otherwise (it was removed or used up) add it again. */
export async function restoreItems(snapshots: FreezerItemRead[]): Promise<void> {
  if (!snapshots.length) return;
  const live = new Set((await api.list()).map((i) => i.id));
  for (const s of snapshots) {
    if (live.has(s.id)) await api.update(s.id, toCreate(s));
    else await api.add(toCreate(s));
  }
}

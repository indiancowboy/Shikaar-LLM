"use client";

import { useCallback, useEffect, useState } from "react";
import AddToFreezer from "@/components/AddToFreezer";
import AskShikaar from "@/components/AskShikaar";
import Gate from "@/components/Gate";
import { CookFirst, InventoryList, StatStrip } from "@/components/Inventory";
import { api } from "@/lib/api";
import type { CookFirstResponse, FreezerItemRead } from "@/lib/types";

export default function Page() {
  // Gate renders FreezerHub only after access is granted, so the data fetch
  // never runs (and never 401s) before the password is accepted.
  return (
    <Gate>
      <FreezerHub />
    </Gate>
  );
}

function FreezerHub() {
  const [items, setItems] = useState<FreezerItemRead[]>([]);
  const [cookFirst, setCookFirst] = useState<CookFirstResponse | null>(null);
  const [loadErr, setLoadErr] = useState<string | null>(null);

  const refresh = useCallback(async () => {
    try {
      const [list, cf] = await Promise.all([api.list(), api.cookFirst()]);
      setItems(list);
      setCookFirst(cf);
      setLoadErr(null);
    } catch (e) {
      setLoadErr(
        e instanceof Error
          ? `Can't reach the backend (${e.message}). Is the API running at ${process.env.NEXT_PUBLIC_API_URL ?? "http://127.0.0.1:8000"}?`
          : "Can't reach the backend.",
      );
    }
  }, []);

  useEffect(() => {
    refresh();
  }, [refresh]);

  const remove = async (id: string) => {
    await api.remove(id);
    refresh();
  };

  return (
    <div className="wrap">
      <header className="brand">
        <div>
          <div className="mark">Shikaar · Two Brown Guys Hunt</div>
          <div className="title">Cold Storage</div>
          <div className="sub">FREEZER MANIFEST — species-aware shelf life</div>
        </div>
        <StatStrip items={items} />
      </header>

      {loadErr ? <div className="banner-err">{loadErr}</div> : null}

      <AddToFreezer onChanged={refresh} />

      <CookFirst data={cookFirst} />

      <div className="eyebrow">In the freezer</div>
      <InventoryList items={items} onRemove={remove} />

      <AskShikaar hasItems={items.length > 0} />

      <footer>
        SPECIES-AWARE SHELF LIFE · RAG MEAL PLANNING · TBGH
        <br />
        Shelf-life estimates are guidance, not gospel — trust your nose.
      </footer>
    </div>
  );
}

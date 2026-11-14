"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import AddToFreezer from "@/components/AddToFreezer";
import AskShikaar from "@/components/AskShikaar";
import BuckLoader from "@/components/BuckLoader";
import { ShikaarLogo, TbghCredit } from "@/components/Brand";
import Gate from "@/components/Gate";
import Toast, { type ToastData } from "@/components/Toast";
import { ClearFreezer, CookFirst, InventoryList, StatStrip } from "@/components/Inventory";
import { api } from "@/lib/api";
import { freezerCacheKey, readFreezerCache, writeFreezerCache } from "@/lib/freezerCache";
import { pretty } from "@/lib/format";
import { restoreItems } from "@/lib/undo";
import type { CookFirstResponse, FreezerItemCreate, FreezerItemRead } from "@/lib/types";

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
  const [updating, setUpdating] = useState(false);
  // False until we have a freezer to show (from the cache or the server).
  const [loaded, setLoaded] = useState(false);
  // The free server can take up to a minute to wake; say so if it's slow.
  const [slow, setSlow] = useState(false);
  const cacheKey = useRef<Promise<string> | null>(null);
  const [toast, setToast] = useState<ToastData | null>(null);
  const closeToast = useCallback(() => setToast(null), []);

  const refresh = useCallback(async () => {
    setUpdating(true);
    try {
      const [list, cf] = await Promise.all([api.list(), api.cookFirst()]);
      setItems(list);
      setCookFirst(cf);
      setLoadErr(null);
      setLoaded(true);
      writeFreezerCache(await (cacheKey.current ??= freezerCacheKey()), { items: list, cookFirst: cf });
    } catch (e) {
      setLoadErr(
        e instanceof Error
          ? `Can't reach the backend (${e.message}). Is the API running at ${process.env.NEXT_PUBLIC_API_URL ?? "http://127.0.0.1:8000"}?`
          : "Can't reach the backend.",
      );
    } finally {
      setUpdating(false);
    }
  }, []);

  useEffect(() => {
    // Show the last-loaded freezer straight away, then refresh it.
    let alive = true;
    (cacheKey.current ??= freezerCacheKey()).then((key) => {
      const cached = readFreezerCache(key);
      if (alive && cached) {
        setItems((cur) => (cur.length ? cur : cached.items));
        setCookFirst((cur) => cur ?? cached.cookFirst);
        setLoaded(true);
      }
    });
    refresh();
    const t = setTimeout(() => alive && setSlow(true), 6000);
    return () => {
      alive = false;
      clearTimeout(t);
    };
  }, [refresh]);

  // Show a message; with snapshots, its Undo puts those items back as they were.
  const notify = useCallback(
    (message: string, snapshots: FreezerItemRead[] = []) => {
      const onUndo = snapshots.length
        ? async () => {
            try {
              await restoreItems(snapshots);
            } catch (e) {
              setToast({ id: Date.now(), message: `Couldn't undo: ${e instanceof Error ? e.message : "try again"}` });
            }
            refresh();
          }
        : undefined;
      setToast({ id: Date.now(), message, onUndo });
    },
    [refresh],
  );

  const label = (i: FreezerItemRead) => `${pretty(i.species)} ${pretty(i.cut).toLowerCase()}`;

  const remove = async (id: string) => {
    const snap = items.find((i) => i.id === id);
    try {
      await api.remove(id);
      if (snap) notify(`Removed ${label(snap)}`, [snap]);
    } catch (e) {
      notify(`Couldn't remove that: ${e instanceof Error ? e.message : "try again"}`);
    }
    refresh();
  };

  const clearAll = async () => {
    await api.clear();
    refresh();
  };

  // Errors bubble up so the card's editor can show them.
  const edit = async (id: string, patch: Partial<FreezerItemCreate>) => {
    await api.update(id, patch);
    refresh();
  };

  const use = async (id: string) => {
    const snap = items.find((i) => i.id === id);
    try {
      const res = await api.use(id);
      if (snap) {
        const what = snap.packs && snap.pack_size ? "pack" : "pkg";
        notify(`Used 1 ${what} · ${label(snap)}${res.removed ? " (all gone)" : ""}`, [snap]);
      }
    } catch (e) {
      notify(`Couldn't update that: ${e instanceof Error ? e.message : "try again"}`);
    }
    refresh();
  };

  return (
    <div className="wrap">
      <header className="brand">
        <div>
          <ShikaarLogo className="brand-logo" />
          <div className="title">Cold Storage</div>
          <div className="sub">FREEZER MANIFEST — species-aware shelf life</div>
        </div>
        <StatStrip items={items} />
      </header>

      {loadErr ? <div className="banner-err">{loadErr}</div> : null}

      <AddToFreezer onChanged={refresh} />

      <CookFirst data={cookFirst} />

      <div className="eyebrow">
        In the freezer
        {updating && loaded && items.length ? (
          <span className="updating-buck">
            <BuckLoader size={34} label="updating…" />
          </span>
        ) : null}
      </div>
      {!loaded && !loadErr ? (
        <div className="loading-panel">
          <BuckLoader
            size={130}
            label={slow ? undefined : "Tracking down your freezer…"}
          />
          {slow ? (
            <div className="buck-label" style={{ marginTop: 10 }}>
              Still tracking…
              <small>The server naps when nobody&apos;s using it. First load can take up to a minute.</small>
            </div>
          ) : null}
        </div>
      ) : loaded ? (
        <InventoryList items={items} onRemove={remove} onUse={use} onEdit={edit} />
      ) : null}
      {items.length ? <ClearFreezer count={items.length} onClear={clearAll} /> : null}

      <AskShikaar items={items} onCooked={notify} onChanged={refresh} />

      <TbghCredit />

      <div className="feedback">
        <a href="mailto:info@twobrownguyshunt.com?subject=Shikaar%20feedback">Send feedback</a>
      </div>

      <footer>
        SPECIES-AWARE SHELF LIFE · RAG MEAL PLANNING · TBGH
        <br />
        Shelf-life estimates are guidance, not gospel — trust your nose.
      </footer>

      <Toast toast={toast} onClose={closeToast} />
    </div>
  );
}

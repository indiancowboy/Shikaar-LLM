"use client";

import { useEffect } from "react";

export interface ToastData {
  id: number;
  message: string;
  onUndo?: () => void;
}

/** A small message at the bottom of the screen with an optional Undo. Goes
 *  away on its own after `ms`. */
export default function Toast({
  toast,
  onClose,
  ms = 6000,
}: {
  toast: ToastData | null;
  onClose: () => void;
  ms?: number;
}) {
  useEffect(() => {
    if (!toast) return;
    const t = setTimeout(onClose, ms);
    return () => clearTimeout(t);
  }, [toast, onClose, ms]);

  if (!toast) return null;
  return (
    <div className="toast" role="status" aria-live="polite">
      <span className="toast-msg">{toast.message}</span>
      {toast.onUndo ? (
        <button
          onClick={() => {
            onClose();
            toast.onUndo?.();
          }}
        >
          Undo
        </button>
      ) : null}
      <button className="toast-x" aria-label="Dismiss" onClick={onClose}>
        ✕
      </button>
    </div>
  );
}

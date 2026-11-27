// REQ-1211: Kontextmenue (Rechtsklick)
import { useEffect, useRef } from "react";

export interface ContextMenuItem {
  label: string;
  action: () => void;
  danger?: boolean;
  separator?: boolean;
}

interface Props {
  x: number;
  y: number;
  items: ContextMenuItem[];
  onClose: () => void;
}

export default function ContextMenu({ x, y, items, onClose }: Props) {
  const ref = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const handler = (e: MouseEvent) => {
      if (ref.current && !ref.current.contains(e.target as Node)) {
        onClose();
      }
    };
    const escHandler = (e: KeyboardEvent) => { if (e.key === "Escape") onClose(); };
    document.addEventListener("mousedown", handler);
    document.addEventListener("keydown", escHandler);
    return () => {
      document.removeEventListener("mousedown", handler);
      document.removeEventListener("keydown", escHandler);
    };
  }, [onClose]);

  return (
    <div
      ref={ref}
      style={{ position: "fixed", left: x, top: y, zIndex: 1000 }}
      className="bg-theme-surface border border-theme-border rounded-xl shadow-xl py-1 min-w-40 text-sm"
    >
      {items.map((item, i) =>
        item.separator ? (
          <div key={i} className="border-t border-theme-border my-1" />
        ) : (
          <button
            key={i}
            onClick={() => { item.action(); onClose(); }}
            className={
              "w-full text-left px-4 py-1.5 hover:bg-theme-surface-hover " +
              (item.danger ? "text-theme-danger hover:bg-theme-danger-soft" : "text-theme-text")
            }
          >
            {item.label}
          </button>
        )
      )}
    </div>
  );
}
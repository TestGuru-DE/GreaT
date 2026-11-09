// REQ-4018: Dialog "Datenklasse anwenden auf: <Kategorie>" (DataNode-Baum)
// Laedt den hierarchischen Datenklassen-Baum, der Nutzer waehlt Werte aus
// und uebernimmt sie als Werte der Kategorie.
import { useEffect, useState } from "react";
import { datanodesApi } from "../api/client";
import type { DataNode } from "../types";

interface Props {
  categoryName: string;
  onClose: () => void;
  onApply: (values: string[]) => void;
}

function collectValues(nodes: DataNode[], depth = 0): { key: string; label: string; value: string; depth: number }[] {
  const out: { key: string; label: string; value: string; depth: number }[] = [];
  for (const node of nodes) {
    out.push({ key: `node-${node.id}`, label: node.name, value: "", depth });
    for (const v of node.values ?? []) {
      out.push({ key: `val-${v.id}`, label: v.value, value: v.value, depth: depth + 1 });
    }
    out.push(...collectValues(node.children ?? [], depth + 1));
  }
  return out;
}

export default function DataNodeApplyDialog({ categoryName, onClose, onApply }: Props) {
  const [items, setItems] = useState<ReturnType<typeof collectValues>>([]);
  const [loading, setLoading] = useState(true);
  const [selected, setSelected] = useState<Set<string>>(new Set());

  useEffect(() => {
    let active = true;
    datanodesApi
      .getTree()
      .then((tree) => { if (active) setItems(collectValues(tree)); })
      .catch(() => { if (active) setItems([]); })
      .finally(() => { if (active) setLoading(false); });
    return () => { active = false; };
  }, []);

  const toggle = (key: string) => {
    setSelected((prev) => {
      const next = new Set(prev);
      if (next.has(key)) next.delete(key); else next.add(key);
      return next;
    });
  };

  const apply = () => {
    const values = items.filter((i) => i.value && selected.has(i.key)).map((i) => i.value);
    onApply(Array.from(new Set(values)));
  };

  return (
    <div role="dialog" aria-modal="true" aria-labelledby="dn-apply-title" className="fixed inset-0 z-50 flex items-center justify-center bg-black/40">
      <div className="bg-theme-surface rounded-2xl shadow-xl max-w-lg w-full mx-4 p-6 border border-theme-border">
        <h2 id="dn-apply-title" className="text-lg font-semibold text-theme-text">
          Datenklasse anwenden auf: {categoryName}
        </h2>
        <div className="mt-4 max-h-80 overflow-auto">
          {loading && <p className="text-sm text-theme-text-muted">Lade Datenklassen...</p>}
          {!loading && items.length === 0 && (
            <p className="text-sm text-theme-text-muted">Keine Datenklassen vorhanden.</p>
          )}
          <ul>
            {items.map((item) => (
              <li key={item.key} style={{ paddingLeft: `${item.depth * 16}px` }} className="py-0.5">
                {item.value ? (
                  <label className="flex items-center gap-2 text-sm text-theme-text">
                    <input
                      type="checkbox"
                      checked={selected.has(item.key)}
                      onChange={() => toggle(item.key)}
                    />
                    {item.label}
                  </label>
                ) : (
                  <span className="text-sm font-medium text-theme-text-secondary">{item.label}</span>
                )}
              </li>
            ))}
          </ul>
        </div>
        <div className="mt-4 flex gap-2 justify-end">
          <button onClick={onClose} className="px-4 py-2 text-sm font-medium text-theme-text-muted bg-theme-surface-hover rounded-md border border-theme-border">
            Abbrechen
          </button>
          <button
            onClick={apply}
            disabled={selected.size === 0}
            className="px-4 py-2 text-sm font-medium text-theme-accent-text bg-theme-accent rounded-md disabled:opacity-50"
          >
            Uebernehmen
          </button>
        </div>
      </div>
    </div>
  );
}

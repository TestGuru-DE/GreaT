// REQ-5012: Constraint-Dialog
// - Links: Auswahlliste aller Ursachen/Wirkungen (Checkboxen)
// - Rechts: Dropdown fuer Constraint-Typ (E, I, O, R, M)
// - Validierung: R/M brauchen genau 2, E/I/O brauchen mind. 2
import { useState, useEffect } from "react";
import { useDecisionTableStore } from "../store/decisionTableStore";

interface ConstraintDialogProps {
  projectId: number;
  onClose: () => void;
}

interface Constraint {
  id: number;
  type: string;
  targets: number[] | { from: number; to: number };
  description?: string;
}

interface ConstraintType {
  value: string;
  label: string;
  minSelect: number;
  maxSelect: number;
  mode: "cause" | "effect";
}

const CONSTRAINT_TYPES: ConstraintType[] = [
  { value: "E", label: "E – Exclusive (max. 1 wahr)", minSelect: 2, maxSelect: Infinity, mode: "cause" },
  { value: "O", label: "O – One-and-Only-One (genau 1 wahr)", minSelect: 2, maxSelect: Infinity, mode: "cause" },
  { value: "I", label: "I – Inclusive (mind. 1 wahr)", minSelect: 2, maxSelect: Infinity, mode: "cause" },
  { value: "R", label: "R – Requires (C1 → C2)", minSelect: 2, maxSelect: 2, mode: "cause" },
  { value: "M", label: "M – Mask (E1 → E2)", minSelect: 2, maxSelect: 2, mode: "effect" },
];

export default function ConstraintDialog({ projectId, onClose }: ConstraintDialogProps) {
  const causes = useDecisionTableStore((s) => s.causes);
  const effects = useDecisionTableStore((s) => s.effects);

  const [selectedItems, setSelectedItems] = useState<number[]>([]);
  const [constraintType, setConstraintType] = useState("E");
  const [description, setDescription] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [existingConstraints, setExistingConstraints] = useState<Constraint[]>([]);

  const currentType = CONSTRAINT_TYPES.find((t) => t.value === constraintType);
  const items = currentType?.mode === "effect" ? effects : causes;

  // Lade bestehende Constraints
  useEffect(() => {
    fetch(`/api/decision-table/constraints/${projectId}`, { credentials: "include" })
      .then((r) => r.json())
      .then(setExistingConstraints)
      .catch(() => {});
  }, [projectId]);

  function validate(): boolean {
    if (!currentType) return false;
    if (selectedItems.length < currentType.minSelect) {
      setError(`Mindestens ${currentType.minSelect} Eintraege erforderlich`);
      return false;
    }
    if (selectedItems.length > currentType.maxSelect) {
      setError(`Maximal ${currentType.maxSelect} Eintraege erlaubt`);
      return false;
    }
    setError(null);
    return true;
  }

  async function handleSubmit() {
    if (!validate()) return;
    setLoading(true);

    const targets =
      constraintType === "R" || constraintType === "M"
        ? { from: selectedItems[0], to: selectedItems[1] }
        : selectedItems;

    try {
      const response = await fetch("/api/decision-table/constraints", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        credentials: "include",
        body: JSON.stringify({
          project_id: projectId,
          constraint_type: constraintType,
          targets,
          description: description || undefined,
        }),
      });

      if (response.ok) {
        setSelectedItems([]);
        setDescription("");
        setConstraintType("E");
        // Reload constraints
        const resp = await fetch(`/api/decision-table/constraints/${projectId}`, {
          credentials: "include",
        });
        setExistingConstraints(await resp.json());
      } else {
        const err = await response.json();
        setError(err.detail || "Fehler");
      }
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : String(e));
    } finally {
      setLoading(false);
    }
  }

  async function handleDelete(id: number) {
    try {
      await fetch(`/api/decision-table/constraints/${id}`, {
        method: "DELETE",
        credentials: "include",
      });
      const resp = await fetch(`/api/decision-table/constraints/${projectId}`, {
        credentials: "include",
      });
      setExistingConstraints(await resp.json());
    } catch {
      // silently fail on delete error
    }
  }

  function getItemName(id: number): string {
    const item = items.find((i) => i.id === id);
    return item ? item.name : `#${id}`;
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black bg-opacity-50">
      <div className="bg-theme-surface rounded-lg shadow-xl max-w-2xl w-full mx-4 max-h-[80vh] overflow-y-auto">
        <div className="p-6">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-xl font-bold text-theme-text">Constraint hinzufuegen</h2>
            <button
              onClick={onClose}
              className="text-theme-text-secondary hover:text-theme-text"
              aria-label="Schliessen"
            >
              ✕
            </button>
          </div>

          {/* Constraint-Typ Auswahl */}
          <div className="mb-4">
            <label className="block text-sm font-medium text-theme-text mb-1">Typ</label>
            <select
              value={constraintType}
              onChange={(e) => {
                setConstraintType(e.target.value);
                setSelectedItems([]);
                setError(null);
              }}
              className="w-full rounded-md border border-theme-border px-3 py-2 text-theme-text bg-theme-bg-input"
            >
              {CONSTRAINT_TYPES.map((t) => (
                <option key={t.value} value={t.value}>
                  {t.label}
                </option>
              ))}
            </select>
          </div>

          {/* Items-Auswahl */}
          <div className="mb-4">
            <label className="block text-sm font-medium text-theme-text mb-1">
              {currentType?.mode === "effect" ? "Wirkungen" : "Ursachen"} auswaehlen
              {constraintType === "R" && (
                <span className="text-xs text-theme-text-secondary ml-2">
                  (1. = Voraussetzung, 2. = Folge)
                </span>
              )}
              {constraintType === "M" && (
                <span className="text-xs text-theme-text-secondary ml-2">
                  (1. = Ausloser, 2. = Blockierter)
                </span>
              )}
            </label>
            <div className="border border-theme-border rounded-md max-h-40 overflow-y-auto">
              {items.map((item) => (
                <label
                  key={item.id}
                  className="flex items-center gap-2 px-3 py-2 hover:bg-theme-bg-hover cursor-pointer"
                >
                  <input
                    type="checkbox"
                    checked={selectedItems.includes(item.id)}
                    onChange={() => {
                      setSelectedItems((prev) =>
                        prev.includes(item.id)
                          ? prev.filter((id) => id !== item.id)
                          : prev.length < (currentType?.maxSelect ?? Infinity)
                            ? [...prev, item.id]
                            : prev
                      );
                      setError(null);
                    }}
                    className="rounded border-theme-border"
                  />
                  <span className="text-sm text-theme-text">{getItemName(item.id)}</span>
                </label>
              ))}
            </div>
            {selectedItems.length > 0 && (
              <p className="text-xs text-theme-text-secondary mt-1">
                Ausgewaehlt: {selectedItems.map((id) => getItemName(id)).join(", ")}
              </p>
            )}
          </div>

          {/* Beschreibung */}
          <div className="mb-4">
            <label className="block text-sm font-medium text-theme-text mb-1">
              Beschreibung (optional)
            </label>
            <input
              type="text"
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              className="w-full rounded-md border border-theme-border px-3 py-2 text-theme-text bg-theme-bg-input"
              placeholder="z.B. 'Nur eine Zahlungsmethode moeglich'"
            />
          </div>

          {error && <p className="text-sm text-theme-danger mb-2">{error}</p>}

          <div className="flex justify-end gap-2">
            <button
              onClick={onClose}
              className="px-4 py-2 text-sm text-theme-text-secondary hover:text-theme-text"
            >
              Abbrechen
            </button>
            <button
              onClick={handleSubmit}
              disabled={loading}
              className="px-4 py-2 text-sm bg-theme-primary text-white rounded-md hover:opacity-90 disabled:opacity-50"
            >
              {loading ? "..." : "Hinzufuegen"}
            </button>
          </div>

          {/* Bestehende Constraints */}
          {existingConstraints.length > 0 && (
            <div className="mt-6 pt-4 border-t border-theme-border">
              <h3 className="text-sm font-semibold text-theme-text mb-2">
                Bestehende Constraints
              </h3>
              <ul className="space-y-1">
                {existingConstraints.map((c) => (
                  <li key={c.id} className="flex items-center justify-between text-sm">
                    <span className="text-theme-text">
                      <span className="font-mono bg-theme-bg-muted px-1 rounded">{c.type}</span>
                      {" "}–{" "}
                      {Array.isArray(c.targets)
                        ? c.targets.map((id) => getItemName(id)).join(", ")
                        : `${getItemName(c.targets.from)} → ${getItemName(c.targets.to)}`}
                      {c.description && (
                        <span className="text-theme-text-secondary ml-1">({c.description})</span>
                      )}
                    </span>
                    <button
                      onClick={() => handleDelete(c.id)}
                      className="text-theme-danger hover:underline text-xs"
                    >
                      Loeschen
                    </button>
                  </li>
                ))}
              </ul>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
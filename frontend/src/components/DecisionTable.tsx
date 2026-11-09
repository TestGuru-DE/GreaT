import { useEffect } from "react";
// REQ-5003 + REQ-5004 + REQ-5005: Entscheidungstabelle-Komponente
// Layout: Ursachen oben, Wirkungen unten, Regeln als Spalten
// Boolean-Werte (Y/N) als Default, automatische Regelgenerierung
// REQ-5012: Constraint-Dialog Integration
// REQ-5021: Priorisierung von Wirkungen (Override)
import { useState } from "react";
import { useDecisionTableStore } from "../store/decisionTableStore";
import ConstraintDialog from "./ConstraintDialog";
import DecisionTableHelp from "./DecisionTableHelp";

interface DecisionTableProps {
  projectId?: number;
}

export default function DecisionTable({ projectId }: DecisionTableProps) {
  const causes = useDecisionTableStore((s) => s.causes);
  const effects = useDecisionTableStore((s) => s.effects);
  const generate = useDecisionTableStore((s) => s.generate);
  const rules = useDecisionTableStore((s) => s.rules);
  const loading = useDecisionTableStore((s) => s.loading);
  const error = useDecisionTableStore((s) => s.error);
  const updateEffect = useDecisionTableStore((s) => s.updateEffect);
  const updateCause = useDecisionTableStore((s) => s.updateCause);

  // REQ-5013/5014/5019/5020: Optimierungsfelder
  const checksum = useDecisionTableStore((s) => s.checksum);
  const contradictions = useDecisionTableStore((s) => s.contradictions);
  const gaps = useDecisionTableStore((s) => s.gaps);
  const collapsedCount = useDecisionTableStore((s) => s.collapsedCount);
  const runCollapse = useDecisionTableStore((s) => s.runCollapse);
  const runValidate = useDecisionTableStore((s) => s.runValidate);

  // REQ-5021: Priorisierung von Wirkungen
  const effectPriorities = useDecisionTableStore((s) => s.effectPriorities);
  const setEffectPriority = useDecisionTableStore((s) => s.setEffectPriority);

  // EPIC-20 Schulden: Text/Binar-Modus und Override
  const effectMode = useDecisionTableStore((s) => s.effectMode);
  const setEffectMode = useDecisionTableStore((s) => s.setEffectMode);
  const enableOverride = useDecisionTableStore((s) => s.enableOverride);
  const setEnableOverride = useDecisionTableStore((s) => s.setEnableOverride);

  // REQ-5012: Constraint-Dialog State
  const [showConstraintDialog, setShowConstraintDialog] = useState(false);

  // Hilfe-Dialog State
  const [showHelpDialog, setShowHelpDialog] = useState(false);

  const effectiveProjectId = projectId ?? 1;
  // REQ-5002/REQ-5003: Ursachen und Wirkungen des Projekts beim Oeffnen laden
  useEffect(() => {
    const store = (useDecisionTableStore as any).getState?.();
    void store?.loadCategories?.(effectiveProjectId);
  }, [effectiveProjectId]);

  if (loading) {
    return (
      <div className="flex items-center justify-center py-12 text-theme-text-secondary animate-pulse">
        Lade Entscheidungstabelle...
      </div>
    );
  }

  if (error) {
    return (
      <div className="px-4 py-3 bg-theme-danger/10 border border-theme-danger rounded-lg text-theme-danger text-sm">
        <div className="flex items-start gap-2">
          <span className="text-lg flex-shrink-0">⚠️</span>
          <div>
            <p className="font-medium">Fehler bei der Generierung</p>
            <p className="mt-1 text-xs">{error}</p>
            <p className="mt-2 text-xs text-theme-text-secondary">
              Tipp: Stelle sicher, dass mindestens eine Ursache- und eine Wirkungskategorie existiert.
            </p>
          </div>
        </div>
      </div>
    );
  }

  if (rules.length === 0 && causes.length === 0 && effects.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center py-12 text-theme-text-secondary">
        <span className="text-3xl mb-2">📋</span>
        <p className="text-sm font-medium">Keine Ursachen oder Wirkungen gefunden</p>
        <p className="text-xs mt-1">
          Erstellen Sie mindestens eine Ursache- und eine Wirkungskategorie im Kategorienbaum.
        </p>
      </div>
    );
  }

  return (
    <div>
      {/* REQ-5013/5014/5019/5020: Optimierung – Collapsing + Validation */}
      {projectId !== undefined && (
        <div className="mb-4 space-y-3">
          {/* Buttons */}
          <div className="flex gap-2">
            <button
              onClick={() => void generate?.(effectiveProjectId)}
              className="px-3 py-1.5 text-sm bg-theme-primary text-white rounded-md hover:opacity-90 transition-opacity"
              aria-label="Regeln generieren"
            >
              Regeln generieren
            </button>
            <button
              onClick={() => runCollapse(effectiveProjectId)}
              className="px-3 py-1.5 text-sm bg-theme-primary text-white rounded-md hover:opacity-90 transition-opacity"
              aria-label="Regeln zusammenfassen"
            >
              📦 Zusammenfassen{collapsedCount > 0 && ` (${collapsedCount} reduziert)`}
            </button>
            <button
              onClick={() => runValidate(effectiveProjectId)}
              className="px-3 py-1.5 text-sm border border-theme-border text-theme-text rounded-md hover:bg-theme-bg-hover transition-colors"
              aria-label="Entscheidungstabelle pruefen"
            >
              🔍 Pruefen
            </button>
            <button
              onClick={() => setShowHelpDialog(true)}
              className="px-3 py-1.5 text-sm border border-theme-border text-theme-text rounded-md hover:bg-theme-bg-hover transition-colors"
              aria-label="Hilfe anzeigen"
            >
              ❓ Hilfe
            </button>
          </div>

          {/* Checksum-Anzeige */}
          {checksum && (
            <div
              className={`p-3 rounded ${
                checksum.status === "complete"
                  ? "bg-green-50 border border-green-200 text-green-800"
                  : checksum.status === "overlap"
                    ? "bg-yellow-50 border border-yellow-200 text-yellow-800"
                    : "bg-red-50 border border-red-200 text-red-800"
              }`}
            >
              <strong>Checksum:</strong> {checksum.checksum} / {checksum.expected} –{" "}
              {checksum.message}
            </div>
          )}

          {/* Widersprueche */}
          {contradictions.length > 0 && (
            <div className="space-y-1">
              {contradictions.map((c, i) => (
                <div
                  key={i}
                  className="p-2 bg-red-50 border border-red-200 text-red-800 rounded text-sm"
                >
                  ⚠️ {c.message}
                </div>
              ))}
            </div>
          )}

          {/* Luecken */}
          {gaps.length > 0 && (
            <div className="p-2 bg-amber-50 border border-amber-200 text-amber-800 rounded">
              <p className="text-sm font-medium">{gaps.length} Luecke(n) in der Abdeckung</p>
              <div className="max-h-32 overflow-y-auto mt-1">
                {gaps.map((g, i) => (
                  <p key={i} className="text-xs">
                    {g.message}
                  </p>
                ))}
              </div>
            </div>
          )}
        </div>
      )}

      {/* REQ-5012: Constraint-Button */}
      {projectId !== undefined && (
        <div className="mb-3 flex justify-end">
          <button
            onClick={() => setShowConstraintDialog(true)}
            className="px-3 py-1.5 text-sm bg-theme-primary text-white rounded-md hover:opacity-90 transition-opacity"
            aria-label="Constraint hinzufuegen"
          >
            Constraint hinzufuegen
          </button>
        </div>
      )}

      {/* EPIC-20 Schulden: Text/Binar Toggle + Override */}
      <div className="flex gap-2 mb-3 flex-wrap">
        <button
          onClick={() => setEffectMode(effectMode === "binary" ? "text" : "binary")}
          className="px-3 py-1.5 text-sm border border-theme-border rounded-md text-theme-text hover:bg-theme-bg-hover"
        >
          {effectMode === "binary" ? "📝 Text-Modus" : "☑️ Binar-Modus"}
        </button>

        <button
          onClick={() => setEnableOverride(!enableOverride)}
          className={`px-3 py-1.5 text-sm rounded-md ${enableOverride ? "bg-red-600 text-white" : "border border-theme-border text-theme-text hover:bg-theme-bg-hover"}`}
        >
          {enableOverride ? "⚠️ Override AKTIV" : "Override-Modus"}
        </button>
      </div>

      {enableOverride && (
        <div className="p-2 mb-3 bg-red-50 border border-red-200 text-red-800 rounded text-sm">
          ⚠️ Override-Modus: Niedrig-priorisierte Wirkungen werden zu Don't Care (—)
        </div>
      )}

      <div className="overflow-x-auto rounded-xl border border-theme-border shadow-sm">
        <table className="w-full border-collapse text-sm">
          <thead>
            <tr>
              <th
                rowSpan={causes.length > 0 || effects.length > 0 ? 2 : 1}
                className="sticky left-0 z-10 bg-theme-surface border border-theme-border p-2 font-semibold text-theme-text min-w-[140px] text-left"
              >
                Regel
              </th>
              {rules.map((rule) => (
                <th
                  key={rule.id}
                  className="border border-theme-border p-1 text-center min-w-[60px] font-medium text-theme-text"
                >
                  R{rule.id}
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {/* REQ-5003: Ursachenzellen (oben) */}
            {causes.map((cause) => (
              <tr key={cause.id}>
                <td className="sticky left-0 z-10 bg-theme-surface-hover border border-theme-border p-2 font-medium text-theme-text">
                  {cause.name}
                </td>
                {rules.map((rule) => (
                  <td key={rule.id} className="border border-theme-border p-1 text-center">
                    <select
                      value={rule.causes[cause.id] ?? "Y"}
                      onChange={(e) => updateCause(rule.id, cause.id, e.target.value)}
                      className="w-full text-center bg-transparent text-theme-text cursor-pointer focus:outline-none focus:ring-1 focus:ring-theme-primary rounded"
                      aria-label={`Regel R${rule.id} – ${cause.name}`}
                    >
                      <option value="Y">Y</option>
                      <option value="N">N</option>
                      <option value="-">—</option>
                    </select>
                  </td>
                ))}
              </tr>
            ))}

            {/* REQ-5003: Trennlinie zwischen Ursachen und Wirkungen */}
            {causes.length > 0 && effects.length > 0 && (
              <tr>
                <td
                  colSpan={rules.length + 1}
                  className="border-t-2 border-b-2 border-theme-border bg-theme-bg-muted p-1 text-xs text-theme-text-secondary text-center"
                >
                  ───────────── Ursachen / Wirkungen ─────────────
                </td>
              </tr>
            )}

            {/* REQ-5003: Wirkungszellen (unten) – initial leer */}
            {effects.map((effect) => (
              <tr key={effect.id}>
                <td className="sticky left-0 z-10 bg-theme-surface-hover border border-theme-border p-2 font-medium text-theme-text">
                  <div className="flex items-center gap-2">
                    <span>{effect.name}</span>
                    {/* REQ-5021: Prioritaets-Selector fuer Wirkung */}
                    <select
                      value={effectPriorities[effect.id] ?? 999}
                      onChange={(e) => setEffectPriority(effect.id, parseInt(e.target.value))}
                      className="text-xs border border-theme-border rounded px-1 py-0.5 bg-theme-bg-input text-theme-text"
                      aria-label={`Prioritaet fuer ${effect.name}`}
                      title="Prioritaet (1=hoechst, 999=keine)"
                    >
                      <option value={999}>Keine</option>
                      {Array.from({ length: effects.length }, (_, i) => (
                        <option key={i + 1} value={i + 1}>
                          Prio {i + 1}
                        </option>
                      ))}
                    </select>
                  </div>
                </td>
                {rules.map((rule) => (
                  <td key={rule.id} className="border border-theme-border p-1 text-center">
                    {effectMode === "text" ? (
                      <>
                        <input
                          type="text"
                          value={(rule.effects[effect.id] as string) || ""}
                          onChange={(e) => updateEffect(rule.id, effect.id, e.target.value || null)}
                          className="w-full text-center text-sm bg-transparent text-theme-text"
                          placeholder="Wirkung"
                          list={`effect-datalist-${effect.id}`}
                          aria-label={`Regel R${rule.id} – ${effect.name}`}
                        />
                        <datalist id={`effect-datalist-${effect.id}`}>
                          {effect.values?.map((v: string) => (
                            <option key={v} value={v} />
                          ))}
                        </datalist>
                      </>
                    ) : (
                      <select
                        value={(rule.effects[effect.id] as string) || ""}
                        onChange={(e) =>
                          updateEffect(
                            rule.id,
                            effect.id,
                            e.target.value ? (e.target.value as string | null) : null
                          )
                        }
                        className="w-full text-center bg-transparent text-theme-text cursor-pointer focus:outline-none focus:ring-1 focus:ring-theme-primary rounded"
                        aria-label={`Regel R${rule.id} – ${effect.name}`}
                      >
                        <option value="">·</option>
                        <option value="X">X</option>
                        <option value="-">—</option>
                      </select>
                    )}
                  </td>
                ))}
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {/* REQ-5012: Constraint-Dialog Modal */}
      {showConstraintDialog && projectId !== undefined && (
        <ConstraintDialog
          projectId={projectId}
          onClose={() => setShowConstraintDialog(false)}
        />
      )}

      {/* Hilfe-Dialog */}
      {showHelpDialog && (
        <DecisionTableHelp onClose={() => setShowHelpDialog(false)} />
      )}
    </div>
  );
}
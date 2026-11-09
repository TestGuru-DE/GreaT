// REQ-4022: StaleDataWarning-Banner bei 409-Conflict
// Teil von EPIC-18 (Multi-User) / Sprint 12
//
// Zeigt ein deutliches Banner wenn Daten veraltet sind (Optimistic Concurrency Conflict).
// Kein automatisches, stilles Ueberschreiben ohne Nutzerinteraktion.
import { useState } from "react";

interface StaleDataWarningProps {
  /** Wer hat die Aenderung vorgenommen (optional, aus 409-Response) */
  modifiedBy?: string;
  /** Wann wurde geaendert (optional) */
  modifiedAt?: string;
  /** Callback: Nutzer hat "Neu laden" gewaehlt */
  onReload: () => void;
  /** Callback: Nutzer hat "Trotzdem ueberschreiben" gewaehlt */
  onOverwrite: () => void;
  /** Banner sichtbar? */
  visible: boolean;
  /** Banner schliessen */
  onClose: () => void;
}

export default function StaleDataWarning({
  modifiedBy,
  modifiedAt,
  onReload,
  onOverwrite,
  visible,
  onClose,
}: StaleDataWarningProps) {
  const [showConfirm, setShowConfirm] = useState(false);

  if (!visible) return null;

  return (
    <div className="fixed top-0 left-0 right-0 z-50">
      <div className="mx-4 mt-4 rounded-lg border-2 border-theme-warning bg-theme-bg shadow-lg">
        <div className="p-4">
          <div className="flex items-start gap-3">
            <svg
              className="h-6 w-6 flex-shrink-0 text-theme-warning"
              fill="none"
              viewBox="0 0 24 24"
              stroke="currentColor"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z"
              />
            </svg>
            <div className="flex-1">
              <h3 className="text-sm font-semibold text-theme-warning">
                Diese Ansicht ist veraltet
              </h3>
              <p className="text-sm text-theme-text-secondary mt-1">
                {modifiedBy
                  ? `Diese Daten wurden zwischenzeitlich von ${modifiedBy} geaendert.`
                  : "Diese Daten wurden zwischenzeitlich von einer anderen Person geaendert."}
                {modifiedAt && (
                  <span className="block text-xs text-theme-text-muted">
                    Letzte Aenderung: {modifiedAt}
                  </span>
                )}
              </p>
            </div>
            <button
              onClick={onClose}
              className="text-theme-text-muted hover:text-theme-text"
              aria-label="Schliessen"
            >
              <svg className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
              </svg>
            </button>
          </div>
          <div className="mt-3 flex gap-2 justify-end">
            <button
              onClick={onReload}
              className="inline-flex items-center px-3 py-1.5 border border-transparent text-sm font-medium rounded-md text-theme-accent-text bg-theme-warning hover:opacity-90 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-theme-warning"
            >
              Neu laden
            </button>
            <button
              onClick={() => setShowConfirm(true)}
              className="inline-flex items-center px-3 py-1.5 border border-theme-border text-sm font-medium rounded-md text-theme-text bg-theme-surface hover:bg-theme-surface-hover focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-theme-warning"
            >
              Trotzdem ueberschreiben
            </button>
          </div>
        </div>
      </div>

      {/* Bestaetigungsdialog fuer "Trotzdem ueberschreiben" */}
      {showConfirm && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40">
          <div className="bg-theme-surface rounded-2xl shadow-xl max-w-md w-full mx-4 p-6 border border-theme-border">
            <h3 className="text-lg font-semibold text-theme-text">
              Ueberschreiben bestaetigen
            </h3>
            <p className="mt-2 text-sm text-theme-text-secondary">
              Du bist dabei, die Aenderungen einer anderen Person zu ueberschreiben.
              Diese Aktion kann nicht rueckgaengig gemacht werden.
            </p>
            <div className="mt-4 flex gap-2 justify-end">
              <button
                onClick={() => setShowConfirm(false)}
                className="px-4 py-2 text-sm font-medium text-theme-text-muted bg-theme-surface-hover hover:opacity-90 rounded-md border border-theme-border"
              >
                Abbrechen
              </button>
              <button
                onClick={() => {
                  setShowConfirm(false);
                  onOverwrite();
                }}
                className="px-4 py-2 text-sm font-medium text-theme-accent-text bg-theme-danger hover:opacity-90 rounded-md"
              >
                Trotzdem ueberschreiben
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
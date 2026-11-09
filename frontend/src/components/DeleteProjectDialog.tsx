// REQ-2002: Dialog fuer Loeschen von Projekten mit verknuepften Generierungen
import type { Project } from "../types";

interface Props {
  projects: Project[];          // betroffene Projekte (mit Generierungen)
  generationCount: number;      // Gesamtzahl der Generierungen
  onConfirm: () => void;        // Ja – loeschen
  onCancel: () => void;         // Nein – abbrechen
  onShow: (project: Project) => void; // Anzeigen – zur Generierungsansicht
}

export default function DeleteProjectDialog({ projects, generationCount, onConfirm, onCancel, onShow }: Props) {
  const isSingle = projects.length === 1;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40">
      <div className="bg-theme-surface rounded-2xl shadow-xl max-w-md w-full mx-4 p-6 border border-theme-border">
        <h3 className="text-lg font-semibold text-theme-text mb-3">Projekt{isSingle ? "" : "e"} löschen</h3>
        <p className="text-sm text-theme-text-secondary mb-2">
          {isSingle
            ? <>Das Projekt <strong>{projects[0].name}</strong> hat</>
            : <>{projects.length} der ausgewählten Projekte haben</>
          }{" "}
          <strong>{generationCount} {generationCount === 1 ? "Generierung" : "Generierungen"}</strong> verknüpft.
        </p>
        <p className="text-sm text-theme-warning bg-theme-bg border-2 border-theme-warning rounded-lg px-3 py-2 mb-5">
          Beim Löschen werden alle verknüpften Generierungen und Testfälle unwiderruflich entfernt.
        </p>

        <div className="flex flex-col gap-2">
          <button
            onClick={onConfirm}
            className="w-full px-4 py-2 bg-theme-danger text-theme-accent-text rounded-lg hover:opacity-90 font-medium text-sm"
          >
            Ja – alles löschen
          </button>

          {projects.length === 1 && (
            <button
              onClick={() => onShow(projects[0])}
              className="w-full px-4 py-2 border border-theme-border text-theme-text-secondary rounded-lg hover:bg-theme-surface-hover text-sm"
            >
              Anzeigen (Generierungen des Projekts)
            </button>
          )}
          {projects.length > 1 && (
            <div className="flex flex-col gap-1 max-h-32 overflow-y-auto">
              {projects.map((p) => (
                <button
                  key={p.id}
                  onClick={() => onShow(p)}
                  className="w-full px-4 py-1.5 border border-theme-border text-theme-text-secondary rounded-lg hover:bg-theme-surface-hover text-xs text-left"
                >
                  Anzeigen: {p.name}
                </button>
              ))}
            </div>
          )}

          <button
            onClick={onCancel}
            className="w-full px-4 py-2 border border-theme-border text-theme-text-muted rounded-lg hover:bg-theme-surface-hover text-sm mt-1"
          >
            Nein – abbrechen
          </button>
        </div>
      </div>
    </div>
  );
}
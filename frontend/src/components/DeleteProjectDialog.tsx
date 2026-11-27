// REQ-2002: Dialog fuer Loeschen von Projekten mit verknuepften Generierungen
// REQ-6005: i18n
import { useTranslation } from "react-i18next";
import type { Project } from "../types";

interface Props {
  projects: Project[];          // betroffene Projekte (mit Generierungen)
  generationCount: number;      // Gesamtzahl der Generierungen
  onConfirm: () => void;        // Ja – loeschen
  onCancel: () => void;         // Nein – abbrechen
  onShow: (project: Project) => void; // Anzeigen – zur Generierungsansicht
}

export default function DeleteProjectDialog({ projects, generationCount, onConfirm, onCancel, onShow }: Props) {
  const { t } = useTranslation();
  const isSingle = projects.length === 1;

  const genWord = generationCount === 1 ? "Generierung" : "Generierungen";

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40">
      <div className="bg-theme-surface rounded-2xl shadow-xl max-w-md w-full mx-4 p-6 border border-theme-border">
        <h3 className="text-lg font-semibold text-theme-text mb-3">
          {isSingle ? t('deleteProjectDialog.titleSingle') : t('deleteProjectDialog.titleMultiple')}
        </h3>
        <p className="text-sm text-theme-text-secondary mb-2">
          {isSingle
            ? <>
                {t('deleteProjectDialog.messageSingle', { name: projects[0].name })}{" "}
                <strong>{generationCount} {genWord}</strong> {t('common.linked')}.
              </>
            : <>
                {t('deleteProjectDialog.messageMultiple', { count: projects.length })}{" "}
                <strong>{generationCount} {genWord}</strong> {t('common.linked')}.
              </>
          }
        </p>
        <p className="text-sm text-theme-warning bg-theme-bg border-2 border-theme-warning rounded-lg px-3 py-2 mb-5">
          {t('deleteProjectDialog.warning')}
        </p>

        <div className="flex flex-col gap-2">
          <button
            onClick={onConfirm}
            className="w-full px-4 py-2 bg-theme-danger-fill text-theme-accent-text rounded-lg hover:opacity-90 font-medium text-sm"
          >
            {t('deleteProjectDialog.confirm')}
          </button>

          {projects.length === 1 && (
            <button
              onClick={() => onShow(projects[0])}
              className="w-full px-4 py-2 border border-theme-border text-theme-text-secondary rounded-lg hover:bg-theme-surface-hover text-sm"
            >
              {t('deleteProjectDialog.showSingle')}
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
                  {t('deleteProjectDialog.showMultiple', { name: p.name })}
                </button>
              ))}
            </div>
          )}

          <button
            onClick={onCancel}
            className="w-full px-4 py-2 border border-theme-border text-theme-text-muted rounded-lg hover:bg-theme-surface-hover text-sm mt-1"
          >
            {t('deleteProjectDialog.cancel')}
          </button>
        </div>
      </div>
    </div>
  );
}
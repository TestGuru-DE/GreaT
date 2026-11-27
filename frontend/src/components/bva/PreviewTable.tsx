// REQ-3041, REQ-4015: PreviewTable – Live-Vorschau der zu erzeugenden Werte mit is_error
import { useTranslation } from "react-i18next";
import type { MultiRangeBVAPoint } from "../../lib/bva-calc";

interface PreviewTableProps {
  points: MultiRangeBVAPoint[];
  markAsErrorCase?: boolean;
}

export function PreviewTable({ points, markAsErrorCase }: PreviewTableProps) {
  const { t } = useTranslation();
  if (points.length === 0) {
    return (
      <div className="text-center py-4 text-theme-text-muted text-sm">
        {t('previewTable.empty')}
      </div>
    );
  }

  return (
    <div className="border border-theme-border rounded-lg overflow-hidden">
      <table className="w-full text-sm">
        <thead className="bg-theme-surface-2 border-b border-theme-border">
          <tr>
            <th className="px-3 py-2 text-left font-semibold text-theme-text">{t('previewTable.value')}</th>
            <th className="px-3 py-2 text-left font-semibold text-theme-text">{t('previewTable.type')}</th>
            <th className="px-3 py-2 text-left font-semibold text-theme-text">{t('previewTable.range')}</th>
            <th className="px-3 py-2 text-left font-semibold text-theme-text">{t('previewTable.status')}</th>
          </tr>
        </thead>
        <tbody>
          {points.map((pt, idx) => {
            // REQ-4015: Prüfe ob is_error Feld vorhanden (MultiRangeBVAPoint)
            const isError = pt.isError;
            const statusLabel = isError === true ? "Fehlerfall" : 
                               markAsErrorCase ? "Fehlerfall" :
                               "Erlaubt";
            const statusBg = isError === true ? "bg-theme-danger-soft text-theme-danger" :
                            markAsErrorCase ? "bg-theme-danger-soft text-theme-danger" :
                            "bg-theme-success-soft text-theme-success";
            
            return (
              <tr
                key={idx}
                className="border-b border-theme-border hover:bg-theme-surface-hover"
              >
                <td className="px-3 py-2 font-mono text-theme-text">
                  {isError && <span className="mr-1">✗</span>}
                  {pt.value}
                </td>
                <td className="px-3 py-2 text-theme-text-secondary">{pt.label}</td>
                <td className="px-3 py-2 text-theme-text-secondary text-xs">
                  {pt.sourceRange ?? ""}
                </td>
                <td className="px-3 py-2">
                  <span className={`inline-flex items-center px-2 py-0.5 rounded text-xs font-medium ${statusBg}`}>
                    {statusLabel}
                  </span>
                </td>
              </tr>
            );
          })}
        </tbody>
      </table>
    </div>
  );
}

// REQ-3041: PreviewTable – Live-Vorschau der zu erzeugenden Werte
import type { BVAPoint } from "../../lib/bva-calc";

interface PreviewTableProps {
  points: BVAPoint[];
  markAsErrorCase: boolean;
}

export function PreviewTable({ points, markAsErrorCase }: PreviewTableProps) {
  if (points.length === 0) {
    return (
      <div className="text-center py-4 text-slate-400 text-sm">
        Keine Vorschau verfügbar
      </div>
    );
  }

  return (
    <div className="border border-slate-200 rounded-lg overflow-hidden">
      <table className="w-full text-sm">
        <thead className="bg-slate-50 border-b border-slate-200">
          <tr>
            <th className="px-3 py-2 text-left font-semibold text-slate-700">Wert</th>
            <th className="px-3 py-2 text-left font-semibold text-slate-700">Typ</th>
            <th className="px-3 py-2 text-left font-semibold text-slate-700">Status</th>
          </tr>
        </thead>
        <tbody>
          {points.map((pt, idx) => (
            <tr
              key={idx}
              className="border-b border-slate-100 hover:bg-slate-50"
            >
              <td className="px-3 py-2 font-mono text-slate-800">{pt.value}</td>
              <td className="px-3 py-2 text-slate-600">{pt.label}</td>
              <td className="px-3 py-2">
                {markAsErrorCase ? (
                  <span className="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-red-100 text-red-800">
                    Fehlerfall
                  </span>
                ) : (
                  <span className="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-green-100 text-green-800">
                    Erlaubt
                  </span>
                )}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

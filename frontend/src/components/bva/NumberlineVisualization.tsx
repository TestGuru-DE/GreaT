// REQ-3041, REQ-4015: NumberlineVisualization – SVG-Zahlenstrahl mit Markierungen und Fehlerwert-Kennzeichnung
import type { BVAPoint } from "../../lib/bva-calc";
import Decimal from "decimal.js";

interface NumberlineVisualizationProps {
  points: BVAPoint[];
  useSymbolicSpacing?: boolean;  // REQ-4015: Symbolische Abstände statt maßstabsgetreu
}

export function NumberlineVisualization({ points, useSymbolicSpacing = true }: NumberlineVisualizationProps) {
  const width = 700;
  const height = 140;
  const margin = { left: 50, right: 50, top: 20, bottom: 50 };
  const lineY = height / 2;
  const lineX1 = margin.left;
  const lineX2 = width - margin.right;

  if (points.length === 0) {
    return (
      <svg width={width} height={height} className="mx-auto">
        <text x={width / 2} y={height / 2} textAnchor="middle" fill="#94a3b8" fontSize="13">
          Keine Punkte zum Anzeigen
        </text>
      </svg>
    );
  }

  // REQ-4015: Berechne X-Position für jeden Punkt
  const getX = (idx: number, value: string): number => {
    if (useSymbolicSpacing) {
      // Symbolische Abstände: alle Punkte gleichmäßig verteilt
      return lineX1 + (idx / Math.max(1, points.length - 1)) * (lineX2 - lineX1);
    } else {
      // Maßstabsgetreu: basierend auf numerischem Wert
      const values = points.map((p) => new Decimal(p.value));
      const minVal = Decimal.min(...values);
      const maxVal = Decimal.max(...values);
      const range = maxVal.minus(minVal);
      
      if (range.isZero()) return (lineX1 + lineX2) / 2;
      
      const val = new Decimal(value);
      const normalized = val.minus(minVal).div(range);
      return lineX1 + normalized.toNumber() * (lineX2 - lineX1);
    }
  };

  return (
    <svg width={width} height={height} className="mx-auto">
      {/* Zahlenstrahl */}
      <line
        x1={lineX1}
        y1={lineY}
        x2={lineX2}
        y2={lineY}
        stroke="#94a3b8"
        strokeWidth="2"
      />

      {/* Marker fuer jeden Punkt */}
      {points.map((pt, idx) => {
        const isError = (pt as any).isError;
        const isBoundary = pt.type === "boundary";
        const x = getX(idx, pt.value);
        
        // REQ-4015: Fehlerwertwerte rot, Grenzwerte blau, Innere Werte gelb
        let color = "#f59e0b";  // inside
        if (isError) {
          color = "#ef4444";  // Fehler: rot
        } else if (isBoundary) {
          color = "#0ea5e9";  // boundary: blau
        }

        return (
          <g key={idx}>
            <circle
              cx={x}
              cy={lineY}
              r={isError ? 7 : (isBoundary ? 6 : 5)}
              fill={color}
              stroke="white"
              strokeWidth="2"
            />
            {isError && (
              <text
                x={x}
                y={lineY + 1}
                textAnchor="middle"
                fontSize="10"
                fill="white"
                fontWeight="bold"
              >
                ✗
              </text>
            )}
            <text
              x={x}
              y={lineY + 30}
              textAnchor="middle"
              fontSize="11"
              fill="#475569"
              fontFamily="monospace"
            >
              {pt.value}
            </text>
            <text
              x={x}
              y={lineY + 45}
              textAnchor="middle"
              fontSize="10"
              fill="#64748b"
            >
              {pt.label}
            </text>
            {(pt as any).sourceRange && (
              <text
                x={x}
                y={lineY + 58}
                textAnchor="middle"
                fontSize="9"
                fill="#94a3b8"
              >
                {(pt as any).sourceRange}
              </text>
            )}
          </g>
        );
      })}
      
      {/* Legende */}
      <g transform={`translate(${lineX1}, ${height - 30})`}>
        <circle cx={0} cy={0} r={4} fill="#0ea5e9" stroke="white" strokeWidth="1" />
        <text x={12} y={4} fontSize="10" fill="#64748b">Grenzwert</text>
        
        <circle cx={80} cy={0} r={4} fill="#f59e0b" stroke="white" strokeWidth="1" />
        <text x={92} y={4} fontSize="10" fill="#64748b">Innen</text>
        
        <circle cx={130} cy={0} r={5} fill="#ef4444" stroke="white" strokeWidth="1" />
        <text x={142} y={4} fontSize="10" fill="#64748b">Fehler</text>
      </g>
    </svg>
  );
}

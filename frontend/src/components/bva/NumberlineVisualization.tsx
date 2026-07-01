// REQ-3041: NumberlineVisualization – SVG-Zahlenstrahl mit Markierungen
import type { BVAPoint } from "../../lib/bva-calc";
import Decimal from "decimal.js";

interface NumberlineVisualizationProps {
  points: BVAPoint[];
}

export function NumberlineVisualization({ points }: NumberlineVisualizationProps) {
  const width = 700;
  const height = 120;
  const margin = { left: 50, right: 50, top: 20, bottom: 40 };
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

  // Numerische Werte extrahieren
  const values = points.map((p) => new Decimal(p.value));
  const minVal = Decimal.min(...values);
  const maxVal = Decimal.max(...values);
  const range = maxVal.minus(minVal);

  // Skala fuer X-Position
  const scale = (val: Decimal) => {
    if (range.isZero()) return (lineX1 + lineX2) / 2;
    const normalized = val.minus(minVal).div(range);
    return lineX1 + normalized.toNumber() * (lineX2 - lineX1);
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
        const val = new Decimal(pt.value);
        const x = scale(val);
        const isBoundary = pt.type === "boundary";
        const color = isBoundary ? "#0ea5e9" : "#f59e0b";

        return (
          <g key={idx}>
            <circle
              cx={x}
              cy={lineY}
              r={isBoundary ? 6 : 5}
              fill={color}
              stroke="white"
              strokeWidth="2"
            />
            <text
              x={x}
              y={lineY + 25}
              textAnchor="middle"
              fontSize="11"
              fill="#475569"
              fontFamily="monospace"
            >
              {pt.value}
            </text>
            <text
              x={x}
              y={lineY + 38}
              textAnchor="middle"
              fontSize="10"
              fill="#64748b"
            >
              {pt.label}
            </text>
          </g>
        );
      })}
    </svg>
  );
}

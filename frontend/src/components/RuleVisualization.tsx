// REQ-NEU: Grafische Regeldarstellung als SVG-Visualisierung
// Zeigt Verbindungen zwischen Werten verschiedener Kategorien als farbige Linien
// Regeltypen: exclude (rot/verboten), dependency (violett/abhängig), combine (grün/kombinieren)
import { useEffect, useState, useRef, useCallback } from "react";
import { rulesApi, categoriesApi } from "../api/client";
import type { Rule } from "../api/client";
import type { Category, Value } from "../types";

interface Props { projectId: number; }

interface RuleWithInfo extends Rule {
  if_category_name: string;
  then_category_name: string;
}

interface ValuePosition {
  id: number;
  value: string;
  categoryId: number;
  x: number;
  y: number;
  width: number;
  height: number;
}

const TYPE_COLORS: Record<string, { line: string; bg: string; text: string; symbol: string; label: string }> = {
  exclude: {
    line: "#ef4444",
    bg: "#fef2f2",
    text: "#dc2626",
    symbol: "✕",
    label: "Verboten",
  },
  dependency: {
    line: "#8b5cf6",
    bg: "#f5f3ff",
    text: "#7c3aed",
    symbol: "→",
    label: "Abhängig",
  },
  combine: {
    line: "#10b981",
    bg: "#ecfdf5",
    text: "#059669",
    symbol: "⊂",
    label: "Kombinieren",
  },
};

// Layout-Konstanten
const CAT_COLUMN_WIDTH = 90;
const CAT_HEADER_HEIGHT = 22;
const VALUE_HEIGHT = 22;
const VALUE_GAP = 5;
const CAT_GAP = 20;
const PADDING = 14;
const LINE_GAP = 4; // Abstand zwischen parallelen Linien

export default function RuleVisualization({ projectId }: Props) {
  const [rules, setRules] = useState<RuleWithInfo[]>([]);
  const [categories, setCategories] = useState<Category[]>([]);
  const [catValues, setCatValues] = useState<Record<number, Value[]>>({});
  const [loading, setLoading] = useState(true);
  const [hoveredRule, setHoveredRule] = useState<RuleWithInfo | null>(null);
  const [viewHeight, setViewHeight] = useState(500); // Anpassbare Höhe (Default größer)
  const [refreshing, setRefreshing] = useState(false);
  
  const svgRef = useRef<SVGSVGElement>(null);
  const resizeHandleRef = useRef<HTMLDivElement>(null);
  const isResizing = useRef(false);

  const loadData = useCallback(async () => {
    setLoading(true);
    try {
      const [ruleList, catList] = await Promise.all([
        rulesApi.list(projectId),
        categoriesApi.list(projectId),
      ]);
      
      // Kategorien-Namen zu Regeln hinzufügen
      const rulesWithInfo: RuleWithInfo[] = ruleList.map(r => ({
        ...r,
        if_category_name: catList.find(c => c.id === r.if_category_id)?.name || `#${r.if_category_id}`,
        then_category_name: catList.find(c => c.id === r.then_category_id)?.name || `#${r.then_category_id}`,
      }));
      
      setRules(rulesWithInfo);
      setCategories(catList);
      
      // Werte für alle Kategorien laden
      const valMap: Record<number, Value[]> = {};
      await Promise.all(catList.map(async (c) => {
        const vals = await categoriesApi.getValues(c.id);
        valMap[c.id] = vals;
      }));
      setCatValues(valMap);
    } finally {
      setLoading(false);
    }
  }, [projectId]);

  useEffect(() => { loadData(); }, [loadData]);

  // Resize-Handler für anpassbare Höhe
  useEffect(() => {
    const handleMouseMove = (e: MouseEvent) => {
      if (!isResizing.current) return;
      const container = resizeHandleRef.current?.parentElement;
      if (!container) return;
      const rect = container.getBoundingClientRect();
      const newHeight = Math.max(250, Math.min(800, rect.bottom - e.clientY));
      setViewHeight(newHeight);
    };
    
    const handleMouseUp = () => {
      isResizing.current = false;
      document.body.style.cursor = '';
      document.body.style.userSelect = '';
    };
    
    const handleMouseDown = (e: MouseEvent) => {
      isResizing.current = true;
      document.body.style.cursor = 'row-resize';
      document.body.style.userSelect = 'none';
      e.preventDefault();
    };
    
    const handle = resizeHandleRef.current;
    if (handle) {
      handle.addEventListener('mousedown', handleMouseDown);
    }
    
    document.addEventListener('mousemove', handleMouseMove);
    document.addEventListener('mouseup', handleMouseUp);
    
    return () => {
      if (handle) handle.removeEventListener('mousedown', handleMouseDown);
      document.removeEventListener('mousemove', handleMouseMove);
      document.removeEventListener('mouseup', handleMouseUp);
    };
  }, []);

  if (loading) {
    return (
      <div className="flex items-center justify-center py-8 text-sm text-theme-text-secondary animate-pulse">
        Lade Regeln...
      </div>
    );
  }

  if (rules.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center py-8 text-theme-text-secondary text-xs text-center">
        <span className="text-2xl mb-2 opacity-50">📋</span>
        <p>Noch keine Regeln</p>
        <p className="mt-1 opacity-70">Erstelle Regeln im "Regeln"-Tab</p>
      </div>
    );
  }

  // Berechne SVG-Dimensionen und Wert-Positionen
  const relevantCategories = categories.filter(c => 
    rules.some(r => r.if_category_id === c.id || r.then_category_id === c.id)
  );
  
  const valuePositions: ValuePosition[] = [];
  let currentX = PADDING;
  
  const catXMap: Record<number, number> = {};
  const valuePosMap: Record<string, ValuePosition> = {}; // "catId-value" -> position
  
  for (const cat of relevantCategories) {
    catXMap[cat.id] = currentX;
    const vals = catValues[cat.id] || [];
    
    let currentY = PADDING + CAT_HEADER_HEIGHT;
    for (const val of vals) {
      const pos: ValuePosition = {
        id: val.id,
        value: val.value,
        categoryId: cat.id,
        x: currentX,
        y: currentY,
        width: CAT_COLUMN_WIDTH,
        height: VALUE_HEIGHT,
      };
      valuePositions.push(pos);
      valuePosMap[`${cat.id}-${val.value}`] = pos;
      currentY += VALUE_HEIGHT + VALUE_GAP;
    }
    
    currentX += CAT_COLUMN_WIDTH + CAT_GAP;
  }
  
  const svgWidth = currentX - CAT_GAP + PADDING;
  const svgHeight = Math.max(viewHeight, 
    Math.max(...valuePositions.map(v => v.y + v.height)) + PADDING
  );

  // Berechne Linien für jede Regel
  const ruleLines = rules.map((rule) => {
    const fromPos = valuePosMap[`${rule.if_category_id}-${rule.if_value}`];
    const toPos = valuePosMap[`${rule.then_category_id}-${rule.then_value}`];
    
    if (!fromPos || !toPos) return null;
    
    // Finde parallele Linien zwischen denselben Kategorien
    const parallelCount = rules.filter(r => 
      r.if_category_id === rule.if_category_id && 
      r.then_category_id === rule.then_category_id &&
      r.id <= rule.id
    ).length;
    
    const offset = (parallelCount - 1) * LINE_GAP;
    
    const typeColor = TYPE_COLORS[rule.type] || TYPE_COLORS.exclude;
    
    // Berechne Start- und Endpunkte
    const startX = fromPos.x + fromPos.width;
    const startY = fromPos.y + fromPos.height / 2 + offset;
    const endX = toPos.x;
    const endY = toPos.y + toPos.height / 2 + offset;
    
    // Kurve erstellen
    const midX = (startX + endX) / 2;
    const path = `M ${startX} ${startY} C ${midX} ${startY}, ${midX} ${endY}, ${endX} ${endY}`;
    
    return {
      rule,
      path,
      midX,
      midY: (startY + endY) / 2,
      color: typeColor,
      isHovered: hoveredRule?.id === rule.id,
    };
  }).filter(Boolean);

  return (
    <div className="flex flex-col h-full">
      {/* Header */}
      <div className="flex items-center justify-between px-1 py-2 border-b border-theme-border">
        <span className="text-xs font-semibold text-theme-text-secondary uppercase tracking-wide">
          Regeln ({rules.length})
        </span>
        <div className="flex items-center gap-1">
          <button
            onClick={() => { setRefreshing(true); loadData().finally(() => setRefreshing(false)); }}
            className={'text-[10px] px-1.5 py-0.5 rounded bg-theme-surface-hover text-theme-text-secondary hover:text-theme-text transition-colors ' +
            (refreshing ? "animate-spin" : "")}
            title="Aktualisieren"
            disabled={refreshing}
          >
            ↻
          </button>
          {Object.entries(TYPE_COLORS).map(([type, color]) => {
            const count = rules.filter(r => r.type === type).length;
            if (count === 0) return null;
            return (
              <span
                key={type}
                className="text-[10px] px-1.5 py-0.5 rounded"
                style={{ backgroundColor: color.bg, color: color.text }}
                title={`${color.label}: ${count}`}
              >
                {color.symbol} {count}
              </span>
            );
          })}
        </div>
      </div>
      
      {/* SVG-Bereich mit Scroll */}
      <div 
        className="flex-1 overflow-auto relative"
        style={{ minHeight: `${viewHeight}px`, maxHeight: `${viewHeight}px` }}
      >
        <svg
          ref={svgRef}
          width={svgWidth}
          height={svgHeight}
          viewBox={`0 0 ${svgWidth} ${svgHeight}`}
          className="block"
        >
          {/* Kategorien-Spalten */}
          {relevantCategories.map((cat) => {
            const x = catXMap[cat.id];
            const vals = catValues[cat.id] || [];
            const colHeight = vals.length * (VALUE_HEIGHT + VALUE_GAP) - VALUE_GAP + CAT_HEADER_HEIGHT + PADDING * 2;
            
            return (
              <g key={cat.id}>
                {/* Spalten-Hintergrund */}
                <rect
                  x={x - 4}
                  y={PADDING - 4}
                  width={CAT_COLUMN_WIDTH + 8}
                  height={colHeight}
                  rx={6}
                  fill="#f8fafc"
                  stroke="#e2e8f0"
                  strokeWidth={hoveredRule && (hoveredRule.if_category_id === cat.id || hoveredRule.then_category_id === cat.id) ? 2 : 1}
                  style={{
                    stroke: hoveredRule && (hoveredRule.if_category_id === cat.id || hoveredRule.then_category_id === cat.id)
                      ? TYPE_COLORS[hoveredRule.type]?.line || '#e2e8f0'
                      : '#e2e8f0',
                    transition: 'stroke 0.2s',
                  }}
                />
                
                {/* Kategorie-Name */}
                <text
                  x={x + CAT_COLUMN_WIDTH / 2}
                  y={PADDING + 14}
                  textAnchor="middle"
                  fontSize={9}
                  fontWeight={600}
                  fill="#1e293b"
                >
                  {cat.name.length > 10 ? cat.name.slice(0, 9) + '…' : cat.name}
                </text>
                
                {/* Werte */}
                {vals.map((val, vIdx) => {
                  const y = PADDING + CAT_HEADER_HEIGHT + vIdx * (VALUE_HEIGHT + VALUE_GAP);
                  const pos = valuePosMap[`${cat.id}-${val.value}`];
                  if (!pos) return null;
                  
                  // Prüfe ob dieser Wert in einer gehoverten Regel vorkommt
                  const isHighlighted = hoveredRule && (
                    (hoveredRule.if_category_id === cat.id && hoveredRule.if_value === val.value) ||
                    (hoveredRule.then_category_id === cat.id && 
                      (hoveredRule.then_value === val.value || 
                       (hoveredRule.then_values_json && 
                        JSON.parse(hoveredRule.then_values_json).includes(val.value))))
                  );
                  
                  return (
                    <g key={val.id}>
                      <rect
                        x={x}
                        y={y}
                        width={CAT_COLUMN_WIDTH}
                        height={VALUE_HEIGHT}
                        rx={3}
                        fill={isHighlighted ? '#f0f9ff' : 'white'}
                        stroke={isHighlighted ? '#0ea5e9' : '#e2e8f0'}
                        strokeWidth={isHighlighted ? 1.5 : 1}
                        style={{ transition: 'all 0.2s' }}
                      />
                      <text
                        x={x + CAT_COLUMN_WIDTH / 2}
                        y={y + VALUE_HEIGHT / 2 + 3}
                        textAnchor="middle"
                        fontSize={8}
                        fill="#1e293b"
                      >
                        {val.value.length > 8 ? val.value.slice(0, 7) + '…' : val.value}
                      </text>
                    </g>
                  );
                })}
              </g>
            );
          })}
          
          {/* Verbindungslinien */}
          {ruleLines.map((line) => {
            if (!line) return null;
            
            const isDashed = line.rule.type === 'exclude' || line.rule.type === 'combine';
            
            return (
              <g
                key={line.rule.id}
                onMouseEnter={() => setHoveredRule(line.rule)}
                onMouseLeave={() => setHoveredRule(null)}
                style={{ cursor: 'help' }}
              >
                {/* Unsichtbare breitere Hit-Area für einfacheres Hover */}
                <path
                  d={line.path}
                  stroke="transparent"
                  strokeWidth={12}
                  fill="none"
                />
                
                {/* Sichtbare Linie */}
                <path
                  d={line.path}
                  stroke={line.color.line}
                  strokeWidth={line.isHovered ? 3 : 2}
                  fill="none"
                  strokeDasharray={isDashed ? (line.rule.type === 'exclude' ? '4,2' : '3,1') : 'none'}
                  style={{ transition: 'stroke-width 0.2s' }}
                />
                
                {/* Symbol in der Mitte */}
                <circle
                  cx={line.midX}
                  cy={line.midY}
                  r={line.isHovered ? 9 : 7}
                  fill={line.color.bg}
                  stroke={line.color.line}
                  strokeWidth={1.5}
                  style={{ transition: 'all 0.2s' }}
                />
                <text
                  x={line.midX}
                  y={line.midY + 3}
                  textAnchor="middle"
                  fontSize={line.isHovered ? 9 : 8}
                  fill={line.color.text}
                  style={{ transition: 'all 0.2s' }}
                >
                  {line.color.symbol}
                </text>
                
                {/* Custom Tooltip */}
                {line.isHovered && (
                  <g>
                    <rect
                      x={line.midX - 60}
                      y={line.midY - 45}
                      width={120}
                      height={36}
                      rx={4}
                      fill="#1e293b"
                      opacity={0.9}
                    />
                    <text
                      x={line.midX}
                      y={line.midY - 30}
                      textAnchor="middle"
                      fontSize={8}
                      fill="white"
                      fontWeight={600}
                    >
                      Wenn {line.rule.if_category_name} = {line.rule.if_value}
                    </text>
                    <text
                      x={line.midX}
                      y={line.midY - 18}
                      textAnchor="middle"
                      fontSize={8}
                      fill="#94a3b8"
                    >
                      {line.rule.type === 'exclude' ? '✕ nicht mit' : 
                       line.rule.type === 'dependency' ? '→ dann' : 
                       '⊂ nur mit'} {line.rule.then_category_name}
                    </text>
                    {/* Pfeil nach unten */}
                    <polygon
                      points={`${line.midX},${line.midY - 9} ${line.midX - 4},${line.midY - 5} ${line.midX + 4},${line.midY - 5}`}
                      fill="#1e293b"
                      opacity={0.9}
                    />
                  </g>
                )}
              </g>
            );
          })}
        </svg>
      </div>
      
      {/* Resize-Handle */}
      <div
        ref={resizeHandleRef}
        className="h-1.5 w-full cursor-row-resize hover:bg-theme-accent/20 transition-colors"
        title="Höhe anpassen (ziehen)"
      />
    </div>
  );
}
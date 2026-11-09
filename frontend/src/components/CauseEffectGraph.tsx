/**
 * REQ-5018: Cause-Effect-Graph-Visualisierung
 * Ursachen links, Wirkungen rechts, Constraints als Kanten
 * SVG-basierte Graph-Ansicht mit Hover-Feedback und Legend
 */
import { useEffect, useState, useRef } from "react";

interface GraphNode {
  id: string;
  name: string;
  x: number;
  y: number;
  type: "cause" | "effect";
}

interface GraphEdge {
  from: string;
  to: string;
  type: string;
  label: string;
}

interface CauseEffectGraphProps {
  projectId: number;
}

const EDGE_COLORS: Record<string, string> = {
  E: "#ef4444", // red - Exclusive
  O: "#3b82f6", // blue - One-and-Only-One
  I: "#22c55e", // green - Inclusive
  requires: "#f97316", // orange - Requires
  mask: "#a855f7", // purple - Mask
};

const NODE_WIDTH = 80;
const NODE_HEIGHT = 30;
const CAUSE_X = 120;
const EFFECT_X = 500;
const NODE_SPACING = 60;
const SVG_WIDTH = 650;

export default function CauseEffectGraph({ projectId }: CauseEffectGraphProps) {
  const [nodes, setNodes] = useState<GraphNode[]>([]);
  const [edges, setEdges] = useState<GraphEdge[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [hoveredNode, setHoveredNode] = useState<string | null>(null);
  const svgRef = useRef<SVGSVGElement>(null);

  // EPIC-20 Schulden: Zoom/Pan
  const [zoom, setZoom] = useState(1);
  const [pan, setPan] = useState({ x: 0, y: 0 });
  const [isDragging, setIsDragging] = useState(false);
  const [dragStart, setDragStart] = useState({ x: 0, y: 0 });

  useEffect(() => {
    setLoading(true);
    setError(null);

    fetch(`/api/decision-table/graph/${projectId}`, { credentials: "include" })
      .then((r) => {
        if (!r.ok) throw new Error("Fehler beim Laden");
        return r.json();
      })
      .then((data) => {
        const nodeList: GraphNode[] = [];

        // Position causes on the left
        data.causes?.forEach((c: { id: number; name: string }, i: number) => {
          nodeList.push({
            id: `cause:${c.id}`,
            name: c.name,
            x: CAUSE_X,
            y: 40 + i * NODE_SPACING,
            type: "cause",
          });
        });

        // Position effects on the right
        data.effects?.forEach((e: { id: number; name: string }, i: number) => {
          nodeList.push({
            id: `effect:${e.id}`,
            name: e.name,
            x: EFFECT_X,
            y: 40 + i * NODE_SPACING,
            type: "effect",
          });
        });

        setNodes(nodeList);
        setEdges(
          (data.edges || []).map((e: { from: string; to: string; type: string; label: string }) => ({
            from: e.from,
            to: e.to,
            type: e.type,
            label: e.label,
          }))
        );
        setLoading(false);
      })
      .catch((e) => {
        setError(e instanceof Error ? e.message : String(e));
        setLoading(false);
      });
  }, [projectId]);

  if (loading) return <div className="p-4 text-theme-text-secondary animate-pulse">Graph laedt...</div>;
  if (error) return <div className="p-4 text-theme-danger">{error}</div>;

  const causeNodes = nodes.filter((n) => n.type === "cause");
  const effectNodes = nodes.filter((n) => n.type === "effect");

  if (causeNodes.length === 0 && effectNodes.length === 0)
    return <div className="p-4 text-theme-text-secondary">Keine Ursache/Wirkung fuer Graph</div>;

  const getHeight = () =>
    Math.max(200, Math.max(causeNodes.length, effectNodes.length) * NODE_SPACING + 80);

  const getNode = (id: string) => nodes.find((n) => n.id === id);

  return (
    <div className="border border-theme-border rounded-lg overflow-auto">
      {/* EPIC-20 Schulden: Zoom/Pan Controls */}
      <div className="flex gap-2 mb-2 p-2">
        <button
          onClick={() => setZoom((z) => Math.max(0.5, z - 0.1))}
          className="px-2 py-1 text-sm border border-theme-border rounded text-theme-text"
          aria-label="Verkleinern"
        >
          −
        </button>
        <span className="text-sm text-theme-text self-center">{Math.round(zoom * 100)}%</span>
        <button
          onClick={() => setZoom((z) => Math.min(2, z + 0.1))}
          className="px-2 py-1 text-sm border border-theme-border rounded text-theme-text"
          aria-label="Vergrossern"
        >
          +
        </button>
        <button
          onClick={() => {
            setZoom(1);
            setPan({ x: 0, y: 0 });
          }}
          className="px-2 py-1 text-sm border border-theme-border rounded text-theme-text"
          aria-label="Zoom zuruecksetzen"
        >
          Reset
        </button>
      </div>

      <svg
        ref={svgRef}
        width={SVG_WIDTH}
        height={getHeight()}
        style={{
          transform: `translate(${pan.x}px, ${pan.y}px) scale(${zoom})`,
          transformOrigin: "0 0",
          cursor: isDragging ? "grabbing" : "grab",
        }}
        onMouseDown={(e) => {
          setIsDragging(true);
          setDragStart({ x: e.clientX - pan.x, y: e.clientY - pan.y });
        }}
        onMouseMove={(e) => {
          if (isDragging) {
            setPan({ x: e.clientX - dragStart.x, y: e.clientY - dragStart.y });
          }
        }}
        onMouseUp={() => setIsDragging(false)}
        onMouseLeave={() => setIsDragging(false)}
        className="bg-theme-bg"
        role="img"
        aria-label="Cause-Effect-Graph Visualisierung"
      >
        {/* Edges */}
        {edges.map((edge, i) => {
          const fromNode = getNode(edge.from);
          const toNode = getNode(edge.to);
          if (!fromNode || !toNode) return null;

          const color = EDGE_COLORS[edge.type] || "#6b7280";

          return (
            <g key={i}>
              <line
                x1={fromNode.x}
                y1={fromNode.y}
                x2={toNode.x}
                y2={toNode.y}
                stroke={color}
                strokeWidth={2}
                strokeDasharray={edge.type === "mask" ? "5,5" : "none"}
              />
              {/* Label */}
              <text
                x={(fromNode.x + toNode.x) / 2}
                y={(fromNode.y + toNode.y) / 2 - 5}
                textAnchor="middle"
                fill={color}
                fontSize="10"
              >
                {edge.label}
              </text>
            </g>
          );
        })}

        {/* Nodes */}
        {nodes.map((node) => (
          <g
            key={node.id}
            onMouseEnter={() => setHoveredNode(node.id)}
            onMouseLeave={() => setHoveredNode(null)}
            className="cursor-pointer"
            role="button"
            aria-label={`${node.type === "cause" ? "Ursache" : "Wirkung"}: ${node.name}`}
          >
            <rect
              x={node.x - NODE_WIDTH / 2}
              y={node.y - NODE_HEIGHT / 2}
              width={NODE_WIDTH}
              height={NODE_HEIGHT}
              rx={5}
              fill={node.type === "cause" ? "#3b82f6" : "#22c55e"}
              opacity={hoveredNode === node.id ? 1 : 0.8}
            />
            <text
              x={node.x}
              y={node.y + 5}
              textAnchor="middle"
              fill="white"
              fontSize="12"
              fontWeight="bold"
            >
              {node.name.length > 10 ? node.name.slice(0, 9) + "\u2026" : node.name}
            </text>
          </g>
        ))}
      </svg>

      {/* Legend */}
      <div className="p-3 flex flex-wrap gap-4 text-xs text-theme-text-secondary border-t border-theme-border">
        <span>
          <span className="inline-block w-3 h-3 rounded-full bg-blue-500 mr-1"></span>Ursache
        </span>
        <span>
          <span className="inline-block w-3 h-3 rounded-full bg-green-500 mr-1"></span>Wirkung
        </span>
        {Object.entries(EDGE_COLORS).map(([type, color]) => (
          <span key={type}>
            <span
              className="inline-block w-4 h-0.5 mr-1 align-middle"
              style={{ backgroundColor: color }}
            ></span>
            {type}
          </span>
        ))}
      </div>
    </div>
  );
}
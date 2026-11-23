// REQ-6006: Klassifikationsbaum als SVG mit Edit-Funktionen
import { useCallback, useRef, useState } from "react";
import { useTranslation } from "react-i18next";
import { useCategoryStore } from "../store/categoryStore";
import { useProjectStore } from "../store/projectStore";
import { computeTreeLayout } from "../lib/classificationTreeLayout";
import type { TreeNode } from "../lib/classificationTreeLayout";

interface Props {
  projectId: number;
}

export default function ClassificationTreeView({ projectId }: Props) {
  const { t } = useTranslation();
  const { categories, values, createCategory, deleteCategory } = useCategoryStore();
  const { projects } = useProjectStore();
  const project = projects.find((p) => p.id === projectId);

  const [zoom, setZoom] = useState(1);
  const [editingId, setEditingId] = useState<string | null>(null);
  const [editText, setEditText] = useState("");
  const svgRef = useRef<SVGSVGElement>(null);

  // Build layout data
  const layoutCats = categories.map((c) => ({
    id: c.id,
    name: c.name,
    isResult: c.is_result ?? false,
    values: (values[c.id] ?? []).map((v) => ({
      name: v.value,
      isError: !v.allowed,
      isDefault: v.is_default,
    })),
  }));

  const layout = computeTreeLayout(
    project?.name ?? t("classificationTree.project", { defaultValue: "Projekt" }),
    layoutCats,
  );

  // Zoom handlers
  const handleWheel = useCallback(
    (e: React.WheelEvent) => {
      if (e.ctrlKey) {
        e.preventDefault();
        const delta = e.deltaY > 0 ? -0.1 : 0.1;
        setZoom((z) => Math.max(0.2, Math.min(3, z + delta)));
      }
    },
    [],
  );

  const handleZoomIn = () => setZoom((z) => Math.min(3, z + 0.2));
  const handleZoomOut = () => setZoom((z) => Math.max(0.2, z - 0.2));
  const handleFit = () => setZoom(1);

  // Edit handlers
  const startEdit = (node: TreeNode) => {
    setEditingId(node.id);
    setEditText(node.label);
  };

  const commitEdit = () => {
    if (!editingId) return;
    // TODO: implement rename via API
    setEditingId(null);
    setEditText("");
  };

  const handleDelete = (node: TreeNode) => {
    if (node.type === "category" && node.categoryId) {
      if (confirm(t("classificationTree.deleteConfirm", { defaultValue: "Kategorie loeschen?" }))) {
        deleteCategory(node.categoryId);
      }
    }
  };

  const nodeColor = (node: TreeNode) => {
    if (node.isResult) return "#f59e0b";
    if (node.isError) return "#ef4444";
    if (node.type === "root") return "#0ea5e9";
    if (node.type === "category") return "#6366f1";
    return "#10b981";
  };

  return (
    <div className="flex flex-col h-full">
      {/* Zoom Controls */}
      <div className="flex items-center gap-2 px-3 py-2 border-b border-slate-200">
        <button
          onClick={handleZoomOut}
          className="px-2 py-1 text-sm bg-white border border-slate-300 rounded hover:bg-slate-50"
          title={t("classificationTree.zoomOut", { defaultValue: "Verkleinern" })}
        >
          −
        </button>
        <span className="text-xs text-slate-500 w-12 text-center">{Math.round(zoom * 100)}%</span>
        <button
          onClick={handleZoomIn}
          className="px-2 py-1 text-sm bg-white border border-slate-300 rounded hover:bg-slate-50"
          title={t("classificationTree.zoomIn", { defaultValue: "Vergruessern" })}
        >
          +
        </button>
        <button
          onClick={handleFit}
          className="px-2 py-1 text-sm text-slate-500 hover:text-slate-700"
          title={t("classificationTree.fit", { defaultValue: "Einpassen" })}
        >
          {t("classificationTree.fit", { defaultValue: "Einpassen" })}
        </button>
        <div className="flex-1" />
        <button
          onClick={() => {
            createCategory(
              projectId,
              t("classificationTree.newCategory", { defaultValue: "Neue Kategorie" })
            );
          }}
          className="px-3 py-1 text-sm bg-sky-600 text-white rounded hover:bg-sky-700"
        >
          + {t("classificationTree.addCategory", { defaultValue: "Kategorie" })}
        </button>
      </div>

      {/* SVG Canvas */}
      <div
        className="flex-1 overflow-auto"
        onWheel={handleWheel}
        tabIndex={0}
      >
        <svg
          ref={svgRef}
          data-tree="true"
          width={layout.totalWidth * zoom}
          height={layout.totalHeight * zoom}
          viewBox={`0 0 ${layout.totalWidth} ${layout.totalHeight}`}
          className="bg-white"
        >
          {layout.nodes.map((node) => (
            <g key={node.id} data-node-id={node.id}>
              <rect
                x={node.x}
                y={node.y}
                width={node.width}
                height={node.height}
                rx={node.type === "root" ? 20 : 4}
                fill={nodeColor(node)}
                fillOpacity={node.type === "value" ? 0.15 : 0.85}
                stroke={nodeColor(node)}
                strokeWidth={node.type === "root" ? 2 : 1}
                onDoubleClick={() => startEdit(node)}
                className="cursor-pointer"
              />
              {editingId === node.id ? (
                <foreignObject x={node.x} y={node.y} width={node.width} height={node.height}>
                  <input
                    autoFocus
                    className="w-full h-full px-2 text-xs bg-white border border-sky-400 rounded text-black"
                    value={editText}
                    onChange={(e) => setEditText(e.target.value)}
                    onBlur={commitEdit}
                    onKeyDown={(e) => {
                      if (e.key === "Enter") commitEdit();
                      if (e.key === "Escape") { setEditingId(null); setEditText(""); }
                    }}
                  />
                </foreignObject>
              ) : (
                <text
                  x={node.x + node.width / 2}
                  y={node.y + node.height / 2}
                  textAnchor="middle"
                  dominantBaseline="central"
                  fontSize={node.type === "root" ? 14 : node.type === "category" ? 12 : 11}
                  fill="currentColor"
                  className="pointer-events-none"
                >
                  {node.label}
                  {node.isResult && " ★"}
                  {node.isError && " ⚠"}
                </text>
              )}
              {node.type === "category" && (
                <text
                  x={node.x + node.width - 12}
                  y={node.y + 12}
                  fontSize={10}
                  fill="#94a3b8"
                  className="cursor-pointer"
                  onClick={(e) => {
                    e.stopPropagation();
                    handleDelete(node);
                  }}
                >
                  ×
                </text>
              )}
            </g>
          ))}
        </svg>
      </div>
    </div>
  );
}
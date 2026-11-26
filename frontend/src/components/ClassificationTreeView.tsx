// REQ-6006: Klassifikationsbaum als SVG mit Edit-Funktionen
// REQ-6016: Hierarchische Klassen (Verfeinerung)
import { useCallback, useEffect, useRef, useState } from "react";
import { useTranslation } from "react-i18next";
import { useCategoryStore } from "../store/categoryStore";
import { useProjectStore } from "../store/projectStore";
import { computeTreeLayout } from "../lib/classificationTreeLayout";
import type { TreeNode } from "../lib/classificationTreeLayout";
import { categoriesApi } from "../api/client";
import { deleteWithConstraintCheck } from "../lib/constraintReference";

interface Props {
  projectId: number;
}

// REQ-6016: Refine Dialog Component
function RefineDialog({
  categoryId,
  valueName,
  onClose,
  onSuccess,
}: {
  categoryId: number;
  valueName: string;
  onClose: () => void;
  onSuccess: (name: string) => void;
}) {
  const { t } = useTranslation();
  const [name, setName] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const inputRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    inputRef.current?.focus();
  }, []);

  const handleSubmit = async () => {
    if (!name.trim()) return;
    setLoading(true);
    setError(null);
    try {
      await categoriesApi.refine(categoryId, name.trim());
      onSuccess(name.trim());
    } catch (e: any) {
      setError(e?.message || String(e));
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="fixed inset-0 bg-black/30 flex items-center justify-center z-50" onClick={onClose}>
      <div
        className="bg-white rounded-lg shadow-xl p-6 w-96"
        onClick={(e) => e.stopPropagation()}
      >
        <h3 className="text-lg font-semibold mb-4">
          {t("classificationTree.refineDialog.title", { valueName })}
        </h3>
        <input
          ref={inputRef}
          className="w-full px-3 py-2 border border-slate-300 rounded mb-2"
          placeholder={t("classificationTree.refineDialog.namePlaceholder")}
          value={name}
          onChange={(e) => setName(e.target.value)}
          onKeyDown={(e) => {
            if (e.key === "Enter") handleSubmit();
            if (e.key === "Escape") onClose();
          }}
        />
        {error && <p className="text-red-500 text-sm mb-2">{error}</p>}
        <div className="flex justify-end gap-2">
          <button
            className="px-3 py-1 text-sm border border-slate-300 rounded hover:bg-slate-50"
            onClick={onClose}
          >
            {t("classificationTree.refineDialog.cancel")}
          </button>
          <button
            className="px-3 py-1 text-sm bg-sky-600 text-white rounded hover:bg-sky-700 disabled:opacity-50"
            onClick={handleSubmit}
            disabled={loading || !name.trim()}
          >
            {loading ? "..." : t("classificationTree.refineDialog.create")}
          </button>
        </div>
      </div>
    </div>
  );
}

// REQ-6016: Context Menu Component
function ContextMenu({
  x,
  y,
  items,
  onClose,
}: {
  x: number;
  y: number;
  items: { label: string; onClick: () => void; danger?: boolean }[];
  onClose: () => void;
}) {
  return (
    <div
      className="fixed bg-white border border-slate-200 rounded shadow-lg z-50 py-1 min-w-[160px]"
      style={{ left: x, top: y }}
      onClick={(e) => e.stopPropagation()}
    >
      {items.map((item, i) => (
        <button
          key={i}
          className={`w-full text-left px-3 py-1.5 text-sm hover:bg-slate-100 ${
            item.danger ? "text-red-600" : ""
          }`}
          onClick={() => {
            item.onClick();
            onClose();
          }}
        >
          {item.label}
        </button>
      ))}
    </div>
  );
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

  // REQ-6016: Refine dialog state
  const [refineTarget, setRefineTarget] = useState<{
    categoryId: number;
    valueName: string;
  } | null>(null);

  // REQ-6016: Context menu state
  const [contextMenu, setContextMenu] = useState<{
    x: number;
    y: number;
    node: TreeNode;
  } | null>(null);

  // Build layout data with hierarchy info
  const layoutCats = categories.map((c) => ({
    id: c.id,
    name: c.name,
    isResult: c.is_result ?? false,
    values: (values[c.id] ?? []).map((v) => ({
      name: v.value,
      isError: !v.allowed,
      isDefault: v.is_default,
      parentId: v.parent_value_id ?? null, // REQ-6016
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
        const categoryId = node.categoryId;
        // REQ-6001 AK-10: bei verweisenden Constraints nachfragen
        deleteWithConstraintCheck(
          (force) => deleteCategory(categoryId, force),
          (names) => confirm(t("categoryTree.constraintReferenceConfirm", { names: names.join(", ") })),
        ).catch((e: unknown) => alert(e instanceof Error ? e.message : String(e)));
      }
    }
  };

  // REQ-6016: Handle refine action
  const handleRefine = (node: TreeNode) => {
    if (node.type === "value" && node.categoryId) {
      setRefineTarget({ categoryId: node.categoryId, valueName: node.label });
    }
  };

  // REQ-6016: Context menu handler
  const handleContextMenu = (e: React.MouseEvent, node: TreeNode) => {
    e.preventDefault();
    setContextMenu({ x: e.clientX, y: e.clientY, node });
  };

  // Close context menu on click outside
  useEffect(() => {
    const handler = () => setContextMenu(null);
    window.addEventListener("click", handler);
    return () => window.removeEventListener("click", handler);
  }, []);

  // REQ-6016: Build context menu items
  const getContextMenuItems = (node: TreeNode) => {
    const items: { label: string; onClick: () => void; danger?: boolean }[] = [];

    if (node.type === "category" && node.categoryId) {
      items.push({
        label: t("categoryTree.contextMenu.rename", { defaultValue: "Umbenennen (F2)" }),
        onClick: () => startEdit(node),
      });
      items.push({
        label: t("categoryTree.contextMenu.addValue", { defaultValue: "Wert hinzufuegen" }),
        onClick: () => {}, // TODO: implement
      });
      items.push({
        label: t("categoryTree.contextMenu.delete", { defaultValue: "Loeschen" }),
        onClick: () => handleDelete(node),
        danger: true,
      });
    }

    if (node.type === "value" && node.categoryId) {
      // REQ-6016: "Verfeinern" context menu item
      items.push({
        label: t("classificationTree.refine", { defaultValue: "Verfeinern..." }),
        onClick: () => handleRefine(node),
      });
      items.push({
        label: t("contextMenu.rename", { defaultValue: "Umbenennen (F2)" }),
        onClick: () => startEdit(node),
      });
      items.push({
        label: t("contextMenu.delete", { defaultValue: "Loeschen" }),
        onClick: () => {}, // TODO: implement value delete
        danger: true,
      });
    }

    return items;
  };

  const nodeColor = (node: TreeNode) => {
    if (node.isResult) return "#f59e0b";
    if (node.isError) return "#ef4444";
    if (node.type === "root") return "#0ea5e9";
    if (node.type === "category") return "#6366f1";
    return "#10b981";
  };

  // REQ-6016: Check if node is a sub-category (indented)
  const isSubCategory = (node: TreeNode): boolean => {
    return node.parentId !== undefined && node.parentId !== null;
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
            <g
              key={node.id}
              data-node-id={node.id}
              onContextMenu={(e) => handleContextMenu(e, node)}
            >
              <rect
                x={node.x}
                y={node.y}
                width={node.width}
                height={node.height}
                rx={node.type === "root" ? 20 : 4}
                fill={nodeColor(node)}
                fillOpacity={
                  node.type === "value"
                    ? isSubCategory(node)
                      ? 0.1
                      : 0.15
                    : 0.85
                }
                stroke={nodeColor(node)}
                strokeWidth={node.type === "root" ? 2 : isSubCategory(node) ? 0.5 : 1}
                strokeDasharray={isSubCategory(node) ? "3,3" : "none"}
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
                      if (e.key === "Escape") {
                        setEditingId(null);
                        setEditText("");
                      }
                    }}
                  />
                </foreignObject>
              ) : (
                <text
                  x={node.x + (isSubCategory(node) ? 12 : node.width / 2)}
                  y={node.y + node.height / 2}
                  textAnchor={isSubCategory(node) ? "start" : "middle"}
                  dominantBaseline="central"
                  fontSize={
                    node.type === "root"
                      ? 14
                      : node.type === "category"
                        ? 12
                        : isSubCategory(node)
                          ? 10
                          : 11
                  }
                  fill="currentColor"
                  className="pointer-events-none"
                >
                  {isSubCategory(node) && "└ "}
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

      {/* REQ-6016: Refine Dialog */}
      {refineTarget && (
        <RefineDialog
          categoryId={refineTarget.categoryId}
          valueName={refineTarget.valueName}
          onClose={() => setRefineTarget(null)}
          onSuccess={() => {
            setRefineTarget(null);
            // TODO: show toast
          }}
        />
      )}

      {/* REQ-6016: Context Menu */}
      {contextMenu && (
        <ContextMenu
          x={contextMenu.x}
          y={contextMenu.y}
          items={getContextMenuItems(contextMenu.node)}
          onClose={() => setContextMenu(null)}
        />
      )}
    </div>
  );
}
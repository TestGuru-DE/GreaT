// REQ-6006: Klassifikationsbaum mit Testfallmatrix (ein SVG fuer Baum und Matrix)
// REQ-6016: Hierarchische Klassen (Verfeinerung)
//
// Bugfixes:
// - C-15: alle Klassen werden geladen (nicht erst nach Aufklappen in der Kategorien-Ansicht)
// - C-16: Matrix mit einer Spalte je Klasse und Punkt (●), exakt unter den Klassen
// - C-17: Umbenennen (Doppelklick/F2), Loeschen (Entf), Hinzufuegen, Reihenfolge per
//         Ziehen oder Alt+Pfeil – alles sofort im Modell
// - C-18: Undo/Redo ueber den Store wirkt auf dem Server (Strg+Z / Strg+Y)
// - C-19: manuelle Testfaelle in der Matrix, Regelverstoesse sofort markiert,
//         Speichern als Seed-Satz (REQ-6009)
// - C-20: Export SVG/PNG mit oder ohne Matrix
// - C-21: feste Farben mit Kontrast >= 4,5:1 in allen Themes
// - C-22: Ergebnis, Fehlerwert und Standardwert mit Symbol UND Beschriftung, Legende
// - C-23: Strg+Mausrad zoomt nur den Baum, "Einpassen" passt an die Flaeche an
import { useEffect, useMemo, useRef, useState } from "react";
import { useTranslation } from "react-i18next";
import { useCategoryStore } from "../store/categoryStore";
import { useProjectStore } from "../store/projectStore";
import { computeTreeLayout, LEFT_MARGIN, ROW_HEIGHT } from "../lib/classificationTreeLayout";
import type { TreeColumn, TreeNode } from "../lib/classificationTreeLayout";
import { buildExportSvg, downloadBlob, svgToPng } from "../lib/classificationTreeExport";
import { categoriesApi, generateApi, seedApi, testcaseCheckApi } from "../api/client";
import type { TestcaseCheckResult } from "../api/client";
import type { TestCaseOut } from "../types";
import { deleteWithConstraintCheck } from "../lib/constraintReference";

interface Props {
  projectId: number;
}

// C-21: Farben mit ausreichendem Kontrast (Text auf Flaeche >= 4,5:1), unabhaengig vom Theme
export const TREE_COLORS = {
  background: "#ffffff",
  line: "#475569",
  rootFill: "#0c4a6e",
  rootText: "#ffffff",
  categoryFill: "#312e81",
  categoryText: "#ffffff",
  resultFill: "#7c2d12",
  classFill: "#ffffff",
  classStroke: "#334155",
  classText: "#0f172a",
  errorFill: "#fef2f2",
  errorStroke: "#b91c1c",
  errorText: "#7f1d1d",
  selected: "#0369a1",
  grid: "#e2e8f0",
  dot: "#0f172a",
  rowText: "#0f172a",
  invalidRow: "#fee2e2",
  incompleteRow: "#ffedd5",
  manualRow: "#f0f9ff",
};
const FONT = "system-ui, -apple-system, 'Segoe UI', Roboto, sans-serif";

type Selection =
  | { type: "category"; categoryId: number }
  | { type: "value"; categoryId: number; valueId: number }
  | null;

interface ManualRow {
  key: number;
  assignment: Record<string, string>;
  check?: TestcaseCheckResult;
}

interface MatrixRow {
  key: string;
  label: string;
  assignment: Record<string, string>;
  manual?: ManualRow;
}

const MATRIX_GAP = 40;
const MIN_ZOOM = 0.2;
const MAX_ZOOM = 3;

function truncate(label: string, width: number): string {
  const max = Math.max(3, Math.floor((width - 12) / 7));
  return label.length > max ? label.slice(0, max - 1) + "…" : label;
}

function uniqueName(base: string, existing: string[]): string {
  if (!existing.includes(base)) return base;
  let n = 2;
  while (existing.includes(`${base} ${n}`)) n++;
  return `${base} ${n}`;
}

// REQ-6016: Dialog fuer Verfeinerung (unveraendert uebernommen)
function RefineDialog({ categoryId, valueName, onClose, onSuccess }: {
  categoryId: number; valueName: string; onClose: () => void; onSuccess: (name: string) => void;
}) {
  const { t } = useTranslation();
  const [name, setName] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const submit = async () => {
    if (!name.trim()) return;
    setLoading(true);
    setError(null);
    try {
      await categoriesApi.refine(categoryId, name.trim());
      onSuccess(name.trim());
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e));
    } finally {
      setLoading(false);
    }
  };
  return (
    <div className="fixed inset-0 bg-black/30 flex items-center justify-center z-50" onClick={onClose}>
      <div className="bg-theme-surface text-theme-text rounded-lg shadow-xl p-6 w-96" onClick={(e) => e.stopPropagation()}>
        <h3 className="text-lg font-semibold mb-4">{t("classificationTree.refineDialog.title", { valueName })}</h3>
        <input autoFocus className="w-full px-3 py-2 border border-theme-border rounded mb-2 bg-theme-bg text-theme-text"
          placeholder={t("classificationTree.refineDialog.namePlaceholder")} value={name}
          onChange={(e) => setName(e.target.value)}
          onKeyDown={(e) => { if (e.key === "Enter") submit(); if (e.key === "Escape") onClose(); }} />
        {error && <p className="text-theme-danger text-sm mb-2">{error}</p>}
        <div className="flex justify-end gap-2">
          <button className="px-3 py-1 text-sm border border-theme-border rounded" onClick={onClose}>
            {t("classificationTree.refineDialog.cancel")}
          </button>
          <button className="px-3 py-1 text-sm bg-theme-accent text-white rounded disabled:opacity-50"
            onClick={submit} disabled={loading || !name.trim()}>
            {loading ? "…" : t("classificationTree.refineDialog.create")}
          </button>
        </div>
      </div>
    </div>
  );
}

export default function ClassificationTreeView({ projectId }: Props) {
  const { t } = useTranslation();
  const store = useCategoryStore();
  const { categories, values } = store;
  const project = useProjectStore((s) => s.projects.find((p) => p.id === projectId));

  const [zoom, setZoom] = useState(1);
  const [selection, setSelection] = useState<Selection>(null);
  const [editing, setEditing] = useState<{ node: TreeNode; text: string } | null>(null);
  const [message, setMessage] = useState<{ text: string; error?: boolean } | null>(null);
  const [contextMenu, setContextMenu] = useState<{ x: number; y: number; node: TreeNode } | null>(null);
  const [refineTarget, setRefineTarget] = useState<{ categoryId: number; valueName: string } | null>(null);
  const [withMatrix, setWithMatrix] = useState(true);
  const dragRef = useRef<Selection>(null);
  const containerRef = useRef<HTMLDivElement>(null);
  const svgRef = useRef<SVGSVGElement>(null);

  // Matrix
  const [generations, setGenerations] = useState<{ id: number; name: string }[]>([]);
  const [generationId, setGenerationId] = useState<number | null>(null);
  const [testcases, setTestcases] = useState<TestCaseOut[]>([]);
  const [manualRows, setManualRows] = useState<ManualRow[]>([]);
  const [seedName, setSeedName] = useState("");
  const nextKey = useRef(1);

  // C-15: alle Klassen laden, sobald die Kategorien bekannt sind
  const categoryKey = categories.map((c) => c.id).join(",");
  useEffect(() => {
    store.fetchAllValues().catch((e) => setMessage({ text: String(e), error: true }));
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [categoryKey]);

  useEffect(() => {
    generateApi.listGenerations(projectId)
      .then((list) => {
        setGenerations(list);
        setGenerationId((current) => current ?? list[0]?.id ?? null);
      })
      .catch(() => setGenerations([]));
  }, [projectId]);

  useEffect(() => {
    if (!generationId) { setTestcases([]); return; }
    generateApi.getTestcases(generationId)
      .then((r) => setTestcases(r.testcases ?? []))
      .catch(() => setTestcases([]));
  }, [generationId]);

  const layout = useMemo(() => computeTreeLayout(
    project?.name ?? t("classificationTree.project"),
    categories.map((c) => ({
      id: c.id,
      name: c.name,
      isResult: c.is_result ?? false,
      values: (values[c.id] ?? []).map((v) => ({
        id: v.id, name: v.value, isError: !v.allowed, isDefault: v.is_default, parentId: v.parent_value_id ?? null,
      })),
    })),
  ), [project?.name, categories, values, t]);

  const rows: MatrixRow[] = useMemo(() => [
    ...testcases.map((tc) => ({ key: `tc-${tc.id}`, label: tc.name, assignment: tc.assignments ?? {} })),
    ...manualRows.map((r, i) => ({ key: `m-${r.key}`, label: `${t("classificationTree.manualPrefix")}${i + 1}`, assignment: r.assignment, manual: r })),
  ], [testcases, manualRows, t]);

  const columnIndex = useMemo(() => {
    const map = new Map<string, TreeColumn>();
    layout.columns.forEach((c) => map.set(`${c.categoryName}\u0000${c.value}`, c));
    return map;
  }, [layout.columns]);

  const matrixTop = layout.totalHeight + MATRIX_GAP;
  const width = Math.max(layout.totalWidth, 480);
  const height = rows.length ? matrixTop + rows.length * ROW_HEIGHT + 8 : layout.totalHeight + 16;

  // ---------------------------------------------------------------- Zoom (C-23)
  useEffect(() => {
    const el = containerRef.current;
    if (!el) return;
    const onWheel = (e: WheelEvent) => {
      if (!e.ctrlKey) return;
      e.preventDefault(); // nur der Baum zoomt, die Seite scrollt nicht mit
      setZoom((z) => Math.max(MIN_ZOOM, Math.min(MAX_ZOOM, z + (e.deltaY > 0 ? -0.1 : 0.1))));
    };
    el.addEventListener("wheel", onWheel, { passive: false });
    return () => el.removeEventListener("wheel", onWheel);
  }, []);

  const fit = () => {
    const el = containerRef.current;
    if (!el || width === 0) return;
    const z = Math.min(el.clientWidth / width, el.clientHeight > 0 ? el.clientHeight / height : Infinity, MAX_ZOOM);
    setZoom(Math.max(MIN_ZOOM, Math.round(z * 100) / 100));
  };

  // ---------------------------------------------------------------- Bearbeiten (C-17)
  const report = (e: unknown) => setMessage({ text: e instanceof Error ? e.message : String(e), error: true });

  const nodeFor = (sel: Selection): TreeNode | undefined =>
    sel === null ? undefined : layout.nodes.find((n) =>
      sel.type === "category" ? n.type === "category" && n.categoryId === sel.categoryId
        : n.type === "value" && n.valueId === sel.valueId);

  const startRename = (node?: TreeNode) => {
    if (node && node.type !== "root") setEditing({ node, text: node.label });
  };

  const commitRename = async () => {
    if (!editing) return;
    const { node, text } = editing;
    setEditing(null);
    const name = text.trim();
    if (!name || name === node.label) return;
    try {
      if (node.type === "category" && node.categoryId) await store.renameCategory(node.categoryId, name);
      if (node.type === "value" && node.categoryId && node.valueId) await store.renameValue(node.categoryId, node.valueId, name);
    } catch (e) { report(e); }
  };

  const confirmAffected = (names: string[]) =>
    confirm(t("categoryTree.constraintReferenceConfirm", { names: names.join(", ") }));

  const remove = async (node?: TreeNode) => {
    if (!node || node.type === "root" || !node.categoryId) return;
    const isCategory = node.type === "category";
    if (!confirm(t(isCategory ? "classificationTree.deleteConfirmCategory" : "classificationTree.deleteConfirmValue", { name: node.label }))) return;
    try {
      const categoryId = node.categoryId;
      await deleteWithConstraintCheck(
        (force) => isCategory ? store.deleteCategory(categoryId, force) : store.deleteValue(categoryId, node.valueId!, force),
        confirmAffected,
      );
      setSelection(null);
    } catch (e) { report(e); }
  };

  const addCategory = async () => {
    try {
      const cat = await store.createCategory(projectId,
        uniqueName(t("classificationTree.newCategory"), categories.map((c) => c.name)));
      setSelection({ type: "category", categoryId: cat.id });
    } catch (e) { report(e); }
  };

  const addClass = async (categoryId?: number) => {
    if (!categoryId) return;
    try {
      const val = await store.createValue(categoryId,
        uniqueName(t("classificationTree.newClass"), (values[categoryId] ?? []).map((v) => v.value)));
      setSelection({ type: "value", categoryId, valueId: val.id });
    } catch (e) { report(e); }
  };

  /** Element vor/hinter ein anderes verschieben (Ziehen) oder um eine Position (Alt+Pfeil). */
  const move = async (source: Selection, targetIndex: number) => {
    if (!source) return;
    try {
      if (source.type === "category") {
        const order = categories.map((c) => c.id).filter((id) => id !== source.categoryId);
        order.splice(Math.max(0, Math.min(order.length, targetIndex)), 0, source.categoryId);
        await store.reorderCategories(projectId, order);
      } else {
        const order = (values[source.categoryId] ?? []).map((v) => v.id).filter((id) => id !== source.valueId);
        order.splice(Math.max(0, Math.min(order.length, targetIndex)), 0, source.valueId);
        await store.reorderValues(source.categoryId, order);
      }
    } catch (e) { report(e); }
  };

  const indexOf = (sel: Selection): number => {
    if (!sel) return -1;
    return sel.type === "category"
      ? categories.findIndex((c) => c.id === sel.categoryId)
      : (values[sel.categoryId] ?? []).findIndex((v) => v.id === sel.valueId);
  };

  const selectionOf = (node: TreeNode): Selection =>
    node.type === "category" && node.categoryId ? { type: "category", categoryId: node.categoryId }
      : node.type === "value" && node.categoryId && node.valueId ? { type: "value", categoryId: node.categoryId, valueId: node.valueId }
        : null;

  const onDrop = (target: TreeNode) => {
    const source = dragRef.current;
    dragRef.current = null;
    const dest = selectionOf(target);
    if (!source || !dest || source.type !== dest.type) return;
    if (source.type === "value" && dest.type === "value" && source.categoryId !== dest.categoryId) return;
    const targetIndex = indexOf(dest);
    if (targetIndex === indexOf(source)) return;
    move(source, targetIndex);
  };

  const onKeyDown = (e: React.KeyboardEvent) => {
    if (editing) return;
    const ctrl = e.ctrlKey || e.metaKey;
    if (ctrl && e.key.toLowerCase() === "z" && !e.shiftKey) { e.preventDefault(); store.undo(); return; }
    if (ctrl && (e.key.toLowerCase() === "y" || (e.key.toLowerCase() === "z" && e.shiftKey))) { e.preventDefault(); store.redo(); return; }
    if (e.key === "F2") { e.preventDefault(); startRename(nodeFor(selection)); return; }
    if (e.key === "Delete") { e.preventDefault(); remove(nodeFor(selection)); return; }
    if (e.altKey && (e.key === "ArrowLeft" || e.key === "ArrowRight") && selection) {
      e.preventDefault();
      move(selection, indexOf(selection) + (e.key === "ArrowLeft" ? -1 : 1));
    }
  };

  // ---------------------------------------------------------------- Manuelle Testfaelle (C-19)
  const toggleCell = async (row: ManualRow, column: TreeColumn) => {
    const assignment = { ...row.assignment };
    if (assignment[column.categoryName] === column.value) delete assignment[column.categoryName];
    else assignment[column.categoryName] = column.value;
    setManualRows((rs) => rs.map((r) => (r.key === row.key ? { ...r, assignment, check: undefined } : r)));
    try {
      const check = Object.keys(assignment).length ? await testcaseCheckApi.check(projectId, assignment) : undefined;
      setManualRows((rs) => rs.map((r) => (r.key === row.key && r.assignment === assignment ? { ...r, check } : r)));
    } catch (e) { report(e); }
  };

  const saveAsSeedSet = async () => {
    const name = seedName.trim();
    if (!name || manualRows.length === 0) return;
    try {
      const seeds = manualRows.map((r) => Object.fromEntries(categories.map((c) => [c.name, r.assignment[c.name] ?? null])));
      const res = await seedApi.create(projectId, { name, seeds });
      setMessage({ text: t("classificationTree.manualSaved", { name: res.name, count: res.seed_count }) });
      setManualRows([]);
      setSeedName("");
    } catch (e) { report(e); }
  };

  // ---------------------------------------------------------------- Export (C-20)
  const exportSvgText = () => svgRef.current
    ? buildExportSvg(svgRef.current, { withMatrix, treeHeight: layout.totalHeight })
    : "";
  const fileBase = `klassifikationsbaum-${(project?.name ?? String(projectId)).replace(/[^\p{L}\p{N}_-]+/gu, "_")}`;

  const exportSvg = () => {
    const text = exportSvgText();
    if (text) downloadBlob(new Blob([text], { type: "image/svg+xml" }), `${fileBase}.svg`);
  };

  const exportPng = async () => {
    const text = exportSvgText();
    if (!text) return;
    try {
      const h = withMatrix ? height : layout.totalHeight + 16;
      downloadBlob(await svgToPng(text, width, h), `${fileBase}.png`);
    } catch (e) { report(e); }
  };

  // Kontextmenue schliessen
  useEffect(() => {
    const close = () => setContextMenu(null);
    window.addEventListener("click", close);
    return () => window.removeEventListener("click", close);
  }, []);

  const contextItems = (node: TreeNode) => {
    const items: { label: string; action: () => void; danger?: boolean }[] = [
      { label: t("classificationTree.rename"), action: () => startRename(node) },
    ];
    if (node.type === "category") items.push({ label: t("classificationTree.addClass"), action: () => addClass(node.categoryId) });
    if (node.type === "value" && node.categoryId) {
      items.push({ label: t("classificationTree.refine"), action: () => setRefineTarget({ categoryId: node.categoryId!, valueName: node.label }) });
    }
    items.push({ label: t("classificationTree.delete"), action: () => remove(node), danger: true });
    return items;
  };

  // ---------------------------------------------------------------- Darstellung
  const isSelected = (node: TreeNode) =>
    !!selection && ((selection.type === "category" && node.type === "category" && node.categoryId === selection.categoryId)
      || (selection.type === "value" && node.type === "value" && node.valueId === selection.valueId));

  const renderNode = (node: TreeNode) => {
    const C = TREE_COLORS;
    const markers: string[] = [];
    if (node.type === "category" && node.isResult) markers.push(`★ ${t("classificationTree.markers.result")}`);
    if (node.type === "value" && node.isError) markers.push(`⚠ ${t("classificationTree.markers.error")}`);
    if (node.type === "value" && node.isDefault) markers.push(`◆ ${t("classificationTree.markers.default")}`);
    const fill = node.type === "root" ? C.rootFill
      : node.type === "category" ? (node.isResult ? C.resultFill : C.categoryFill)
        : node.isError ? C.errorFill : C.classFill;
    const text = node.type === "value" ? (node.isError ? C.errorText : C.classText) : C.rootText;
    const stroke = node.type === "value" ? (node.isError ? C.errorStroke : C.classStroke) : fill;
    const fullLabel = [node.label, ...markers].join(" – ");
    const center = node.x + node.width / 2;
    const interactive = node.type !== "root";
    return (
      <g key={node.id} data-node-id={node.id} data-node-type={node.type}
        role={interactive ? "button" : undefined}
        aria-label={fullLabel}
        style={{ cursor: interactive ? "pointer" : "default" }}
        onClick={(e) => { e.stopPropagation(); setSelection(selectionOf(node)); containerRef.current?.focus(); }}
        onDoubleClick={() => startRename(node)}
        onContextMenu={(e) => { if (!interactive) return; e.preventDefault(); e.stopPropagation(); setSelection(selectionOf(node)); setContextMenu({ x: e.clientX, y: e.clientY, node }); }}
        onPointerDown={() => { dragRef.current = selectionOf(node); }}
        onPointerUp={() => onDrop(node)}
      >
        <title>{fullLabel}</title>
        <rect x={node.x} y={node.y} width={node.width} height={node.height}
          rx={node.type === "root" ? 20 : 4} fill={fill} stroke={stroke}
          strokeWidth={node.type === "value" && node.isDefault ? 2.5 : 1}
          strokeDasharray={node.parentId ? "4 3" : undefined} />
        {isSelected(node) && (
          <rect data-export="skip" x={node.x - 3} y={node.y - 3} width={node.width + 6} height={node.height + 6}
            rx={6} fill="none" stroke={TREE_COLORS.selected} strokeWidth={3} />
        )}
        <text x={center} y={node.y + (markers.length ? node.height / 2 - 7 : node.height / 2)}
          textAnchor="middle" dominantBaseline="central" fontFamily={FONT}
          fontSize={node.type === "root" ? 14 : 12} fontWeight={node.type === "value" ? 400 : 600} fill={text}>
          {truncate(node.label, node.width)}
        </text>
        {markers.length > 0 && (
          <text x={center} y={node.y + node.height / 2 + 9} textAnchor="middle" dominantBaseline="central"
            fontFamily={FONT} fontSize={10} fill={text}>
            {truncate(markers.join(" "), node.width)}
          </text>
        )}
      </g>
    );
  };

  const C = TREE_COLORS;
  const btn = "px-2 py-1 text-xs rounded border border-theme-border bg-theme-surface text-theme-text hover:bg-theme-surface-hover disabled:opacity-50";
  const selectedNode = nodeFor(selection);

  return (
    <div className="flex flex-col h-full min-h-0 min-w-0 w-full gap-2">
      {/* Werkzeugleiste */}
      <div className="flex flex-wrap items-center gap-2" role="toolbar" aria-label={t("classificationTree.title")}>
        <button className={btn} onClick={() => setZoom((z) => Math.max(MIN_ZOOM, Math.round((z - 0.2) * 10) / 10))} aria-label={t("classificationTree.zoomOut")}>−</button>
        <span className="text-xs text-theme-text w-12 text-center" data-testid="zoom-level">{Math.round(zoom * 100)} %</span>
        <button className={btn} onClick={() => setZoom((z) => Math.min(MAX_ZOOM, Math.round((z + 0.2) * 10) / 10))} aria-label={t("classificationTree.zoomIn")}>+</button>
        <button className={btn} onClick={fit}>{t("classificationTree.fit")}</button>
        <span className="mx-1 h-4 border-l border-theme-border" />
        <button className={btn} onClick={addCategory}>+ {t("classificationTree.addCategory")}</button>
        <button className={btn} onClick={() => addClass(selection?.categoryId)} disabled={!selection}>+ {t("classificationTree.addClass")}</button>
        <button className={btn} onClick={() => startRename(selectedNode)} disabled={!selectedNode}>{t("classificationTree.rename")}</button>
        <button className={btn} onClick={() => remove(selectedNode)} disabled={!selectedNode}>{t("classificationTree.delete")}</button>
        <button className={btn} onClick={() => store.undo()} disabled={!store.canUndo || store.busy}>{t("classificationTree.undo")}</button>
        <button className={btn} onClick={() => store.redo()} disabled={!store.canRedo || store.busy}>{t("classificationTree.redo")}</button>
        <span className="mx-1 h-4 border-l border-theme-border" />
        <label className="flex items-center gap-1 text-xs text-theme-text">
          <input type="checkbox" checked={withMatrix} onChange={(e) => setWithMatrix(e.target.checked)} />
          {t("classificationTree.withMatrix")}
        </label>
        <button className={btn} onClick={exportSvg}>{t("classificationTree.exportSvg")}</button>
        <button className={btn} onClick={exportPng}>{t("classificationTree.exportPng")}</button>
      </div>

      {/* Legende (C-22) */}
      <p className="text-xs text-theme-text-secondary" data-testid="tree-legend">
        <span className="font-medium text-theme-text">{t("classificationTree.legend.title")}:</span>{" "}
        ★ {t("classificationTree.markers.result")} · ⚠ {t("classificationTree.markers.error")} ·
        ◆ {t("classificationTree.markers.default")} · ● {t("classificationTree.legend.dot")} ·
        {" "}{t("classificationTree.legend.keys")}
      </p>

      {(message || store.error) && (
        <div role={message?.error || store.error ? "alert" : "status"}
          className={`px-3 py-1.5 text-sm rounded border ${message?.error || store.error ? "border-theme-danger text-theme-danger" : "border-theme-success text-theme-success"}`}>
          {message?.text ?? store.error}
          <button className="ml-2 text-xs underline" onClick={() => setMessage(null)}>×</button>
        </div>
      )}

      {/* Baum + Matrix */}
      <div ref={containerRef} tabIndex={0} onKeyDown={onKeyDown}
        className="relative flex-1 min-h-[240px] overflow-auto rounded border border-theme-border focus:outline-none focus:ring-2 focus:ring-theme-accent"
        aria-label={t("classificationTree.canvasLabel")}
        onPointerUp={() => { dragRef.current = null; }}>
        <svg ref={svgRef} data-tree="true" xmlns="http://www.w3.org/2000/svg"
          width={width * zoom} height={height * zoom} viewBox={`0 0 ${width} ${height}`}
          onClick={() => setSelection(null)}>
          <rect data-part="background" x={0} y={0} width={width} height={height} fill={C.background} />
          <g data-part="tree">
            {layout.edges.map((e, i) => (
              <line key={i} x1={e.x1} y1={e.y1} x2={e.x2} y2={e.y2} stroke={C.line} strokeWidth={1} />
            ))}
            {layout.nodes.map(renderNode)}
          </g>
          {rows.length > 0 && (
            <g data-part="matrix">
              {layout.columns.map((col) => (
                <line key={`g-${col.categoryId}-${col.value}`} x1={col.x + col.width / 2} y1={layout.totalHeight}
                  x2={col.x + col.width / 2} y2={height - 8} stroke={C.grid} strokeWidth={1} />
              ))}
              {rows.map((row, ri) => {
                const y = matrixTop + ri * ROW_HEIGHT;
                const check = row.manual?.check;
                const bg = row.manual ? (check && !check.valid ? C.invalidRow : check && !check.completable ? C.incompleteRow : C.manualRow) : undefined;
                const status = check && !check.valid
                  ? `⚠ ${check.violations.join("; ")}`
                  : check && !check.completable ? `⚠ ${t("classificationTree.notCompletable")}` : "";
                return (
                  <g key={row.key} data-row={row.key} data-row-state={check ? (check.valid ? (check.completable ? "ok" : "incomplete") : "invalid") : undefined}>
                    {status && <title>{status}</title>}
                    {bg && <rect x={0} y={y} width={width} height={ROW_HEIGHT} fill={bg} />}
                    <line x1={0} y1={y + ROW_HEIGHT} x2={width} y2={y + ROW_HEIGHT} stroke={C.grid} strokeWidth={1} />
                    <text x={8} y={y + ROW_HEIGHT / 2} dominantBaseline="central" fontFamily={FONT} fontSize={11} fill={C.rowText}>
                      {(check && !check.valid ? "⚠ " : "") + truncate(row.label, LEFT_MARGIN - 8)}
                    </text>
                    {Object.entries(row.assignment).map(([cat, val]) => {
                      const col = columnIndex.get(`${cat}\u0000${val}`);
                      return col ? (
                        <circle key={cat} data-dot={`${row.key}:${cat}=${val}`} cx={col.x + col.width / 2}
                          cy={y + ROW_HEIGHT / 2} r={5} fill={C.dot} />
                      ) : null;
                    })}
                    {row.manual && layout.columns.map((col) => (
                      <rect key={`c-${col.categoryId}-${col.value}`} data-export="skip" data-cell={`${row.key}:${col.categoryName}=${col.value}`}
                        x={col.x} y={y} width={col.width} height={ROW_HEIGHT} fill="transparent" style={{ cursor: "pointer" }}
                        onClick={(e) => { e.stopPropagation(); toggleCell(row.manual!, col); }} />
                    ))}
                  </g>
                );
              })}
            </g>
          )}
        </svg>

        {/* Umbenennen direkt am Element */}
        {editing && (
          <input autoFocus aria-label={t("classificationTree.rename")}
            className="absolute px-1 text-sm border-2 border-theme-accent rounded bg-theme-surface text-theme-text"
            style={{
              left: editing.node.x * zoom, top: editing.node.y * zoom,
              width: Math.max(80, editing.node.width * zoom), height: Math.max(24, editing.node.height * zoom / 1.5),
            }}
            value={editing.text}
            onChange={(e) => setEditing({ ...editing, text: e.target.value })}
            onBlur={commitRename}
            onKeyDown={(e) => {
              e.stopPropagation();
              if (e.key === "Enter") commitRename();
              if (e.key === "Escape") setEditing(null);
            }} />
        )}
      </div>

      {/* Matrix-Steuerung */}
      <div className="flex flex-wrap items-center gap-2 text-xs text-theme-text">
        <label className="flex items-center gap-1">
          {t("classificationTree.generation")}
          <select className="px-2 py-1 rounded border border-theme-border bg-theme-surface text-theme-text"
            value={generationId ?? ""} onChange={(e) => setGenerationId(e.target.value ? Number(e.target.value) : null)}>
            <option value="">{t("classificationTree.noGeneration")}</option>
            {generations.map((g) => <option key={g.id} value={g.id}>{g.name || `#${g.id}`}</option>)}
          </select>
        </label>
        <button className={btn} onClick={() => setManualRows((rs) => [...rs, { key: nextKey.current++, assignment: {} }])}
          disabled={layout.columns.length === 0}>
          + {t("classificationTree.addTestCase")}
        </button>
        {manualRows.length > 0 && (
          <>
            <input className="px-2 py-1 rounded border border-theme-border bg-theme-surface text-theme-text"
              placeholder={t("classificationTree.seedSetName")} aria-label={t("classificationTree.seedSetName")}
              value={seedName} onChange={(e) => setSeedName(e.target.value)} />
            <button className={btn} onClick={saveAsSeedSet} disabled={!seedName.trim()}>{t("classificationTree.saveAsSeeds")}</button>
            <button className={btn} onClick={() => setManualRows([])}>{t("classificationTree.discardManual")}</button>
            <span className="text-theme-text-secondary">{t("classificationTree.manualHint")}</span>
          </>
        )}
      </div>

      {refineTarget && (
        <RefineDialog categoryId={refineTarget.categoryId} valueName={refineTarget.valueName}
          onClose={() => setRefineTarget(null)}
          onSuccess={(name) => { setRefineTarget(null); setMessage({ text: t("classificationTree.refineDialog.success", { name }) }); store.fetchCategories(projectId); }} />
      )}

      {contextMenu && (
        <div role="menu" className="fixed z-50 py-1 min-w-[180px] rounded border border-theme-border bg-theme-surface text-theme-text shadow-lg"
          style={{ left: contextMenu.x, top: contextMenu.y }} onClick={(e) => e.stopPropagation()}>
          {contextItems(contextMenu.node).map((item) => (
            <button key={item.label} role="menuitem"
              className={`block w-full text-left px-3 py-1.5 text-sm hover:bg-theme-surface-hover ${item.danger ? "text-theme-danger" : ""}`}
              onClick={() => { setContextMenu(null); item.action(); }}>
              {item.label}
            </button>
          ))}
        </div>
      )}
    </div>
  );
}


// REQ-1207: Kategorienbaum mit Drag&Drop (REQ-1209), Kontextmenue (REQ-1211),
// Inline-Edit (REQ-1213), Keyboard-Shortcuts (REQ-1210), Toast (REQ-1212), Undo/Redo (REQ-3053)
// REQ-3054: Pfeiltasten-Navigation, F2, Enter, Delete, Escape
// REQ-6005: i18n
import { useEffect, useRef, useState } from "react";
import { useTranslation } from "react-i18next";
import { useCategoryStore } from "../store/categoryStore";
import { categoriesApi } from "../api/client";
import { categoryPropertiesApi } from "../api/client";
import { useToastStore } from "./Toast";
import { useKeyboardShortcuts } from "../hooks/useKeyboardShortcuts";
import { useKeyboardNav } from "../hooks/useKeyboardNav";
import ContextMenu, { type ContextMenuItem } from "./ContextMenu";
import { BVADialog } from "./bva/BVADialog";
import DataNodeApplyDialog from "./DataNodeApplyDialog";
import UndoRedoToolbar from "./ui/UndoRedoToolbar";
import { deleteWithConstraintCheck } from "../lib/constraintReference";

interface Props { projectId: number; }

interface CtxState {
  x: number; y: number;
  type: "category" | "value";
  id: number; catId?: number;
}

export default function CategoryTree({ projectId }: Props) {
  const { t } = useTranslation();
  const {
    categories, values, loading, error,
    fetchCategories, createCategory, deleteCategory: storeDeleteCategory,
    fetchValues, createValue, deleteValue: storeDeleteValue,
    canUndo, canRedo, undo, redo, // REQ-3053
    renameCategory, renameValue, reorderCategories, // BUG C-18
  } = useCategoryStore();
  const toast = useToastStore();

  // REQ-6001 AK-10: Bei verweisenden Constraints vor dem Loeschen nachfragen.
  // Liefert true, wenn geloescht wurde, false bei Abbruch durch den Nutzer.
  const confirmAffectedConstraints = (names: string[]) =>
    confirm(t("categoryTree.constraintReferenceConfirm", { names: names.join(", ") }));
  const deleteCategory = (categoryId: number) =>
    deleteWithConstraintCheck((force) => storeDeleteCategory(categoryId, force), confirmAffectedConstraints);
  const deleteValue = (categoryId: number, valueId: number) =>
    deleteWithConstraintCheck((force) => storeDeleteValue(categoryId, valueId, force), confirmAffectedConstraints);

  const [newCatName, setNewCatName] = useState("");
  // REQ-5002/REQ-4016: Typ der neuen Kategorie
  const [newCatKind, setNewCatKind] = useState<"normal" | "ergebnis" | "ursache" | "wirkung">("normal");
  const [expanded, setExpanded] = useState<Record<number, boolean>>({});
  const [newValue, setNewValue] = useState<Record<number, string>>({});
  const [editingCat, setEditingCat] = useState<number | null>(null);
  const [editingCatName, setEditingCatName] = useState("");
  const [editingVal, setEditingVal] = useState<{ catId: number; valId: number } | null>(null);
  const [editingValName, setEditingValName] = useState("");
  const [selectedCatId, setSelectedCatId] = useState<number | null>(null);
  const [selectedValId, setSelectedValId] = useState<{ catId: number; valId: number } | null>(null);
  const [ctx, setCtx] = useState<CtxState | null>(null);
  const [bvaDialogOpen, setBvaDialogOpen] = useState<{ id: number; name: string } | null>(null);
  // REQ-4018: Ziel-Dialog "Datenklasse anwenden auf:" (DataNode-Baum)
  const [dataNodeDialog, setDataNodeDialog] = useState<{ id: number; name: string } | null>(null);
  const [dragOverId, setDragOverId] = useState<number | null>(null);
  const newCatRef = useRef<HTMLInputElement>(null);

  useEffect(() => { fetchCategories(projectId); }, [projectId, fetchCategories]);

  // REQ-3054: Pfeiltasten-Navigation für Kategorien
  const { focusedIndex: focusedCatIndex, setFocusedIndex: setFocusedCatIndex } = useKeyboardNav(
    categories.map((cat) => ({
      id: cat.id,
      onSelect: () => {
        setSelectedCatId(cat.id);
        setSelectedValId(null);
        toggleExpand(cat.id);
      },
      onDelete: () => {
        if (confirm(t("categoryTree.contextMenu.deleteCategoryConfirm"))) {
          deleteCategory(cat.id)
            .then((done) => { if (!done) return; toast.add(t("categoryTree.toast.categoryDeleted")); setSelectedCatId(null); })
            .catch(() => toast.add(t("categoryTree.toast.errorDelete"), "error"));
        }
      },
      onRename: () => startEditCat(cat.id, cat.name),
    })),
    !editingCat && !editingVal // Navigation nur wenn nicht im Edit-Modus
  );

  // Keyboard Shortcuts (REQ-1210/REQ-3012)
  useKeyboardShortcuts({
    "delete": () => {
      // Bug-Fix: DEL löscht gewählten Wert ODER gewählte Kategorie
      if (selectedValId) {
        if (confirm(t("categoryTree.contextMenu.deleteValueConfirm"))) {
          deleteValue(selectedValId.catId, selectedValId.valId)
            .then((done) => { if (!done) return; toast.add(t("categoryTree.toast.valueDeleted")); setSelectedValId(null); })
            .catch(() => toast.add(t("categoryTree.toast.errorDelete"), "error"));
        }
      } else if (selectedCatId) {
        if (confirm(t("categoryTree.contextMenu.deleteCategoryConfirm"))) {
          deleteCategory(selectedCatId)
            .then((done) => { if (!done) return; toast.add(t("categoryTree.toast.categoryDeleted")); setSelectedCatId(null); })
            .catch(() => toast.add(t("categoryTree.toast.errorDelete"), "error"));
        }
      }
    },
  });

  const toggleExpand = async (catId: number) => {
    if (!expanded[catId] && !values[catId]) {
      await fetchValues(catId);
    }
    setExpanded((s) => ({ ...s, [catId]: !s[catId] }));
  };

  const handleAddCategory = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!newCatName.trim()) return;
    const kind = newCatKind === "ursache" ? "cause" : newCatKind === "wirkung" ? "effect" : "standard";
    const isResult = newCatKind === "ergebnis";
    try {
      await createCategory(projectId, newCatName.trim(), kind, isResult);
      toast.add(t("categoryTree.toast.categoryCreated"));
      setNewCatName("");
      setNewCatKind("normal");
    } catch { toast.add(t("categoryTree.toast.errorCreate"), "error"); }
  };

  const changeCategoryType = async (catId: number, type: "standard" | "cause" | "effect") => {
    try {
      await categoryPropertiesApi.updateCategoryType(catId, type);
      await fetchCategories(projectId);
      toast.add(t("categoryTree.toast.categoryTypeChanged"));
    } catch { toast.add(t("categoryTree.toast.errorTypeChange"), "error"); }
  };

  const handleAddValue = async (catId: number) => {
    const val = newValue[catId]?.trim();
    if (!val) return;
    try {
      await createValue(catId, val);
      toast.add(t("categoryTree.toast.valueAdded"));
      setNewValue((s) => ({ ...s, [catId]: "" }));
    } catch { toast.add(t("categoryTree.toast.errorAdd"), "error"); }
  };

  // Inline-Edit Kategorie (REQ-1213)
  const startEditCat = (catId: number, name: string) => {
    setEditingCat(catId); setEditingCatName(name);
  };
  const confirmEditCat = async (catId: number) => {
    if (!editingCatName.trim()) { setEditingCat(null); return; }
    try {
      await renameCategory(catId, editingCatName.trim());  // BUG C-18: mit serverseitigem Undo
      toast.add(t("categoryTree.toast.categoryRenamed"));
    } catch { toast.add(t("categoryTree.toast.errorRename"), "error"); }
    setEditingCat(null);
  };

  // Inline-Edit Wert (REQ-1213)
  const startEditVal = (catId: number, valId: number, val: string) => {
    setEditingVal({ catId, valId }); setEditingValName(val);
  };
  const confirmEditVal = async (catId: number, valId: number) => {
    if (!editingValName.trim()) { setEditingVal(null); return; }
    try {
      await renameValue(catId, valId, editingValName.trim());  // BUG C-18: mit serverseitigem Undo
      toast.add(t("categoryTree.toast.valueRenamed"));
    } catch { toast.add(t("categoryTree.toast.errorRename"), "error"); }
    setEditingVal(null);
  };

  // Drag & Drop Sortierung (REQ-1209)
  const dragRef = useRef<number | null>(null);
  const handleDragStart = (catId: number) => { dragRef.current = catId; };
  const handleDragOver = (e: React.DragEvent, catId: number) => {
    e.preventDefault(); setDragOverId(catId);
  };
  const handleDrop = async (targetId: number) => {
    const fromId = dragRef.current;
    if (!fromId || fromId === targetId) { setDragOverId(null); return; }
    const ids = categories.map((c) => c.id);
    const fromIdx = ids.indexOf(fromId);
    const toIdx = ids.indexOf(targetId);
    const newOrder = [...ids];
    newOrder.splice(fromIdx, 1);
    newOrder.splice(toIdx, 0, fromId);
    try {
      await reorderCategories(projectId, newOrder);  // BUG C-18: mit serverseitigem Undo
      toast.add(t("categoryTree.toast.orderSaved"));
    } catch { toast.add(t("categoryTree.toast.errorSort"), "error"); }
    setDragOverId(null);
  };

  // Kontextmenue (REQ-1211)
  const openCtxCat = (e: React.MouseEvent, catId: number) => {
    e.preventDefault();
    setCtx({ x: e.clientX, y: e.clientY, type: "category", id: catId });
  };
  const openCtxVal = (e: React.MouseEvent, catId: number, valId: number): void => {
    e.preventDefault();
    setCtx({ x: e.clientX, y: e.clientY, type: "value", id: valId, catId });
  };

  const ctxItems = (): ContextMenuItem[] => {
    if (!ctx) return [];
    if (ctx.type === "category") {
      const cat = categories.find((c) => c.id === ctx.id);
      return [
        { label: t("categoryTree.contextMenu.rename"), action: () => startEditCat(ctx.id, cat?.name ?? "") },
        // REQ-5002: Typ nachtraeglich aendern
        { label: t("categoryTree.contextMenu.typeNormal"), action: () => changeCategoryType(ctx.id, "standard") },
        { label: t("categoryTree.contextMenu.typeCause"), action: () => changeCategoryType(ctx.id, "cause") },
        { label: t("categoryTree.contextMenu.typeEffect"), action: () => changeCategoryType(ctx.id, "effect") },
        { label: t("categoryTree.contextMenu.addValue"), action: () => {
          setExpanded((s) => ({ ...s, [ctx.id]: true }));
          if (!values[ctx.id]) fetchValues(ctx.id);
        }},
        { label: "", separator: true, action: () => {} },
        { label: t("categoryTree.contextMenu.applyDataClass"), action: () => { const c = categories.find((c) => c.id === ctx.id); if (c) setDataNodeDialog({ id: c.id, name: c.name }); } },
        { label: t("categoryTree.contextMenu.bva"), action: () => { const c = categories.find((c) => c.id === ctx.id); if (c) setBvaDialogOpen({ id: c.id, name: c.name }); } },
        { label: "", separator: true, action: () => {} },
        { label: t("categoryTree.contextMenu.delete"), danger: true, action: () => {
          if (confirm(t("categoryTree.contextMenu.deleteCategoryConfirm")))
            deleteCategory(ctx.id)
              .then((done) => { if (done) toast.add(t("categoryTree.toast.categoryDeleted")); })
              .catch(() => toast.add(t("categoryTree.toast.error"), "error"));
        }},
      ];
    }
    const currentVal = (values[ctx.catId!] ?? []).find((v) => v.id === ctx.id);
    const isDefault = currentVal?.is_default === true;
    return [
      { label: isDefault ? t("categoryTree.contextMenu.unsetDefault") : t("categoryTree.contextMenu.setDefault"), action: async () => {
        const catId = ctx.catId!;
        if (isDefault) {
          await categoriesApi.unsetDefault(ctx.id);
        } else {
          await categoriesApi.setDefault(ctx.id);
        }
        fetchValues(catId);
      }},
      { label: t("categoryTree.contextMenu.rename"), action: () => {
        if (currentVal) startEditVal(ctx.catId!, ctx.id, currentVal.value);
      }},
      { label: t("categoryTree.contextMenu.delete"), danger: true, action: () => {
        if (confirm(t("categoryTree.contextMenu.deleteValueConfirm")))
          deleteValue(ctx.catId!, ctx.id)
            .then((done) => { if (done) toast.add(t("categoryTree.toast.valueDeleted")); })
            .catch(() => toast.add(t("categoryTree.toast.error"), "error"));
      }},
    ];
  };

  if (loading) return <p className="text-theme-text-muted text-sm animate-pulse">{t('categoryTree.loading')}</p>;
  if (error) return <p className="text-theme-danger text-sm">{error}</p>;

  return (
    <div>
      {/* REQ-3053: Undo/Redo Toolbar */}
      <UndoRedoToolbar 
        canUndo={canUndo} 
        canRedo={canRedo} 
        onUndo={undo} 
        onRedo={redo} 
      />

      {/* Neue Kategorie */}
      <form onSubmit={handleAddCategory} className="flex gap-2 mb-4">
        <select aria-label={t('categoryTree.categoryType.normal')} value={newCatKind}
          onChange={(e) => setNewCatKind(e.target.value as typeof newCatKind)}
          className="shrink-0 max-w-[7.5rem] px-2 py-1.5 text-sm rounded-lg border border-theme-border focus:outline-none focus:ring-2 focus:ring-theme-accent">
          <option value="normal">{t('categoryTree.categoryType.normal')}</option>
          <option value="ergebnis">{t('categoryTree.categoryType.ergebnis')}</option>
          <option value="ursache">{t('categoryTree.categoryType.ursache')}</option>
          <option value="wirkung">{t('categoryTree.categoryType.wirkung')}</option>
        </select>
        <input ref={newCatRef} value={newCatName}
          onChange={(e) => setNewCatName(e.target.value)}
          placeholder={t('categoryTree.newCategoryPlaceholder')}
          className="flex-1 min-w-0 px-3 py-1.5 text-sm rounded-lg border border-theme-border focus:outline-none focus:ring-2 focus:ring-theme-accent"
        />
        <button type="submit" disabled={!newCatName.trim()}
          aria-label={t('categoryTree.newCategoryPlaceholder')}
          className="shrink-0 px-3 py-1.5 bg-theme-accent text-white text-sm rounded-lg hover:bg-theme-accent-hover disabled:opacity-40 font-bold">
          +
        </button>
      </form>

      {categories.length === 0 ? (
        <div className="flex flex-col items-center justify-center py-12 text-theme-text-muted">
          <span className="text-4xl mb-2">+</span>
          <p className="text-sm">{t('categoryTree.noCategories')}</p>
          <p className="text-xs mt-1">{t('categoryTree.noCategoriesHint')}</p>
        </div>
      ) : (
        <ul 
          className="space-y-1.5" 
          role="listbox" 
          aria-label={t('projectDetail.categoriesTitle')}
          tabIndex={0}
        >
          {categories.map((cat, idx) => (
            <li key={cat.id}
              role="option"
              aria-selected={selectedCatId === cat.id}
              draggable
              onDragStart={() => handleDragStart(cat.id)}
              onDragOver={(e) => handleDragOver(e, cat.id)}
              onDrop={() => handleDrop(cat.id)}
              onDragEnd={() => setDragOverId(null)}
              onClick={() => { setSelectedCatId(cat.id); setFocusedCatIndex(idx); }}
              onContextMenu={(e) => openCtxCat(e, cat.id)}
              className={
                "border rounded-xl overflow-hidden transition-all cursor-grab " +
                (selectedCatId === cat.id ? "border-theme-accent shadow-sm" : "border-theme-border") +
                (dragOverId === cat.id ? " opacity-60 scale-95" : "") +
                (focusedCatIndex === idx ? " ring-2 ring-theme-accent ring-offset-1" : "")
              }
            >
              {/* Kategorie-Header */}
              <div
                className={"flex items-center justify-between px-3 py-2 hover:bg-theme-surface-hover " +
                  (selectedCatId === cat.id ? "bg-theme-accent-soft" : "bg-theme-surface-2")}
                onClick={(e) => { e.stopPropagation(); toggleExpand(cat.id); }}
              >
                <span className="flex items-center gap-2 font-medium text-sm text-theme-text min-w-0">
                  <span className="text-theme-text-muted w-4 text-center select-none flex-shrink-0">
                    {expanded[cat.id] ? "v" : ">"}
                  </span>
                  {editingCat === cat.id ? (
                    <input autoFocus value={editingCatName}
                      onChange={(e) => setEditingCatName(e.target.value)}
                      onBlur={() => confirmEditCat(cat.id)}
                      onKeyDown={(e) => {
                        if (e.key === "Enter") confirmEditCat(cat.id);
                        if (e.key === "Escape") setEditingCat(null);
                      }}
                      onClick={(e) => e.stopPropagation()}
                      className="flex-1 px-1 py-0.5 text-sm border border-theme-accent rounded focus:outline-none"
                    />
                  ) : (
                    <span onDoubleClick={(e) => { e.stopPropagation(); startEditCat(cat.id, cat.name); }}
                      className="truncate">{cat.name}</span>
                  )}
                  {/* REQ-5002/REQ-4016: Kategorie-Typ visuell anzeigen */}
                  {cat.category_type === "cause" && (
                    <span className="ml-1 flex-shrink-0 text-xs bg-theme-accent-soft text-theme-link rounded-full px-1.5 py-0.5" title={t('categoryTree.categoryType.ursache')}>U</span>
                  )}
                  {cat.category_type === "effect" && (
                    <span className="ml-1 flex-shrink-0 text-xs bg-theme-success-soft text-theme-success rounded-full px-1.5 py-0.5" title={t('categoryTree.categoryType.wirkung')}>W</span>
                  )}
                  {cat.is_result && (
                    <span className="ml-1 flex-shrink-0 text-xs bg-theme-accent-soft text-theme-link rounded-full px-1.5 py-0.5" title={t('categoryTree.categoryType.ergebnis')}>E</span>
                  )}
                  {/* Werte-Zaehler Badge (Bugfix: '-' wenn noch nicht geladen) */}
                  <span
                    onClick={() => {
                      if (!values[cat.id]) {
                        fetchValues(cat.id);
                        setExpanded((s) => ({ ...s, [cat.id]: true }));
                      }
                    }}
                    className="ml-1 flex-shrink-0 text-xs bg-theme-surface-hover text-theme-text-secondary rounded-full px-1.5 py-0.5 font-normal cursor-pointer hover:bg-theme-surface-hover transition-colors"
                    title={values[cat.id] ? t('categoryTree.valuesCount', { count: (values[cat.id]).length }) : t('categoryTree.loadValues')}
                  >
                    {values[cat.id] ? (values[cat.id]).length : "…"}
                  </span>
                </span>
                <span className="flex items-center gap-2 ml-2 flex-shrink-0">
                  {/* BUG-1 Fix: BVA-Button direkt sichtbar */}
                  <button
                    onClick={(e) => { e.stopPropagation(); setBvaDialogOpen({ id: cat.id, name: cat.name }); }}
                    title={t('categoryTree.contextMenu.bva')}
                    className="text-theme-text-muted hover:text-theme-link text-xs px-1.5 py-0.5 rounded hover:bg-theme-accent-soft transition-colors"
                  >
                    ≈
                  </button>
                  <span className="text-theme-text-muted text-xs select-none cursor-grab" title={t('categoryTree.keyboardHelp.sort')}>
                    :::
                  </span>
                </span>
              </div>

              {/* Werte-Liste */}
              {expanded[cat.id] && (
                <div className="px-3 py-2 bg-theme-surface border-t border-theme-border">
                  <ul className="space-y-0.5 mb-2">
                    {(values[cat.id] ?? []).length === 0 ? (
                      <li className="text-theme-text-muted text-xs italic py-1">{t('categoryTree.noValues')}</li>
                    ) : (
                      (values[cat.id] ?? []).map((v) => (
                        <li key={v.id}
                          onContextMenu={(e) => openCtxVal(e, cat.id, v.id)}
                          onClick={() => { setSelectedValId({ catId: cat.id, valId: v.id }); setSelectedCatId(null); }}
                          className={"flex items-center justify-between text-sm py-0.5 px-1 rounded hover:bg-theme-surface-hover group" +
                            (selectedValId?.valId === v.id ? " bg-theme-accent-soft ring-1 ring-theme-accent" : "")}>
                          {editingVal?.valId === v.id ? (
                            <input autoFocus value={editingValName}
                              onChange={(e) => setEditingValName(e.target.value)}
                              onBlur={() => confirmEditVal(cat.id, v.id)}
                              onKeyDown={(e) => {
                                if (e.key === "Enter") confirmEditVal(cat.id, v.id);
                                if (e.key === "Escape") setEditingVal(null);
                              }}
                              className="flex-1 px-1 py-0.5 text-sm border border-theme-accent rounded focus:outline-none"
                            />
                          ) : (
                            <>
                              <span
                                onDoubleClick={() => startEditVal(cat.id, v.id, v.value)}
                                className={"text-theme-text flex-1 truncate " +
                                  (v.risk_weight > 2 ? "text-theme-warning font-medium" : "")}>
                                {v.is_default && <span className="mr-1 text-theme-warning font-bold" title={t('categoryTree.contextMenu.setDefault')}>★</span>}
                                {v.value}
                                {v.risk_weight > 2 && (
                                  <span className="ml-1 text-xs bg-theme-warning-soft text-theme-warning rounded px-1">
                                    R{v.risk_weight}
                                  </span>
                                )}
                                {v.allowed === false && (
                                  <span className="ml-1 text-xs bg-theme-danger-soft text-theme-danger rounded px-1 font-bold" title={t('categoryTree.keyboardHelp.delete')}>✕</span>
                                )}
                              </span>
                              <div className="flex items-center gap-1 transition-opacity">
                                {/* REQ-3007: Inline-Eigenschaften - BUG-2 Fix: immer sichtbar */}
                                <input
                                  type="number" min={1} max={10}
                                  value={v.risk_weight}
                                  title={t('categoryTree.keyboardHelp.delete')}
                                  onClick={(e) => e.stopPropagation()}
                                  onChange={async (e) => {
                                    const rw = Math.max(1, Math.min(10, Number(e.target.value)));
                                    await categoriesApi.updateProperties(v.id, { risk_weight: rw });
                                    fetchValues(cat.id);
                                  }}
                                  className="w-10 px-1 py-0.5 text-xs border border-theme-border rounded text-center focus:outline-none focus:ring-1 focus:ring-theme-accent"
                                />
                                <select
                                  value={v.vtype ?? "string"}
                                  title={t('categoryTree.categoryType.normal')}
                                  onClick={(e) => e.stopPropagation()}
                                  onChange={async (e) => {
                                    await categoriesApi.updateProperties(v.id, { vtype: e.target.value });
                                    fetchValues(cat.id);
                                  }}
                                  className="text-xs border border-theme-border rounded px-1 py-0.5 focus:outline-none focus:ring-1 focus:ring-theme-accent"
                                >
                                  {["string","number","date","time","boolean","email","text"].map((t2) => (
                                    <option key={t2} value={t2}>{t2}</option>
                                  ))}
                                </select>
                                <input
                                  type="checkbox"
                                  checked={v.allowed === false}
                                  title={t('categoryTree.keyboardHelp.delete')}
                                  onClick={(e) => e.stopPropagation()}
                                  onChange={async (e) => {
                                    await categoriesApi.updateProperties(v.id, { allowed: !e.target.checked });
                                    fetchValues(cat.id);
                                  }}
                                  className="rounded border-theme-border text-theme-danger"
                                />
                              </div>
                              <button onClick={() => deleteValue(cat.id, v.id)
                                .then((done) => { if (done) toast.add(t("categoryTree.toast.valueDeleted")); })
                                .catch(() => toast.add(t("categoryTree.toast.error"), "error"))}
                                className="opacity-0 group-hover:opacity-100 text-theme-danger hover:text-theme-danger text-xs ml-2 transition-opacity">
                                x
                              </button>
                            </>
                          )}
                        </li>
                      ))
                    )}
                  </ul>
                  {/* Neuer Wert */}
                  <div className="flex gap-1.5">
                    <input value={newValue[cat.id] ?? ""}
                      onChange={(e) => setNewValue((s) => ({ ...s, [cat.id]: e.target.value }))}
                      onKeyDown={(e) => { if (e.key === "Enter") { e.preventDefault(); handleAddValue(cat.id); } }}
                      placeholder={t('categoryTree.newValuePlaceholder')}
                      className="flex-1 px-2 py-1 text-xs rounded border border-theme-border focus:outline-none focus:ring-1 focus:ring-theme-accent"
                    />
                    <button onClick={() => handleAddValue(cat.id)}
                      className="px-2 py-1 bg-theme-surface-2 hover:bg-theme-surface-hover text-xs rounded border border-theme-border">
                      +
                    </button>
                  </div>
                </div>
              )}
            </li>
          ))}
        </ul>
      )}

      {/* REQ-4018: Datenklasse anwenden (DataNode-Baum) */}
      {dataNodeDialog && (
        <DataNodeApplyDialog
          categoryName={dataNodeDialog.name}
          onClose={() => setDataNodeDialog(null)}
          onApply={async (values) => {
            const catId = dataNodeDialog.id;
            for (const v of values) {
              await createValue(catId, v);
            }
            toast.add(t('categoryTree.toast.valuesApplied', { count: values.length }));
            fetchValues(catId);
            setDataNodeDialog(null);
          }}
        />
      )}

      {/* BVA-Dialog (REQ-3041) */}
      {bvaDialogOpen && (
        <BVADialog
          isOpen={true}
          categoryId={bvaDialogOpen.id}
          categoryName={bvaDialogOpen.name}
          projectId={projectId}
          onClose={() => {
            // REQ-4019: Werte auch beim Abbrechen neu laden (Regression-Schutz)
            if (expanded[bvaDialogOpen.id]) fetchValues(bvaDialogOpen.id);
            setBvaDialogOpen(null);
          }}
          onApply={(newValues) => {
            toast.add(t('categoryTree.toast.boundaryValuesAdded', { count: newValues.length }));
            if (expanded[bvaDialogOpen.id]) fetchValues(bvaDialogOpen.id);
            setBvaDialogOpen(null);
          }}
        />
      )}

      {/* Kontextmenue */}
      {ctx && (
        <ContextMenu x={ctx.x} y={ctx.y} items={ctxItems()} onClose={() => setCtx(null)} />
      )}

      {/* Tastatur-Hilfe */}
      <div className="mt-4 pt-3 border-t border-theme-border text-xs text-theme-text-muted space-y-0.5">
        <p>{t('categoryTree.keyboardHelp.newCategory')} &nbsp; {t('categoryTree.keyboardHelp.delete')} &nbsp; {t('categoryTree.keyboardHelp.rename')}</p>
        <p>{t('categoryTree.keyboardHelp.contextMenu')} &nbsp; {t('categoryTree.keyboardHelp.sort')}</p>
        <p>{t('categoryTree.keyboardHelp.undo')} &nbsp; {t('categoryTree.keyboardHelp.redo')}</p>
      </div>
    </div>
  );
}
// REQ-1207: Kategorienbaum mit Drag&Drop (REQ-1209), Kontextmenue (REQ-1211),
// Inline-Edit (REQ-1213), Keyboard-Shortcuts (REQ-1210), Toast (REQ-1212)
import { useEffect, useRef, useState } from "react";
import { useCategoryStore } from "../store/categoryStore";
import { categoriesApi } from "../api/client";
import { renameApi, reorderApi } from "../api/client";
import { useToastStore } from "./Toast";
import { useKeyboardShortcuts } from "../hooks/useKeyboardShortcuts";
import ContextMenu, { type ContextMenuItem } from "./ContextMenu";
import DataClassDialog from "./DataClassDialog";

interface Props { projectId: number; }

interface CtxState {
  x: number; y: number;
  type: "category" | "value";
  id: number; catId?: number;
}

export default function CategoryTree({ projectId }: Props) {
  const {
    categories, values, loading, error,
    fetchCategories, createCategory, deleteCategory,
    fetchValues, createValue, deleteValue,
  } = useCategoryStore();
  const toast = useToastStore();

  const [newCatName, setNewCatName] = useState("");
  const [expanded, setExpanded] = useState<Record<number, boolean>>({});
  const [newValue, setNewValue] = useState<Record<number, string>>({});
  const [editingCat, setEditingCat] = useState<number | null>(null);
  const [editingCatName, setEditingCatName] = useState("");
  const [editingVal, setEditingVal] = useState<{ catId: number; valId: number } | null>(null);
  const [editingValName, setEditingValName] = useState("");
  const [selectedCatId, setSelectedCatId] = useState<number | null>(null);
  const [selectedValId, setSelectedValId] = useState<{ catId: number; valId: number } | null>(null);
  const [ctx, setCtx] = useState<CtxState | null>(null);
  const [dataClassCat, setDataClassCat] = useState<{ id: number; name: string } | null>(null);
  const [dragOverId, setDragOverId] = useState<number | null>(null);
  const newCatRef = useRef<HTMLInputElement>(null);

  useEffect(() => { fetchCategories(projectId); }, [projectId, fetchCategories]);

  // Keyboard Shortcuts (REQ-1210/REQ-3012)
  useKeyboardShortcuts({
    "delete": () => {
      // Bug-Fix: DEL löscht gewählten Wert ODER gewählte Kategorie
      if (selectedValId) {
        if (confirm("Wert löschen?")) {
          deleteValue(selectedValId.catId, selectedValId.valId)
            .then(() => { toast.add("Wert gelöscht"); setSelectedValId(null); })
            .catch(() => toast.add("Fehler beim Löschen", "error"));
        }
      } else if (selectedCatId) {
        if (confirm("Kategorie löschen?")) {
          deleteCategory(selectedCatId)
            .then(() => { toast.add("Kategorie gelöscht"); setSelectedCatId(null); })
            .catch(() => toast.add("Fehler beim Löschen", "error"));
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
    try {
      await createCategory(projectId, newCatName.trim());
      toast.add("Kategorie angelegt");
      setNewCatName("");
    } catch { toast.add("Fehler beim Anlegen", "error"); }
  };

  const handleAddValue = async (catId: number) => {
    const val = newValue[catId]?.trim();
    if (!val) return;
    try {
      await createValue(catId, val);
      toast.add("Wert hinzugefuegt");
      setNewValue((s) => ({ ...s, [catId]: "" }));
    } catch { toast.add("Fehler beim Hinzufuegen", "error"); }
  };

  // Inline-Edit Kategorie (REQ-1213)
  const startEditCat = (catId: number, name: string) => {
    setEditingCat(catId); setEditingCatName(name);
  };
  const confirmEditCat = async (catId: number) => {
    if (!editingCatName.trim()) { setEditingCat(null); return; }
    try {
      await renameApi.category(catId, editingCatName.trim());
      await fetchCategories(projectId);
      toast.add("Kategorie umbenannt");
    } catch { toast.add("Fehler beim Umbenennen", "error"); }
    setEditingCat(null);
  };

  // Inline-Edit Wert (REQ-1213)
  const startEditVal = (catId: number, valId: number, val: string) => {
    setEditingVal({ catId, valId }); setEditingValName(val);
  };
  const confirmEditVal = async (catId: number, valId: number) => {
    if (!editingValName.trim()) { setEditingVal(null); return; }
    try {
      await renameApi.value(valId, editingValName.trim());
      await fetchValues(catId);
      toast.add("Wert umbenannt");
    } catch { toast.add("Fehler beim Umbenennen", "error"); }
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
      await reorderApi.categories(projectId, newOrder);
      await fetchCategories(projectId);
      toast.add("Reihenfolge gespeichert");
    } catch { toast.add("Fehler beim Sortieren", "error"); }
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
        { label: "Umbenennen (F2)", action: () => startEditCat(ctx.id, cat?.name ?? "") },
        { label: "Wert hinzufügen", action: () => {
          setExpanded((s) => ({ ...s, [ctx.id]: true }));
          if (!values[ctx.id]) fetchValues(ctx.id);
        }},
        { label: "", separator: true, action: () => {} },
        { label: "Datenklasse anwenden...", action: () => { const c = categories.find((c) => c.id === ctx.id); if (c) setDataClassCat({ id: c.id, name: c.name }); } },
        { label: "", separator: true, action: () => {} },
        { label: "Löschen", danger: true, action: () => {
          if (confirm("Kategorie löschen?"))
            deleteCategory(ctx.id)
              .then(() => toast.add("Kategorie gelöscht"))
              .catch(() => toast.add("Fehler", "error"));
        }},
      ];
    }
    return [
      { label: "? Als Default markieren", action: async () => {
        const catId = ctx.catId!;
        await categoriesApi.setDefault(ctx.id);
        fetchValues(catId);
      }},
      { label: "Umbenennen (F2)", action: () => {
        const val = (values[ctx.catId!] ?? []).find((v) => v.id === ctx.id);
        if (val) startEditVal(ctx.catId!, ctx.id, val.value);
      }},
      { label: "Löschen", danger: true, action: () => {
        if (confirm("Wert löschen?"))
          deleteValue(ctx.catId!, ctx.id)
            .then(() => toast.add("Wert gelöscht"))
            .catch(() => toast.add("Fehler", "error"));
      }},
    ];
  };

  if (loading) return <p className="text-slate-400 text-sm animate-pulse">Lade Kategorien...</p>;
  if (error) return <p className="text-red-500 text-sm">{error}</p>;

  return (
    <div>
      {/* Neue Kategorie */}
      <form onSubmit={handleAddCategory} className="flex gap-2 mb-4">
        <input ref={newCatRef} value={newCatName}
          onChange={(e) => setNewCatName(e.target.value)}
          placeholder="Neue Kategorie eingeben..."
          className="flex-1 px-3 py-1.5 text-sm rounded-lg border border-slate-200 focus:outline-none focus:ring-2 focus:ring-sky-400"
        />
        <button type="submit" disabled={!newCatName.trim()}
          className="px-3 py-1.5 bg-sky-600 text-white text-sm rounded-lg hover:bg-sky-700 disabled:opacity-40 font-bold">
          +
        </button>
      </form>

      {categories.length === 0 ? (
        <div className="flex flex-col items-center justify-center py-12 text-slate-400">
          <span className="text-4xl mb-2">+</span>
          <p className="text-sm">Noch keine Kategorien</p>
          <p className="text-xs mt-1">Gib oben einen Namen ein und klicke +</p>
        </div>
      ) : (
        <ul className="space-y-1.5">
          {categories.map((cat) => (
            <li key={cat.id}
              draggable
              onDragStart={() => handleDragStart(cat.id)}
              onDragOver={(e) => handleDragOver(e, cat.id)}
              onDrop={() => handleDrop(cat.id)}
              onDragEnd={() => setDragOverId(null)}
              onClick={() => setSelectedCatId(cat.id)}
              onContextMenu={(e) => openCtxCat(e, cat.id)}
              className={
                "border rounded-xl overflow-hidden transition-all cursor-grab " +
                (selectedCatId === cat.id ? "border-sky-400 shadow-sm" : "border-slate-200") +
                (dragOverId === cat.id ? " opacity-60 scale-95" : "")
              }
            >
              {/* Kategorie-Header */}
              <div
                className={"flex items-center justify-between px-3 py-2 hover:bg-slate-50 " +
                  (selectedCatId === cat.id ? "bg-sky-50" : "bg-slate-50")}
                onClick={(e) => { e.stopPropagation(); toggleExpand(cat.id); }}
              >
                <span className="flex items-center gap-2 font-medium text-sm text-slate-700 min-w-0">
                  <span className="text-slate-400 w-4 text-center select-none flex-shrink-0">
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
                      className="flex-1 px-1 py-0.5 text-sm border border-sky-400 rounded focus:outline-none"
                    />
                  ) : (
                    <span onDoubleClick={(e) => { e.stopPropagation(); startEditCat(cat.id, cat.name); }}
                      className="truncate">{cat.name}</span>
                  )}
                  {/* Werte-Zaehler Badge */}
                  <span className="ml-1 flex-shrink-0 text-xs bg-slate-200 text-slate-600 rounded-full px-1.5 py-0.5 font-normal">
                    {(values[cat.id] ?? []).length}
                  </span>
                </span>
                <span className="text-slate-300 text-xs ml-2 flex-shrink-0 select-none cursor-grab" title="Ziehen zum Sortieren">
                  :::
                </span>
              </div>

              {/* Werte-Liste */}
              {expanded[cat.id] && (
                <div className="px-3 py-2 bg-white border-t border-slate-100">
                  <ul className="space-y-0.5 mb-2">
                    {(values[cat.id] ?? []).length === 0 ? (
                      <li className="text-slate-400 text-xs italic py-1">Noch keine Werte</li>
                    ) : (
                      (values[cat.id] ?? []).map((v) => (
                        <li key={v.id}
                          onContextMenu={(e) => openCtxVal(e, cat.id, v.id)}
                          onClick={() => { setSelectedValId({ catId: cat.id, valId: v.id }); setSelectedCatId(null); }}
                          className={"flex items-center justify-between text-sm py-0.5 px-1 rounded hover:bg-slate-50 group" +
                            (selectedValId?.valId === v.id ? " bg-sky-50 ring-1 ring-sky-300" : "")}>
                          {editingVal?.valId === v.id ? (
                            <input autoFocus value={editingValName}
                              onChange={(e) => setEditingValName(e.target.value)}
                              onBlur={() => confirmEditVal(cat.id, v.id)}
                              onKeyDown={(e) => {
                                if (e.key === "Enter") confirmEditVal(cat.id, v.id);
                                if (e.key === "Escape") setEditingVal(null);
                              }}
                              className="flex-1 px-1 py-0.5 text-sm border border-sky-400 rounded focus:outline-none"
                            />
                          ) : (
                            <>
                              <span
                                onDoubleClick={() => startEditVal(cat.id, v.id, v.value)}
                                className={"text-slate-700 flex-1 truncate " +
                                  (v.risk_weight > 2 ? "text-orange-700 font-medium" : "")}>
                                {v.is_default && <span className="mr-1 text-amber-400" title="Default-Wert">?</span>}
                                {v.value}
                                {v.risk_weight > 2 && (
                                  <span className="ml-1 text-xs bg-orange-100 text-orange-600 rounded px-1">
                                    R{v.risk_weight}
                                  </span>
                                )}
                                {v.allowed === false && (
                                  <span className="ml-1 text-xs bg-red-100 text-red-500 rounded px-1" title="Fehlerwert">?</span>
                                )}
                              </span>
                              <div className="flex items-center gap-1 opacity-0 group-hover:opacity-100 transition-opacity">
                                {/* REQ-3007: Inline-Eigenschaften */}
                                <input
                                  type="number" min={1} max={10}
                                  value={v.risk_weight}
                                  title="Risiko (1-10)"
                                  onClick={(e) => e.stopPropagation()}
                                  onChange={async (e) => {
                                    const rw = Math.max(1, Math.min(10, Number(e.target.value)));
                                    await categoriesApi.updateProperties(v.id, { risk_weight: rw });
                                    fetchValues(cat.id);
                                  }}
                                  className="w-10 px-1 py-0.5 text-xs border border-slate-200 rounded text-center focus:outline-none focus:ring-1 focus:ring-sky-400"
                                />
                                <select
                                  value={v.vtype ?? "string"}
                                  title="Datentyp"
                                  onClick={(e) => e.stopPropagation()}
                                  onChange={async (e) => {
                                    await categoriesApi.updateProperties(v.id, { vtype: e.target.value });
                                    fetchValues(cat.id);
                                  }}
                                  className="text-xs border border-slate-200 rounded px-1 py-0.5 focus:outline-none focus:ring-1 focus:ring-sky-400"
                                >
                                  {["string","number","date","time","boolean","email","text"].map((t) => (
                                    <option key={t} value={t}>{t}</option>
                                  ))}
                                </select>
                                <input
                                  type="checkbox"
                                  checked={v.allowed === false}
                                  title="Fehlerwert"
                                  onClick={(e) => e.stopPropagation()}
                                  onChange={async (e) => {
                                    await categoriesApi.updateProperties(v.id, { allowed: !e.target.checked });
                                    fetchValues(cat.id);
                                  }}
                                  className="rounded border-slate-300 text-red-500"
                                />
                              </div>
                              <button onClick={() => deleteValue(cat.id, v.id)
                                .then(() => toast.add("Wert gelöscht"))
                                .catch(() => toast.add("Fehler", "error"))}
                                className="opacity-0 group-hover:opacity-100 text-red-300 hover:text-red-500 text-xs ml-2 transition-opacity">
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
                      placeholder="Neuer Wert... (Enter)"
                      className="flex-1 px-2 py-1 text-xs rounded border border-slate-200 focus:outline-none focus:ring-1 focus:ring-sky-400"
                    />
                    <button onClick={() => handleAddValue(cat.id)}
                      className="px-2 py-1 bg-slate-100 hover:bg-slate-200 text-xs rounded border border-slate-200">
                      +
                    </button>
                  </div>
                </div>
              )}
            </li>
          ))}
        </ul>
      )}

      {/* Datenklassen-Dialog */}
      {dataClassCat && (
        <DataClassDialog
          categoryId={dataClassCat.id}
          categoryName={dataClassCat.name}
          onClose={() => setDataClassCat(null)}
          onApplied={() => { if (expanded[dataClassCat.id]) fetchValues(dataClassCat.id); }}
        />
      )}

      {/* Kontextmenue */}
      {ctx && (
        <ContextMenu x={ctx.x} y={ctx.y} items={ctxItems()} onClose={() => setCtx(null)} />
      )}

      {/* Tastatur-Hilfe */}
      <div className="mt-4 pt-3 border-t border-slate-100 text-xs text-slate-400 space-y-0.5">
        <p>Alt+N: Neue Kategorie &nbsp; DEL: Löschen &nbsp; F2/Doppelklick: Umbenennen</p>
        <p>Rechtsklick: Kontextmenü &nbsp; Ziehen: Sortieren</p>
      </div>
    </div>
  );
}
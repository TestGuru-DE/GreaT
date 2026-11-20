// REQ-6001: Logischer Constraint-Editor (Builder)
// ADR-020: AST-Format fuer logische Constraints
// AK-1..4, AK-10
import { useEffect, useState, useCallback, useMemo } from "react";
import { useTranslation } from "react-i18next";
import {
  logicalConstraintsApi,
  categoriesApi,
  valuesApi,
} from "../api/client";
import type {
  LogicalConstraint,
  ConstraintKind,
  ConstraintNode,
  ConstraintAtom,
  ConstraintGroup,
  ConstraintNot,
  ConstraintCreatePayload,
} from "../api/client";
import type { Category, Value } from "../types";

/* ------------------------------------------------------------------ */
/*  Helper types for the builder's editable state                     */
/* ------------------------------------------------------------------ */

type BuilderOp = "eq" | "ne" | "in" | "not_in";
type GroupOp = "and" | "or";

interface BuilderAtom {
  _type: "atom";
  op: BuilderOp;
  category_id: number;
  value_id: number;
  value_ids: number[]; // for in / not_in
}

interface BuilderGroup {
  _type: "group";
  op: GroupOp;
  children: BuilderNode[];
}

interface BuilderNot {
  _type: "not";
  child: BuilderNode;
}

type BuilderNode = BuilderAtom | BuilderGroup | BuilderNot;

/* ------------------------------------------------------------------ */
/*  Conversion: Builder <-> AST                                        */
/* ------------------------------------------------------------------ */

function builderToAST(node: BuilderNode, _catValues: Record<number, Value[]>): ConstraintNode {
  switch (node._type) {
    case "atom": {
      const ast: ConstraintAtom = {
        op: node.op,
        category_id: node.category_id,
        value_id: node.value_id,
      };
      if ((node.op === "in" || node.op === "not_in") && node.value_ids.length > 0) {
        ast.value_ids = node.value_ids;
      }
      return ast;
    }
    case "group":
      return {
        op: node.op,
        args: node.children.map((c) => builderToAST(c, _catValues)),
      };
    case "not":
      return { op: "not", arg: builderToAST(node.child, _catValues) };
  }
}

function createAtom(categoryId: number, valueId: number): BuilderAtom {
  return { _type: "atom", op: "eq", category_id: categoryId, value_id: valueId, value_ids: [] };
}

function createAndGroup(): BuilderGroup {
  return { _type: "group", op: "and", children: [] };
}

function createOrGroup(): BuilderGroup {
  return { _type: "group", op: "or", children: [] };
}

// Convert AST (ConstraintNode) back to BuilderNode for editing
function astToBuilderNode(node: ConstraintNode): BuilderNode {
  if (!node) {
    // Fallback: should not happen, but return a dummy atom
    return { _type: "atom", op: "eq", category_id: 0, value_id: 0, value_ids: [] };
  }
  switch (node.op) {
    case "eq":
    case "ne":
    case "in":
    case "not_in": {
      const atom = node as ConstraintAtom;
      return {
        _type: "atom",
        op: atom.op as BuilderOp,
        category_id: atom.category_id,
        value_id: atom.value_id,
        value_ids: atom.value_ids ?? [],
      };
    }
    case "and":
    case "or": {
      const group = node as ConstraintGroup;
      return {
        _type: "group",
        op: group.op as GroupOp,
        children: (group.args ?? []).map((arg) => astToBuilderNode(arg)),
      };
    }
    case "not": {
      const notNode = node as ConstraintNot;
      return {
        _type: "not",
        child: astToBuilderNode(notNode.arg),
      };
    }
    default:
      // Unknown operator - return a dummy atom
      return { _type: "atom", op: "eq", category_id: 0, value_id: 0, value_ids: [] };
  }
}

/* ------------------------------------------------------------------ */
/*  Text rendering (AK-4)                                              */
/* ------------------------------------------------------------------ */

function nodeToText(node: ConstraintNode, categories: Category[], catValues: Record<number, Value[]>): string {
  if (!node) return "";
  switch (node.op) {
    case "eq":
    case "ne": {
      const cat = categories.find((c) => c.id === (node as ConstraintAtom).category_id);
      const val = catValues[(node as ConstraintAtom).category_id]?.find(
        (v) => v.id === (node as ConstraintAtom).value_id
      );
      const opSymbol = node.op === "eq" ? "=" : "!=";
      return `${cat?.name ?? "?"} ${opSymbol} "${val?.value ?? "?"}"`;
    }
    case "in":
    case "not_in": {
      const cat = categories.find((c) => c.id === (node as ConstraintAtom).category_id);
      const ids = (node as ConstraintAtom).value_ids ?? [(node as ConstraintAtom).value_id];
      const vals = ids
        .map((id) => catValues[(node as ConstraintAtom).category_id]?.find((v) => v.id === id)?.value ?? "?")
        .join(", ");
      const opSymbol = node.op === "in" ? "IN" : "NOT IN";
      return `${cat?.name ?? "?"} ${opSymbol} {${vals}}`;
    }
    case "and":
      return (node as ConstraintGroup).args.map((a) => nodeToText(a, categories, catValues)).join(" AND ");
    case "or":
      return (node as ConstraintGroup).args.map((a) => nodeToText(a, categories, catValues)).join(" OR ");
    case "not":
      return `NOT (${nodeToText((node as ConstraintNot).arg, categories, catValues)})`;
    default:
      return "(?)";
  }
}

function buildTextPreview(
  kind: ConstraintKind,
  condition: ConstraintNode | null,
  consequence: ConstraintNode | null,
  categories: Category[],
  catValues: Record<number, Value[]>
): string {
  const condText = condition ? nodeToText(condition, categories, catValues) : "";
  if (kind === "forbid") {
    return condText ? `NOT (${condText})` : "";
  }
  // implies
  const consText = consequence ? nodeToText(consequence, categories, catValues) : "";
  if (!condText && !consText) return "";
  return `IF ${condText || "(?)" } THEN ${consText || "(?)"}`;
}

/* ------------------------------------------------------------------ */
/*  Sub-components                                                     */
/* ------------------------------------------------------------------ */

interface AtomEditorProps {
  atom: BuilderAtom;
  categories: Category[];
  catValues: Record<number, Value[]>;
  onChange: (a: BuilderAtom) => void;
  onRemove: () => void;
  onWrapNot: () => void;
  isNegated: boolean;
}

function AtomEditor({ atom, categories, catValues, onChange, onRemove, onWrapNot, isNegated }: AtomEditorProps) {
  const { t } = useTranslation();
  const vals = catValues[atom.category_id] ?? [];
  const isMulti = atom.op === "in" || atom.op === "not_in";

  return (
    <div className={`flex flex-wrap items-center gap-2 px-3 py-2 rounded-lg border text-sm transition-colors ${
      isNegated ? "bg-amber-50 border-amber-200" : "bg-white border-slate-200"
    }`}>
      {/* NOT toggle */}
      <button
        type="button"
        onClick={onWrapNot}
        className={`text-xs font-semibold px-1.5 py-0.5 rounded transition-colors ${
          isNegated ? "bg-amber-500 text-white" : "bg-slate-100 text-slate-500 hover:bg-slate-200"
        }`}
        title={t("constraintBuilder.not")}
      >
        {t("constraintBuilder.not")}
      </button>

      {/* Category */}
      <select
        value={atom.category_id}
        onChange={(e) => onChange({ ...atom, category_id: Number(e.target.value) })}
        className="px-2 py-1 text-xs border border-slate-300 rounded bg-white text-black"
        aria-label={t("constraintBuilder.category")}
      >
        {categories.map((c) => <option key={c.id} value={c.id}>{c.name}</option>)}
      </select>

      {/* Operator */}
      <select
        value={atom.op}
        onChange={(e) => onChange({ ...atom, op: e.target.value as BuilderOp })}
        className="px-2 py-1 text-xs border border-slate-300 rounded bg-white text-black"
        aria-label={t("constraintBuilder.operator")}
      >
        {[
          { v: "eq", l: t("constraintBuilder.valueEquals") },
          { v: "ne", l: t("constraintBuilder.valueNotEquals") },
          { v: "in", l: t("constraintBuilder.valueIn") },
          { v: "not_in", l: t("constraintBuilder.valueNotIn") },
        ].map(({ v, l }) => <option key={v} value={v}>{l}</option>)}
      </select>

      {/* Value(s) */}
      {isMulti ? (
        <div className="flex flex-wrap gap-1 px-2 py-1 border border-slate-300 rounded bg-white min-h-[26px]">
          {vals.map((v) => {
            const checked = atom.value_ids.includes(v.id);
            return (
              <button
                key={v.id}
                type="button"
                onClick={() => {
                  const ids = checked ? atom.value_ids.filter((i) => i !== v.id) : [...atom.value_ids, v.id];
                  onChange({ ...atom, value_ids: ids, value_id: ids[0] ?? v.id });
                }}
                className={`px-1.5 py-0.5 rounded text-xs transition-colors ${
                  checked ? "bg-sky-500 text-white" : "bg-slate-100 text-slate-600 hover:bg-slate-200"
                }`}
              >
                {v.value}
              </button>
            );
          })}
        </div>
      ) : (
        <select
          value={atom.value_id}
          onChange={(e) => onChange({ ...atom, value_id: Number(e.target.value) })}
          className="px-2 py-1 text-xs border border-slate-300 rounded bg-white text-black"
          aria-label={t("constraintBuilder.value")}
        >
          {vals.map((v) => <option key={v.id} value={v.id}>{v.value}</option>)}
        </select>
      )}

      {/* Remove */}
      <button
        type="button"
        onClick={onRemove}
        className="text-slate-400 hover:text-red-500 text-lg leading-none ml-1"
        title={t("common.delete")}
      >
        ×
      </button>
    </div>
  );
}

interface GroupEditorProps {
  group: BuilderGroup;
  categories: Category[];
  catValues: Record<number, Value[]>;
  onChange: (g: BuilderGroup) => void;
  onRemove: () => void;
}

function GroupEditor({ group, categories, catValues, onChange, onRemove }: GroupEditorProps) {
  const { t } = useTranslation();

  function setChildren(children: BuilderNode[]) {
    onChange({ ...group, children });
  }

  function setChild(index: number, child: BuilderNode) {
    setChildren(group.children.map((c, i) => (i === index ? child : c)));
  }

  function addChild(node: BuilderNode) {
    setChildren([...group.children, node]);
  }

  function removeChild(index: number) {
    setChildren(group.children.filter((_, i) => i !== index));
  }

  function wrapInNot(index: number) {
    const child = group.children[index];
    const existing: BuilderNot = child._type === "not"
      ? { _type: "not", child: child.child }
      : { _type: "not", child };
    setChild(index, existing);
  }

  const isNegated = (index: number) => group.children[index]?._type === "not";

  return (
    <div className="ml-4 border-l-2 border-slate-300 pl-3 space-y-2">
      <div className="flex items-center gap-2">
        <span className={`text-xs font-bold px-2 py-0.5 rounded ${
          group.op === "and" ? "bg-sky-100 text-sky-700" : "bg-violet-100 text-violet-700"
        }`}>
          {group.op === "and" ? t("constraintBuilder.andGroup") : t("constraintBuilder.orGroup")}
        </span>
        <button
          type="button"
          onClick={() => onChange({ ...group, op: group.op === "and" ? "or" : "and" })}
          className="text-xs text-slate-400 hover:text-slate-600"
          title={t("constraintBuilder.addGroup")}
        >
          {t("constraintBuilder.addGroup")}
        </button>
        <button
          type="button"
          onClick={onRemove}
          className="text-slate-400 hover:text-red-500 text-sm"
          title={t("common.delete")}
        >
          ×
        </button>
      </div>

      {group.children.map((child, i) => {
        if (child._type === "atom") {
          return (
            <AtomEditor
              key={i}
              atom={child}
              categories={categories}
              catValues={catValues}
              isNegated={isNegated(i)}
              onChange={(a) => setChild(i, a)}
              onRemove={() => removeChild(i)}
              onWrapNot={() => wrapInNot(i)}
            />
          );
        }
        if (child._type === "group") {
          return (
            <GroupEditor
              key={i}
              group={child}
              categories={categories}
              catValues={catValues}
              onChange={(g) => setChild(i, g)}
              onRemove={() => removeChild(i)}
            />
          );
        }
        if (child._type === "not") {
          return (
            <div key={i} className="flex items-center gap-2">
              <span className="text-xs font-bold text-amber-600">{t("constraintBuilder.not")}</span>
              {child.child._type === "atom" && (
                <AtomEditor
                  atom={child.child}
                  categories={categories}
                  catValues={catValues}
                  isNegated={true}
                  onChange={(a) => setChild(i, { _type: "not", child: a })}
                  onRemove={() => removeChild(i)}
                  onWrapNot={() => wrapInNot(i)}
                />
              )}
              {child.child._type === "group" && (
                <GroupEditor
                  group={child.child}
                  categories={categories}
                  catValues={catValues}
                  onChange={(g) => setChild(i, { _type: "not", child: g })}
                  onRemove={() => removeChild(i)}
                />
              )}
            </div>
          );
        }
        return null;
      })}

      <div className="flex gap-2">
        <button
          type="button"
          onClick={() => {
            const firstCat = categories[0]?.id ?? 0;
            const firstVal = catValues[firstCat]?.[0]?.id ?? 0;
            addChild(createAtom(firstCat, firstVal));
          }}
          className="text-xs text-sky-600 hover:text-sky-800"
        >
          + {t("constraintBuilder.addCondition")}
        </button>
        <button
          type="button"
          onClick={() => addChild(createAndGroup())}
          className="text-xs text-sky-600 hover:text-sky-800"
        >
          + {t("constraintBuilder.andGroup")}
        </button>
        <button
          type="button"
          onClick={() => addChild(createOrGroup())}
          className="text-xs text-violet-600 hover:text-violet-800"
        >
          + {t("constraintBuilder.orGroup")}
        </button>
      </div>
    </div>
  );
}

interface ConditionBuilderProps {
  nodes: BuilderNode[];
  categories: Category[];
  catValues: Record<number, Value[]>;
  onChange: (nodes: BuilderNode[]) => void;
  label: string;
}

function ConditionBuilder({ nodes, categories, catValues, onChange, label }: ConditionBuilderProps) {
  const { t } = useTranslation();

  function setNode(index: number, node: BuilderNode) {
    onChange(nodes.map((n, i) => (i === index ? node : n)));
  }

  function addNode(node: BuilderNode) {
    onChange([...nodes, node]);
  }

  function removeNode(index: number) {
    onChange(nodes.filter((_, i) => i !== index));
  }

  function wrapInNot(index: number) {
    const node = nodes[index];
    const existing: BuilderNot = node._type === "not"
      ? { _type: "not", child: node.child }
      : { _type: "not", child: node };
    setNode(index, existing);
  }

  const isNegated = (index: number) => nodes[index]?._type === "not";

  return (
    <div className="space-y-2">
      <h4 className="text-xs font-semibold text-slate-500 uppercase tracking-wide">{label}</h4>
      {nodes.length === 0 && (
        <p className="text-xs text-slate-400 italic">{t("constraintBuilder.emptyCondition")}</p>
      )}
      {nodes.map((node, i) => {
        if (node._type === "atom") {
          return (
            <AtomEditor
              key={i}
              atom={node}
              categories={categories}
              catValues={catValues}
              isNegated={isNegated(i)}
              onChange={(a) => setNode(i, a)}
              onRemove={() => removeNode(i)}
              onWrapNot={() => wrapInNot(i)}
            />
          );
        }
        if (node._type === "group") {
          return (
            <GroupEditor
              key={i}
              group={node}
              categories={categories}
              catValues={catValues}
              onChange={(g) => setNode(i, g)}
              onRemove={() => removeNode(i)}
            />
          );
        }
        if (node._type === "not") {
          return (
            <div key={i} className="flex items-center gap-2">
              <span className="text-xs font-bold text-amber-600">{t("constraintBuilder.not")}</span>
              {node.child._type === "atom" && (
                <AtomEditor
                  atom={node.child}
                  categories={categories}
                  catValues={catValues}
                  isNegated={true}
                  onChange={(a) => setNode(i, { _type: "not", child: a })}
                  onRemove={() => removeNode(i)}
                  onWrapNot={() => wrapInNot(i)}
                />
              )}
              {node.child._type === "group" && (
                <GroupEditor
                  group={node.child}
                  categories={categories}
                  catValues={catValues}
                  onChange={(g) => setNode(i, { _type: "not", child: g })}
                  onRemove={() => removeNode(i)}
                />
              )}
            </div>
          );
        }
        return null;
      })}
      <div className="flex gap-2 flex-wrap">
        <button
          type="button"
          onClick={() => {
            const firstCat = categories[0]?.id ?? 0;
            const firstVal = catValues[firstCat]?.[0]?.id ?? 0;
            addNode(createAtom(firstCat, firstVal));
          }}
          className="text-xs text-sky-600 hover:text-sky-800"
        >
          + {t("constraintBuilder.addCondition")}
        </button>
        <button
          type="button"
          onClick={() => addNode(createAndGroup())}
          className="text-xs text-sky-600 hover:text-sky-800"
        >
          + {t("constraintBuilder.andGroup")}
        </button>
        <button
          type="button"
          onClick={() => addNode(createOrGroup())}
          className="text-xs text-violet-600 hover:text-violet-800"
        >
          + {t("constraintBuilder.orGroup")}
        </button>
      </div>
    </div>
  );
}

/* ------------------------------------------------------------------ */
/*  Main Component                                                     */
/* ------------------------------------------------------------------ */

interface Props {
  projectId: number;
}

export default function ConstraintBuilder({ projectId }: Props) {
  const { t } = useTranslation();
  const [constraints, setConstraints] = useState<LogicalConstraint[]>([]);
  const [categories, setCategories] = useState<Category[]>([]);
  const [catValues, setCatValues] = useState<Record<number, Value[]>>({});
  const [loading, setLoading] = useState(true);
  const [msg, setMsg] = useState<{ text: string; type: "ok" | "warn" | "error" } | null>(null);

  // Form state
  const [editingId, setEditingId] = useState<number | null>(null);
  const [name, setName] = useState("");
  const [kind, setKind] = useState<ConstraintKind>("forbid");
  const [conditionNodes, setConditionNodes] = useState<BuilderNode[]>([]);
  const [consequenceNodes, setConsequenceNodes] = useState<BuilderNode[]>([]);

  const loadData = useCallback(async () => {
    setLoading(true);
    setMsg(null);
    try {
      const [constrList, catList] = await Promise.all([
        logicalConstraintsApi.list(projectId),
        categoriesApi.list(projectId),
      ]);
      setConstraints(constrList);
      setCategories(catList);
      const valMap: Record<number, Value[]> = {};
      await Promise.all(catList.map(async (c) => {
        const vals = await valuesApi.list(c.id);
        valMap[c.id] = vals;
      }));
      setCatValues(valMap);
    } catch (err: unknown) {
      const message = err instanceof Error ? err.message : String(err);
      console.error("[ConstraintBuilder] loadData failed:", err);
      setMsg({
        text: t("constraintBuilder.loadError", { error: message }),
        type: "error",
      });
    } finally {
      setLoading(false);
    }
  }, [projectId, t]);

  useEffect(() => { loadData(); }, [loadData]);

  // Reset form
  const resetForm = useCallback(() => {
    setEditingId(null);
    setName("");
    setKind("forbid");
    setConditionNodes([]);
    setConsequenceNodes([]);
    setMsg(null);
  }, []);

  // Load constraint for editing
  const startEdit = useCallback((c: LogicalConstraint) => {
    setEditingId(c.id);
    setName(c.name);
    setKind(c.kind);
    // Convert AST back to builder nodes for editing
    setConditionNodes(c.expression ? [astToBuilderNode(c.expression)] : []);
    setConsequenceNodes(c.consequence ? [astToBuilderNode(c.consequence)] : []);
    setMsg(null);
  }, []);

  // Build AST from builder state
  const buildAST = useCallback((): { condition: ConstraintNode | null; consequence: ConstraintNode | null } => {
    // FIX: Bei nur 1 Bedingung: nutze sie direkt (keine AND-Gruppe)
    // Bei >1 Bedingungen: wickle in AND-Gruppe
    const cond = conditionNodes.length === 0
      ? null
      : conditionNodes.length === 1
        ? builderToAST(conditionNodes[0], catValues)
        : builderToAST({ _type: "group", op: "and", children: conditionNodes }, catValues);
    
    const cons = consequenceNodes.length === 0
      ? null
      : consequenceNodes.length === 1
        ? builderToAST(consequenceNodes[0], catValues)
        : builderToAST({ _type: "group", op: "and", children: consequenceNodes }, catValues);
    
    return { condition: cond, consequence: cons };
  }, [conditionNodes, consequenceNodes, catValues]);

  // Text preview
  const textPreview = useMemo(() => {
    const { condition, consequence } = buildAST();
    return buildTextPreview(kind, condition, consequence, categories, catValues);
  }, [kind, buildAST, categories, catValues]);

  // Save
  const handleSave = async () => {
    if (!name.trim()) {
      setMsg({ text: t("constraintBuilder.saveError"), type: "error" });
      return;
    }
    const { condition, consequence } = buildAST();
    if (!condition) {
      setMsg({ text: t("constraintBuilder.saveError"), type: "error" });
      return;
    }
    if (kind === "implies" && !consequence) {
      setMsg({ text: t("constraintBuilder.saveError"), type: "error" });
      return;
    }

    const payload: ConstraintCreatePayload = {
      name: name.trim(),
      kind,
      expression: condition,
    };
    if (kind === "implies" && consequence) {
      payload.consequence = consequence;
    }

    try {
      // Validate first
      try {
        const validation = await logicalConstraintsApi.validate(projectId, payload);
        if (!validation.is_valid && validation.errors.length > 0) {
          setMsg({ text: t("constraintBuilder.validationError", { errors: validation.errors.join("; ") }), type: "error" });
          return;
        }
      } catch (validationErr: unknown) {
        // Validation endpoint might not exist yet; proceed with save
        console.warn("[ConstraintBuilder] Validation failed, proceeding with save:", validationErr);
      }

      if (editingId) {
        const updated = await logicalConstraintsApi.update(projectId, editingId, payload);
        setConstraints((prev) => prev.map((c) => (c.id === updated.id ? updated : c)));
      } else {
        const created = await logicalConstraintsApi.create(projectId, payload);
        setConstraints((prev) => [...prev, created]);
      }
      // Reset form state first (without clearing msg)
      setEditingId(null);
      setName("");
      setKind("forbid");
      setConditionNodes([]);
      setConsequenceNodes([]);
      setMsg({ text: t("constraintBuilder.saved"), type: "ok" });
      setTimeout(() => setMsg(null), 4000);
    } catch (err: unknown) {
      console.error("[ConstraintBuilder] Save failed:", err);

      // Extract detailed error from axios response
      let userMessage = t("constraintBuilder.saveError");

      // Axios error structure
      if (err && typeof err === "object" && "response" in err) {
        const axiosErr = err as { response?: { data?: { message?: string; errors?: string[] }; status?: number } };
        const data = axiosErr.response?.data;
        const status = axiosErr.response?.status;

        if (data?.errors && Array.isArray(data.errors) && data.errors.length > 0) {
          userMessage = t("constraintBuilder.validationError", { errors: data.errors.join("; ") });
        } else if (data?.message) {
          userMessage = data.message;
        } else if (status === 400) {
          userMessage = "Speicherfehler: Ungueltiger Constraint. Bitte pruefe Bedingung und Folge.";
        } else if (status === 404) {
          userMessage = "Projekt nicht gefunden.";
        } else if (status === 401 || status === 403) {
          userMessage = "Nicht autorisiert. Bitte erneut anmelden.";
        } else {
          userMessage = `Speicherfehler (HTTP ${status}). Bitte versuche es erneut.`;
        }
      } else if (err instanceof Error) {
        userMessage = `Fehler: ${err.message}`;
      }

      setMsg({ text: userMessage, type: "error" });
    }
  };

  // Delete
  const handleDelete = async (c: LogicalConstraint) => {
    if (!confirm(t("constraintBuilder.deleteConfirm", { name: c.name }))) return;
    try {
      await logicalConstraintsApi.delete(projectId, c.id);
      setConstraints((prev) => prev.filter((x) => x.id !== c.id));
    } catch {
      setMsg({ text: t("constraintBuilder.saveError"), type: "error" });
    }
  };

  // Copy text
  const [copied, setCopied] = useState(false);
  const handleCopy = () => {
    navigator.clipboard.writeText(textPreview).then(() => {
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    });
  };

  if (loading) return <p className="text-slate-400 text-sm animate-pulse">{t("common.loading")}</p>;
  if (categories.length === 0) {
    if (msg && msg.type === "error") return (
      <div className="text-center py-8">
        <div className="px-3 py-2 rounded-lg text-sm bg-red-50 border border-red-200 text-red-700 inline-block">
          {msg.text}
        </div>
      </div>
    );
    return (
      <div className="text-center py-8 text-slate-400">
        <p className="text-sm">{t("constraintBuilder.needOneCategory")}</p>
      </div>
    );
  }

  return (
    <div className="flex flex-col gap-5">
      {/* Builder + Preview (two-pane) */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        {/* Left: Builder */}
        <div className="border border-slate-200 rounded-2xl p-4 bg-slate-50 space-y-4">
          <h3 className="text-sm font-semibold text-slate-700">
            {editingId ? t("common.edit") : t("constraintBuilder.title")}
          </h3>

          {msg && (
            <div className={`px-3 py-2 rounded-lg text-sm ${
              msg.type === "ok" ? "bg-green-50 border border-green-200 text-green-700" :
              msg.type === "warn" ? "bg-amber-50 border border-amber-200 text-amber-700" :
              "bg-red-50 border border-red-200 text-red-700"
            }`}>
              {msg.text}
            </div>
          )}

          {/* Name */}
          <div>
            <label className="text-xs font-medium text-slate-500 mb-1 block">{t("constraintBuilder.name")}</label>
            <input
              type="text"
              value={name}
              onChange={(e) => setName(e.target.value)}
              placeholder={t("constraintBuilder.namePlaceholder")}
              className="w-full px-3 py-1.5 text-sm border border-slate-300 rounded-lg focus:outline-none focus:ring-1 focus:ring-sky-400 bg-white text-black"
            />
          </div>

          {/* Kind */}
          <div>
            <label className="text-xs font-medium text-slate-500 mb-1 block">{t("constraintBuilder.kind")}</label>
            <select
              value={kind}
              onChange={(e) => setKind(e.target.value as ConstraintKind)}
              className="w-full px-3 py-1.5 text-sm border border-slate-300 rounded-lg focus:outline-none focus:ring-1 focus:ring-sky-400 bg-white text-black"
            >
              <option value="forbid">{t("constraintBuilder.forbid")}</option>
              <option value="implies">{t("constraintBuilder.implies")}</option>
            </select>
          </div>

          {/* Condition */}
          <ConditionBuilder
            nodes={conditionNodes}
            categories={categories}
            catValues={catValues}
            onChange={setConditionNodes}
            label={t("constraintBuilder.condition")}
          />

          {/* Consequence (only for implies) */}
          {kind === "implies" && (
            <ConditionBuilder
              nodes={consequenceNodes}
              categories={categories}
              catValues={catValues}
              onChange={setConsequenceNodes}
              label={t("constraintBuilder.consequence")}
            />
          )}

          {/* Buttons */}
          <div className="flex gap-2">
            <button
              onClick={handleSave}
              className="flex-1 py-2 bg-sky-600 text-white text-sm font-medium rounded-xl hover:bg-sky-700 transition-colors"
            >
              {t("constraintBuilder.save")}
            </button>
            {editingId && (
              <button
                onClick={resetForm}
                className="px-4 py-2 bg-slate-200 text-slate-700 text-sm rounded-xl hover:bg-slate-300 transition-colors"
              >
                {t("common.cancel")}
              </button>
            )}
          </div>
        </div>

        {/* Right: Preview */}
        <div className="border border-slate-200 rounded-2xl p-4 bg-white flex flex-col">
          <div className="flex items-center justify-between mb-3">
            <h3 className="text-sm font-semibold text-slate-700">{t("constraintBuilder.textPreview")}</h3>
            <button
              type="button"
              onClick={handleCopy}
              className="text-xs text-sky-600 hover:text-sky-800"
              disabled={!textPreview}
            >
              {copied ? t("constraintBuilder.copied") : t("constraintBuilder.copy")}
            </button>
          </div>
          <div className="flex-1 overflow-auto">
            {textPreview ? (
              <pre className="text-sm font-mono text-slate-700 whitespace-pre-wrap bg-slate-50 rounded-xl p-4 border border-slate-200">
                {textPreview}
              </pre>
            ) : (
              <p className="text-xs text-slate-400 italic">{t("constraintBuilder.emptyCondition")}</p>
            )}
          </div>
        </div>
      </div>

      {/* Existing constraints list */}
      <div>
        <h3 className="text-sm font-semibold text-slate-700 mb-2">
          {t("constraintBuilder.title")} ({constraints.length})
        </h3>
        {constraints.length === 0 ? (
          <p className="text-xs text-slate-400 text-center py-4">{t("constraintBuilder.noConstraints")}</p>
        ) : (
          <ul className="space-y-2">
            {constraints.map((c) => {
              const invalid = !c.is_valid;
              return (
                <li
                  key={c.id}
                  className={`flex items-start gap-3 px-3 py-2.5 border rounded-xl text-sm ${
                    invalid
                      ? "bg-slate-100 border-slate-300 text-slate-400"
                      : "bg-white border-slate-200 hover:bg-slate-50 text-black"
                  }`}
                >
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2 flex-wrap">
                      <span className="font-medium truncate">{c.name}</span>
                      <span className={`text-xs px-1.5 py-0.5 rounded ${
                        c.kind === "forbid"
                          ? "bg-red-50 text-red-600 border border-red-200"
                          : "bg-emerald-50 text-emerald-600 border border-emerald-200"
                      }`}>
                        {c.kind === "forbid" ? t("constraintBuilder.forbid") : t("constraintBuilder.implies")}
                      </span>
                      {invalid && (
                        <span className="text-xs text-amber-600">
                          ⚠️ {t("constraintBuilder.invalidConstraint", { reason: t("constraintBuilder.invalidConstraint") })}
                        </span>
                      )}
                    </div>
                    <p className="text-xs text-slate-500 mt-0.5 truncate">
                      {buildTextPreview(c.kind, c.expression, c.consequence ?? null, categories, catValues)}
                    </p>
                  </div>
                  <div className="flex items-center gap-1 shrink-0">
                    <button
                      onClick={() => startEdit(c)}
                      className="text-slate-400 hover:text-sky-600 text-sm"
                      title={t("constraintBuilder.edit")}
                    >
                      ✏️
                    </button>
                    <button
                      onClick={() => handleDelete(c)}
                      className="text-slate-300 hover:text-red-500 text-lg leading-none"
                      title={t("constraintBuilder.deleteTitle")}
                    >
                      ×
                    </button>
                  </div>
                </li>
              );
            })}
          </ul>
        )}
      </div>
    </div>
  );
}
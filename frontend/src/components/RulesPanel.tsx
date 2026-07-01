// REQ-1216 + REQ-3003 + REQ-3004: Regeleditor und Regelanzeige in React
import { useEffect, useState, useCallback } from "react";
import { rulesApi, categoriesApi } from "../api/client";
import type { Rule } from "../api/client";
import type { Category } from "../types";

interface Props { projectId: number; }

const TYPE_LABELS: Record<string, string> = {
  exclude:    "Verboten (Paar nicht gemeinsam)",
  dependency: "Abhängig (Wenn/Dann)",
  combine:    "Kombinieren (Fan-out)",
};
const TYPE_BADGE: Record<string, string> = {
  exclude:    "bg-red-50 text-red-600 border border-red-200",
  dependency: "bg-violet-50 text-violet-600 border border-violet-200",
  combine:    "bg-emerald-50 text-emerald-600 border border-emerald-200",
};

type RuleWithConflict = Rule & { conflict_with?: number[] };

export default function RulesPanel({ projectId }: Props) {
  const [rules, setRules] = useState<RuleWithConflict[]>([]);
  const [categories, setCategories] = useState<Category[]>([]);
  const [catValues, setCatValues] = useState<Record<number, string[]>>({});
  const [loading, setLoading] = useState(true);
  const [msg, setMsg] = useState<{ text: string; type: "ok" | "warn" | "error" } | null>(null);

  // Formular-State
  const [form, setForm] = useState({
    type: "dependency",
    if_cat: 0,
    if_val: "",
    then_cat: 0,
    then_val: "",
    then_vals: [] as string[],
  });

  const loadData = useCallback(async () => {
    setLoading(true);
    try {
      const [ruleList, catList] = await Promise.all([
        rulesApi.list(projectId),
        categoriesApi.list(projectId),
      ]);
      setRules(ruleList);
      setCategories(catList);
      // Werte für alle Kategorien laden
      const valMap: Record<number, string[]> = {};
      await Promise.all(catList.map(async (c) => {
        const vals = await categoriesApi.getValues(c.id);
        valMap[c.id] = vals.map((v) => v.value);
      }));
      setCatValues(valMap);
      if (catList.length > 0) {
        setForm((f) => ({
          ...f,
          if_cat: f.if_cat || catList[0].id,
          then_cat: f.then_cat || (catList[1]?.id ?? catList[0].id),
        }));
      }
    } finally {
      setLoading(false);
    }
  }, [projectId]);

  useEffect(() => { loadData(); }, [loadData]);

  // Werte für if_cat / then_cat automatisch füllen
  useEffect(() => {
    const vals = catValues[form.if_cat] ?? [];
    setForm((f) => ({ ...f, if_val: vals[0] ?? "" }));
  }, [form.if_cat, catValues]);

  useEffect(() => {
    const vals = catValues[form.then_cat] ?? [];
    setForm((f) => ({ ...f, then_val: vals[0] ?? "", then_vals: vals.length > 0 ? [vals[0]] : [] }));
  }, [form.then_cat, catValues]);

  const catName = (id: number) => categories.find((c) => c.id === id)?.name ?? "Kategorie #" + id;

  const handleCreate = async () => {
    if (!form.if_val || (!form.then_val && form.type !== "combine")) return;
    if (form.type === "combine" && form.then_vals.length === 0) return;
    try {
      const created = await rulesApi.create(projectId, {
        type: form.type,
        if_category_id: form.if_cat,
        if_value: form.if_val,
        then_category_id: form.then_cat,
        then_value: form.type !== "combine" ? form.then_val : undefined,
        then_values: form.type === "combine" ? form.then_vals : undefined,
      });
      setRules((prev) => [...prev, created]);
      if (created.conflict_with && created.conflict_with.length > 0) {
        setMsg({ text: `Regelwiderspruch mit Regel #${created.conflict_with.join(", #")}`, type: "warn" });
      } else {
        setMsg({ text: "Regel gespeichert.", type: "ok" });
      }
      setTimeout(() => setMsg(null), 4000);
    } catch {
      setMsg({ text: "Fehler beim Speichern.", type: "error" });
    }
  };

  const handleDelete = async (rid: number) => {
    if (!confirm("Regel löschen?")) return;
    await rulesApi.delete(projectId, rid);
    setRules((prev) => prev.filter((r) => r.id !== rid));
  };

  const toggleCombineVal = (val: string) => {
    setForm((f) => ({
      ...f,
      then_vals: f.then_vals.includes(val)
        ? f.then_vals.filter((v) => v !== val)
        : [...f.then_vals, val],
    }));
  };

  if (loading) return <p className="text-slate-400 text-sm animate-pulse">Lade Regeln...</p>;
  if (categories.length < 2) return (
    <div className="text-center py-8 text-slate-400">
      <p className="text-sm">Mindestens zwei Kategorien erforderlich um Regeln anzulegen.</p>
    </div>
  );

  const ifVals = catValues[form.if_cat] ?? [];
  const thenVals = catValues[form.then_cat] ?? [];

  return (
    <div className="flex flex-col gap-5">
      {/* Regel anlegen – REQ-3003 */}
      <div className="border border-slate-200 rounded-2xl p-4 bg-slate-50">
        <h3 className="text-sm font-semibold text-slate-700 mb-3">Neue Regel anlegen</h3>

        {msg && (
          <div className={`mb-3 px-3 py-2 rounded-lg text-sm ${
            msg.type === "ok" ? "bg-green-50 border border-green-200 text-green-700" :
            msg.type === "warn" ? "bg-amber-50 border border-amber-200 text-amber-700" :
            "bg-red-50 border border-red-200 text-red-700"
          }`}>
            {msg.type === "warn" && "⚠️ "}{msg.text}
          </div>
        )}

        <div className="grid grid-cols-1 gap-3">
          {/* Typ */}
          <div>
            <label className="text-xs font-medium text-slate-500 mb-1 block">Regeltyp</label>
            <select
              value={form.type}
              onChange={(e) => setForm((f) => ({ ...f, type: e.target.value }))}
              className="w-full px-3 py-1.5 text-sm border border-slate-300 rounded-lg focus:outline-none focus:ring-1 focus:ring-sky-400 bg-white"
            >
              {Object.entries(TYPE_LABELS).map(([val, label]) => (
                <option key={val} value={val}>{label}</option>
              ))}
            </select>
          </div>

          {/* Wenn-Block */}
          <div className="grid grid-cols-2 gap-2">
            <div>
              <label className="text-xs font-medium text-slate-500 mb-1 block">Wenn Kategorie</label>
              <select
                value={form.if_cat}
                onChange={(e) => setForm((f) => ({ ...f, if_cat: Number(e.target.value) }))}
                className="w-full px-3 py-1.5 text-sm border border-slate-300 rounded-lg focus:outline-none focus:ring-1 focus:ring-sky-400 bg-white"
              >
                {categories.map((c) => <option key={c.id} value={c.id}>{c.name}</option>)}
              </select>
            </div>
            <div>
              <label className="text-xs font-medium text-slate-500 mb-1 block">Wert</label>
              <select
                value={form.if_val}
                onChange={(e) => setForm((f) => ({ ...f, if_val: e.target.value }))}
                className="w-full px-3 py-1.5 text-sm border border-slate-300 rounded-lg focus:outline-none focus:ring-1 focus:ring-sky-400 bg-white"
              >
                {ifVals.map((v) => <option key={v} value={v}>{v}</option>)}
              </select>
            </div>
          </div>

          {/* Dann-Block */}
          <div className="grid grid-cols-2 gap-2">
            <div>
              <label className="text-xs font-medium text-slate-500 mb-1 block">
                {form.type === "exclude" ? "Paar-Kategorie" : "Dann Kategorie"}
              </label>
              <select
                value={form.then_cat}
                onChange={(e) => setForm((f) => ({ ...f, then_cat: Number(e.target.value) }))}
                className="w-full px-3 py-1.5 text-sm border border-slate-300 rounded-lg focus:outline-none focus:ring-1 focus:ring-sky-400 bg-white"
              >
                {categories.map((c) => <option key={c.id} value={c.id}>{c.name}</option>)}
              </select>
            </div>
            <div>
              <label className="text-xs font-medium text-slate-500 mb-1 block">
                {form.type === "combine" ? "Erlaubte Werte (Mehrfachauswahl)" : "Wert"}
              </label>
              {form.type === "combine" ? (
                <div className="flex flex-wrap gap-1 p-2 border border-slate-300 rounded-lg bg-white min-h-[34px]">
                  {thenVals.map((v) => (
                    <button
                      key={v}
                      type="button"
                      onClick={() => toggleCombineVal(v)}
                      className={`px-2 py-0.5 rounded text-xs transition-colors ${
                        form.then_vals.includes(v)
                          ? "bg-sky-500 text-white"
                          : "bg-slate-100 text-slate-600 hover:bg-slate-200"
                      }`}
                    >
                      {v}
                    </button>
                  ))}
                </div>
              ) : (
                <select
                  value={form.then_val}
                  onChange={(e) => setForm((f) => ({ ...f, then_val: e.target.value }))}
                  className="w-full px-3 py-1.5 text-sm border border-slate-300 rounded-lg focus:outline-none focus:ring-1 focus:ring-sky-400 bg-white"
                >
                  {thenVals.map((v) => <option key={v} value={v}>{v}</option>)}
                </select>
              )}
            </div>
          </div>

          <button
            onClick={handleCreate}
            className="w-full py-2 bg-sky-600 text-white text-sm font-medium rounded-xl hover:bg-sky-700 transition-colors"
          >
            Regel speichern
          </button>
        </div>
      </div>

      {/* Regelanzeige */}
      <div>
        <h3 className="text-sm font-semibold text-slate-700 mb-2">
          {rules.length} Regel{rules.length !== 1 ? "n" : ""}
        </h3>
        {rules.length === 0 ? (
          <p className="text-xs text-slate-400 text-center py-4">Noch keine Regeln angelegt.</p>
        ) : (
          <ul className="space-y-2">
            {rules.map((rule) => {
              const hasConflict = (rule.conflict_with?.length ?? 0) > 0;
              return (
                <li key={rule.id}
                  className={`flex items-start gap-3 px-3 py-2.5 border rounded-xl text-sm ${
                    hasConflict
                      ? "bg-amber-50 border-amber-300"
                      : "bg-white border-slate-200 hover:bg-slate-50"
                  }`}>
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-1.5 flex-wrap">
                      <span className="text-xs font-semibold text-slate-400 uppercase tracking-wide">Wenn</span>
                      <span className="px-2 py-0.5 bg-amber-50 border border-amber-200 text-amber-700 rounded-lg text-xs font-medium truncate max-w-24">
                        {catName(rule.if_category_id)}
                      </span>
                      <span className="text-slate-400">=</span>
                      <span className="px-2 py-0.5 bg-slate-100 rounded-lg text-xs font-mono truncate max-w-24">
                        {rule.if_value}
                      </span>
                    </div>
                    <div className="flex items-center gap-1.5 flex-wrap mt-1">
                      <span className="text-xs font-semibold text-slate-400 uppercase tracking-wide">
                        {rule.type === "exclude" ? "Nicht mit" : "Dann"}
                      </span>
                      <span className="px-2 py-0.5 bg-sky-50 border border-sky-200 text-sky-700 rounded-lg text-xs font-medium truncate max-w-24">
                        {catName(rule.then_category_id)}
                      </span>
                      <span className="text-slate-400">=</span>
                      {rule.then_values_json ? (
                        <span className="px-2 py-0.5 bg-slate-100 rounded-lg text-xs font-mono">
                          {JSON.parse(rule.then_values_json).join(", ")}
                        </span>
                      ) : (
                        <span className="px-2 py-0.5 bg-slate-100 rounded-lg text-xs font-mono truncate max-w-24">
                          {rule.then_value}
                        </span>
                      )}
                    </div>
                    {hasConflict && (
                      <p className="text-xs text-amber-600 mt-1">
                        ⚠️ Regelwiderspruch mit Regel #{rule.conflict_with!.join(", #")}
                      </p>
                    )}
                  </div>
                  <div className="flex items-center gap-2 shrink-0">
                    <span className={"text-xs px-1.5 py-0.5 rounded " + (TYPE_BADGE[rule.type] ?? "bg-slate-100 text-slate-600")}>
                      {rule.type}
                    </span>
                    <button
                      onClick={() => handleDelete(rule.id)}
                      className="text-slate-300 hover:text-red-500 transition-colors text-lg leading-none"
                      title="Regel löschen"
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
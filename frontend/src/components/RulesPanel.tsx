// REQ-1216 + REQ-3003 + REQ-3004: Regeleditor und Regelanzeige in React
// REQ-6005: i18n
import { useEffect, useState, useCallback } from "react";
import { useTranslation } from "react-i18next";
import { rulesApi, categoriesApi, valuesApi } from "../api/client";
import type { Rule } from "../api/client";
import type { Category } from "../types";
import { TriangleAlert } from "lucide-react";

interface Props { projectId: number; }

const TYPE_BADGE: Record<string, string> = {
  exclude:    "bg-theme-danger-soft text-theme-danger border border-theme-danger-border",
  dependency: "bg-theme-accent-soft text-theme-link border border-theme-accent",
  combine:    "bg-theme-success-soft text-theme-success border border-theme-success-border",
};

type RuleWithConflict = Rule & { conflict_with?: number[] };

export default function RulesPanel({ projectId }: Props) {
  const { t } = useTranslation();
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
        const vals = await valuesApi.list(c.id);
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

  const catName = (id: number) => categories.find((c) => c.id === id)?.name ?? t('rulesPanel.categoryFallback', { id });

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
        setMsg({ text: t('rulesPanel.conflictWith', { ids: created.conflict_with.join(", #") }), type: "warn" });
      } else {
        setMsg({ text: t('rulesPanel.saved'), type: "ok" });
      }
      setTimeout(() => setMsg(null), 4000);
    } catch {
      setMsg({ text: t('rulesPanel.saveError'), type: "error" });
    }
  };

  const handleDelete = async (rid: number) => {
    if (!confirm(t("rulesPanel.deleteConfirm"))) return;
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

  if (loading) return <p className="text-theme-text-muted text-sm animate-pulse">{t('rulesPanel.loading')}</p>;
  if (categories.length < 2) return (
    <div className="text-center py-8 text-theme-text-muted">
      <p className="text-sm">{t('rulesPanel.needTwoCategories')}</p>
    </div>
  );

  const ifVals = catValues[form.if_cat] ?? [];
  const thenVals = catValues[form.then_cat] ?? [];

  return (
    <div className="flex flex-col gap-5">
      {/* Regel anlegen – REQ-3003 */}
      <div className="border border-theme-border rounded-2xl p-4 bg-theme-surface-2">
        <h3 className="text-sm font-semibold text-theme-text mb-3">{t('rulesPanel.createTitle')}</h3>

        {msg && (
          <div className={`mb-3 px-3 py-2 rounded-lg text-sm ${
            msg.type === "ok" ? "bg-theme-success-soft border border-theme-success-border text-theme-success" :
            msg.type === "warn" ? "bg-theme-warning-soft border border-theme-warning-border text-theme-warning" :
            "bg-theme-danger-soft border border-theme-danger-border text-theme-danger"
          }`}>
            {msg.type === "warn" && <TriangleAlert className="w-4 h-4 inline-block align-[-3px] mr-1" aria-hidden="true" />}{msg.text}
          </div>
        )}

        <div className="grid grid-cols-1 gap-3">
          {/* Typ */}
          <div>
            <label className="text-xs font-medium text-theme-text-secondary mb-1 block">{t('rulesPanel.typeLabel')}</label>
            <select
              value={form.type}
              onChange={(e) => setForm((f) => ({ ...f, type: e.target.value }))}
              className="w-full px-3 py-1.5 text-sm border border-theme-border rounded-lg focus:outline-none focus:ring-1 focus:ring-theme-accent bg-theme-surface text-theme-text"
            >
              {[
                { val: 'exclude', key: 'rulesPanel.typeLabels.exclude' },
                { val: 'dependency', key: 'rulesPanel.typeLabels.dependency' },
                { val: 'combine', key: 'rulesPanel.typeLabels.combine' },
              ].map(({ val, key }) => (
                <option key={val} value={val}>{t(key)}</option>
              ))}
            </select>
          </div>

          {/* Wenn-Block */}
          <div className="grid grid-cols-2 gap-2">
            <div>
              <label className="text-xs font-medium text-theme-text-secondary mb-1 block">{t('rulesPanel.ifCategoryLabel')}</label>
              <select
                value={form.if_cat}
                onChange={(e) => setForm((f) => ({ ...f, if_cat: Number(e.target.value) }))}
                className="w-full px-3 py-1.5 text-sm border border-theme-border rounded-lg focus:outline-none focus:ring-1 focus:ring-theme-accent bg-theme-surface text-theme-text"
              >
                {categories.map((c) => <option key={c.id} value={c.id}>{c.name}</option>)}
              </select>
            </div>
            <div>
              <label className="text-xs font-medium text-theme-text-secondary mb-1 block">{t('rulesPanel.valueLabel')}</label>
              <select
                value={form.if_val}
                onChange={(e) => setForm((f) => ({ ...f, if_val: e.target.value }))}
                className="w-full px-3 py-1.5 text-sm border border-theme-border rounded-lg focus:outline-none focus:ring-1 focus:ring-theme-accent bg-theme-surface text-theme-text"
              >
                {ifVals.map((v) => <option key={v} value={v}>{v}</option>)}
              </select>
            </div>
          </div>

          {/* Dann-Block */}
          <div className="grid grid-cols-2 gap-2">
            <div>
              <label className="text-xs font-medium text-theme-text-secondary mb-1 block">
                {form.type === "exclude" ? t('rulesPanel.thenCategoryLabelExclude') : t('rulesPanel.thenCategoryLabel')}
              </label>
              <select
                value={form.then_cat}
                onChange={(e) => setForm((f) => ({ ...f, then_cat: Number(e.target.value) }))}
                className="w-full px-3 py-1.5 text-sm border border-theme-border rounded-lg focus:outline-none focus:ring-1 focus:ring-theme-accent bg-theme-surface text-theme-text"
              >
                {categories.map((c) => <option key={c.id} value={c.id}>{c.name}</option>)}
              </select>
            </div>
            <div>
              <label className="text-xs font-medium text-theme-text-secondary mb-1 block">
                {form.type === "combine" ? t('rulesPanel.thenValueLabelCombine') : t('rulesPanel.valueLabel')}
              </label>
              {form.type === "combine" ? (
                <div className="flex flex-wrap gap-1 p-2 border border-theme-border rounded-lg bg-theme-surface min-h-[34px]">
                  {thenVals.map((v) => (
                    <button
                      key={v}
                      type="button"
                      onClick={() => toggleCombineVal(v)}
                      className={`px-2 py-0.5 rounded text-xs transition-colors ${
                        form.then_vals.includes(v)
                          ? "bg-theme-accent text-white"
                          : "bg-theme-surface-2 text-theme-text-secondary hover:bg-theme-surface-hover"
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
                  className="w-full px-3 py-1.5 text-sm border border-theme-border rounded-lg focus:outline-none focus:ring-1 focus:ring-theme-accent bg-theme-surface text-theme-text"
                >
                  {thenVals.map((v) => <option key={v} value={v}>{v}</option>)}
                </select>
              )}
            </div>
          </div>

          <button
            onClick={handleCreate}
            className="w-full py-2 bg-theme-accent text-white text-sm font-medium rounded-xl hover:bg-theme-accent-hover transition-colors"
          >
            {t('rulesPanel.saveBtn')}
          </button>
        </div>
      </div>

      {/* Regelanzeige */}
      <div>
        <h3 className="text-sm font-semibold text-theme-text mb-2">
          {t('rulesPanel.ruleCount', { count: rules.length })}
        </h3>
        {rules.length === 0 ? (
          <p className="text-xs text-theme-text-muted text-center py-4">{t('rulesPanel.noRules')}</p>
        ) : (
          <ul className="space-y-2">
            {rules.map((rule) => {
              const hasConflict = (rule.conflict_with?.length ?? 0) > 0;
              return (
                <li key={rule.id}
                  className={`flex items-start gap-3 px-3 py-2.5 border rounded-xl text-sm text-theme-text ${
                    hasConflict
                      ? "bg-theme-warning-soft border-theme-warning-border"
                      : "bg-theme-surface border-theme-border hover:bg-theme-surface-hover"
                  }`}>
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-1.5 flex-wrap">
                      <span className="text-xs font-semibold text-theme-text uppercase tracking-wide">{t('rulesPanel.ifLabel')}</span>
                      <span className="px-2 py-0.5 bg-theme-warning-soft border border-theme-warning-border text-theme-warning rounded-lg text-xs font-medium truncate max-w-24">
                        {catName(rule.if_category_id)}
                      </span>
                      <span className="text-theme-text">=</span>
                      <span className="px-2 py-0.5 bg-theme-surface-2 rounded-lg text-xs font-mono truncate max-w-24">
                        {rule.if_value}
                      </span>
                    </div>
                    <div className="flex items-center gap-1.5 flex-wrap mt-1">
                      <span className="text-xs font-semibold text-theme-text uppercase tracking-wide">
                        {rule.type === "exclude" ? t('rulesPanel.excludeLabel') : t('rulesPanel.thenLabel')}
                      </span>
                      <span className="px-2 py-0.5 bg-theme-accent-soft border border-theme-accent text-theme-link rounded-lg text-xs font-medium truncate max-w-24">
                        {catName(rule.then_category_id)}
                      </span>
                      <span className="text-theme-text">=</span>
                      {rule.then_values_json ? (
                        <span className="px-2 py-0.5 bg-theme-surface-2 rounded-lg text-xs font-mono">
                          {JSON.parse(rule.then_values_json).join(", ")}
                        </span>
                      ) : (
                        <span className="px-2 py-0.5 bg-theme-surface-2 rounded-lg text-xs font-mono truncate max-w-24">
                          {rule.then_value}
                        </span>
                      )}
                    </div>
                    {hasConflict && (
                      <p className="text-xs text-theme-warning mt-1">
                        {t('rulesPanel.conflictWarning', { ids: rule.conflict_with!.join(", #") })}
                      </p>
                    )}
                  </div>
                  <div className="flex items-center gap-2 shrink-0">
                    <span className={"text-xs px-1.5 py-0.5 rounded " + (TYPE_BADGE[rule.type] ?? "bg-theme-surface-2 text-theme-text-secondary")}>
                      {rule.type}
                    </span>
                    <button
                      onClick={() => handleDelete(rule.id)}
                      className="text-theme-text-muted hover:text-theme-danger transition-colors text-lg leading-none"
                      title={t('rulesPanel.deleteTitle')}
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
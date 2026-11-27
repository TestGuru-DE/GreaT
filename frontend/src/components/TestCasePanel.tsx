// REQ-1208 + REQ-1214 + REQ-2001 + REQ-2004 + REQ-3052 + REQ-4016: Testfall-Generierung mit Office-ähnlicher Tabelle
// REQ-6005 Slice 3: i18n Datums-/Zahlenformate, Export-Spaltenkoepfe
import { useEffect, useRef, useState } from "react";
import { useTranslation } from "react-i18next";
import { rulesApi, seedApi } from "../api/client";
import type { SeedSetList } from "../types";
import { useGenerateStore } from "../store/generateStore";
import { useDecisionTableStore } from "../store/decisionTableStore";
import { useSortableTable } from "../hooks/useSortableTable";
import { useFormattedNumber } from "../hooks/useFormattedNumber";
import type { Strategy } from "../types";
import { Download, Pencil, TriangleAlert } from "lucide-react";

const STRATEGIES: { value: Strategy; label: string }[] = [
  { value: "each", label: "Each Choice (empfohlen)" },
  { value: "linear", label: "Lineare Expansion" },
  { value: "all", label: "All Combinations" },
  { value: "pairwise", label: "Pairwise" },
  { value: "t_wise", label: "T-Wise (parametrisiert)" }, // BUG-3 BLOCKER
  { value: "mcdc", label: "MC/DC (Modified Condition/Decision Coverage)" }, // BUG-3 BLOCKER
  { value: "risk_based", label: "Risikobasiert" },
];

// REQ-6009: Seeds bei Pairwise, T-Wise, Each Choice oder Linear
const SEED_STRATEGIES: Strategy[] = ["each", "linear", "pairwise", "t_wise"];

interface Props { projectId: number; }

export default function TestCasePanel({ projectId }: Props) {
  const { t, i18n } = useTranslation();
  const { formatNumber } = useFormattedNumber({ minimumFractionDigits: 1, maximumFractionDigits: 1 });
  const {
    testcases, count, loading, error, strategy, setStrategy, generate,
    generations, generationsLoading, fetchGenerations, loadGeneration, generationId, renameGeneration,
    riskSummary, // REQ-3051
    resultCategories,
    updateAssignment,
    warnings, // BUG R-05
  } = useGenerateStore();
  // REQ-6009 / BUG K-09: Seed-Satz als Startpunkt der Generierung
  const [seedSets, setSeedSets] = useState<SeedSetList[]>([]);
  const [seedSetId, setSeedSetId] = useState<number | null>(null);
  const seedCapable = SEED_STRATEGIES.includes(strategy);

  const [editingName, setEditingName] = useState<string | null>(null);
  const [applyRules, setApplyRules] = useState(false); // REQ-3005
  const applyRulesTouched = useRef(false);
  const [savingName, setSavingName] = useState(false);
  const [tStrength, setTStrength] = useState(2); // BUG-3: T-Wise Stärke
  const [draftAssignments, setDraftAssignments] = useState<Record<string, string>>({});
  // REQ-3041/REQ-5010: Entscheidungstabellen-Modus sperrt die Generierung in dieser Ansicht
  const dtMode = useDecisionTableStore((s) => s.mode);

  useEffect(() => {
    fetchGenerations(projectId);
  }, [projectId, fetchGenerations]);

  useEffect(() => {
    setSeedSetId(null);
    seedApi.list(projectId).then(setSeedSets).catch(() => setSeedSets([]));
  }, [projectId]);


  useEffect(() => {
    let cancelled = false;
    applyRulesTouched.current = false;
    setApplyRules(false);

    void rulesApi.list(projectId)
      .then((rules) => {
        if (!cancelled && !applyRulesTouched.current) {
          setApplyRules(rules.length > 0);
        }
      })
      .catch(() => {
        if (!cancelled && !applyRulesTouched.current) {
          setApplyRules(false);
        }
      });

    return () => {
      cancelled = true;
    };
  }, [projectId]);

  useEffect(() => {
    setDraftAssignments({});
  }, [generationId, testcases]);

  const rows = testcases.map((tc, i) => ({
    "#": i + 1,
    "Risiko": tc.risk_coverage ?? 0,
    "__testcaseId": tc.id,
    "__testcaseName": tc.name,
    "__hasError": tc.has_error_value ?? false,  // REQ-3063
    "__filled": tc.filled_categories ?? [],  // Restbefund 9c
    ...tc.assignments,
  } as Record<string, unknown>));
  const { sorted, sortCol, sortDir, toggleSort } = useSortableTable(rows);
  const columns = testcases.length > 0 ? Object.keys(testcases[0].assignments) : [];
  const resultCategoryByName = Object.fromEntries(resultCategories.map((category) => [category.name, category]));

  const draftKey = (testcaseId: number, column: string) => `${testcaseId}:${column}`;
  const getDraftValue = (testcaseId: number, column: string, fallback: string) =>
    draftAssignments[draftKey(testcaseId, column)] ?? fallback;

  const resetDraftValue = (testcaseId: number, column: string) => {
    setDraftAssignments((current) => {
      const next = { ...current };
      delete next[draftKey(testcaseId, column)];
      return next;
    });
  };

  const saveDraftValue = async (testcaseId: number, column: string, currentValue: string) => {
    const nextValue = draftAssignments[draftKey(testcaseId, column)];
    if (nextValue === undefined || nextValue === currentValue) {
      return;
    }
    await updateAssignment(testcaseId, column, nextValue);
    resetDraftValue(testcaseId, column);
  };

  const handleExport = (format: "json" | "xlsx" | "csv") => {
    const genId = useGenerateStore.getState().generationId;
    if (!genId) return;
    const lang = i18n.language === "de" ? "de" : "en";
    window.open(`/api/generations/${genId}/export/${format}?lang=${lang}`, "_blank");
  };

  // REQ-3052: Client-seitiger CSV-Export mit i18n Spaltenkoepfen
  const exportTableAsCSV = () => {
    if (testcases.length === 0) return;

    // REQ-6005: Spaltenkoepfe pro Sprache
    const colHeaders = [
      t("export.columns.id"),
      t("export.columns.risk"),
      ...columns,
      t("export.columns.errorValue"),
    ];
    const csvHeader = colHeaders.map(h => `"${h}"`).join(";");

    // Datenzeilen erstellen
    const csvRows = sorted.map((row) => {
      const hasError = row["__hasError"] ?? false;
      const values = [
        String(row["#"] ?? ""),
        formatNumber(Number(row["Risiko"] ?? 0)),
        ...columns.map(col => {
          const val = String(row[col] ?? "-");
          return `"${val.replace(/"/g, '""')}"`;
        }),
        hasError ? t("export.columns.yes") : t("export.columns.no"),
      ];
      return values.join(";");
    });

    // CSV zusammenbauen (mit BOM für Excel)
    const csv = [csvHeader, ...csvRows].join("\r\n");
    const bom = "\uFEFF";
    const blob = new Blob([bom + csv], { type: "text/csv;charset=utf-8;" });

    // Download auslösen
    const url = URL.createObjectURL(blob);
    const link = document.createElement("a");
    link.href = url;
    link.download = `${t("export.columns.fileName")}_${generationId ?? Date.now()}.csv`;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    URL.revokeObjectURL(url);
  };

  const sortIcon = (col: string) => {
    if (sortCol !== col) return <span className="text-theme-text-muted ml-1">↕</span>;
    return <span className="text-theme-link ml-1">{sortDir === "asc" ? "↑" : "↓"}</span>;
  };

  return (
    <div className="flex flex-col h-full gap-3">
      {/* Steuerung – Neu generieren */}
      <div className="flex gap-3 items-end flex-wrap border-b border-theme-border pb-3">
        {dtMode && (
          <p className="w-full text-xs text-theme-warning">
            {t('testCasePanel.dtModeActive')}
          </p>
        )}
        <div>
          <label className="block text-xs text-theme-text-secondary mb-1 font-medium">{t('testCasePanel.strategy')}</label>
          <select value={strategy} onChange={(e) => setStrategy(e.target.value as Strategy)} disabled={dtMode}
            className="px-3 py-1.5 text-sm rounded-lg border border-theme-border focus:outline-none focus:ring-2 focus:ring-theme-accent">
            {STRATEGIES.map((s) => (
              <option key={s.value} value={s.value}>{t(`testCasePanel.strategies.${s.value}`)}</option>
            ))}
          </select>
        </div>
        {/* REQ-3005: Mit Regeln generieren */}
        <label className="flex items-center gap-2 text-sm text-theme-text-secondary cursor-pointer">
          <input
            type="checkbox"
            checked={applyRules}
            onChange={(e) => {
              applyRulesTouched.current = true;
              setApplyRules(e.target.checked);
            }}
            className="rounded border-theme-border text-theme-link focus:ring-theme-accent"
          />
          {t('testCasePanel.applyRules')}
        </label>
        {/* BUG-3: T-Wise Stärke Eingabe */}
        {strategy === "t_wise" && (
          <div>
            <label className="block text-xs text-theme-text-secondary mb-1 font-medium">{t('testCasePanel.tStrength')}</label>
            <input
              type="number"
              min="1"
              max="5"
              value={tStrength}
              onChange={(e) => setTStrength(Number(e.target.value))}
              className="px-3 py-1.5 text-sm w-16 rounded-lg border border-theme-border focus:outline-none focus:ring-2 focus:ring-theme-accent"
            />
          </div>
        )}
        {seedCapable && seedSets.length > 0 && (
          <div>
            <label htmlFor="seed-set-select" className="block text-xs text-theme-text-secondary mb-1 font-medium">{t('seeds.generateWith')}</label>
            <select id="seed-set-select" value={seedSetId ?? ""}
              onChange={(e) => setSeedSetId(e.target.value ? Number(e.target.value) : null)}
              className="px-3 py-1.5 text-sm rounded-lg border border-theme-border focus:outline-none focus:ring-2 focus:ring-theme-accent">
              <option value="">{t('seeds.none')}</option>
              {seedSets.map((s) => (
                <option key={s.id} value={s.id}>{s.name} ({s.seed_count})</option>
              ))}
            </select>
          </div>
        )}
        <button onClick={() => {
          const ts = strategy === "t_wise" ? tStrength : undefined;
          if (seedCapable && seedSetId) generate(projectId, applyRules, ts, seedSetId);
          else generate(projectId, applyRules, ts);
        }} disabled={loading || dtMode}
          className="px-4 py-1.5 bg-theme-accent text-white text-sm rounded-lg hover:bg-theme-accent-hover disabled:opacity-50 font-medium">
          {loading ? t('testCasePanel.generating') : t('testCasePanel.regenerate')}
        </button>

        {/* History-Dropdown – vorherige Generierungen laden */}
        {generations.length > 0 && (
          <div className="ml-2">
            <label className="block text-xs text-theme-text-secondary mb-1 font-medium">
              {t('testCasePanel.loadPrevious')}
            </label>
            <select
              value={generationId ?? ""}
              onChange={(e) => { if (e.target.value) loadGeneration(Number(e.target.value)); }}
              className="px-3 py-1.5 text-sm rounded-lg border border-theme-border focus:outline-none focus:ring-2 focus:ring-theme-accent max-w-xs"
              disabled={generationsLoading}
            >
              <option value="">{t('testCasePanel.chooseGeneration')}</option>
              {generations.map((g) => (
                <option key={g.id} value={g.id}>
                  {g.name}
                </option>
              ))}
            </select>
            {/* REQ-2004: Editierbarer Generierungsname */}
            {generationId && (() => {
              const currentGen = generations.find((g) => g.id === generationId);
              return currentGen ? (
                <div className="flex items-center gap-1 mt-1">
                  {editingName !== null ? (
                    <>
                      <input
                        value={editingName}
                        onChange={(e) => setEditingName(e.target.value)}
                        className="text-xs px-2 py-0.5 border border-theme-accent rounded focus:outline-none"
                        onKeyDown={async (e) => {
                          if (e.key === "Enter" && editingName.trim()) {
                            setSavingName(true);
                            await renameGeneration(generationId, editingName.trim());
                            setSavingName(false);
                            setEditingName(null);
                          } else if (e.key === "Escape") {
                            setEditingName(null);
                          }
                        }}
                        autoFocus
                      />
                      <button
                        disabled={savingName}
                        onClick={async () => {
                          if (editingName.trim()) {
                            setSavingName(true);
                            await renameGeneration(generationId, editingName.trim());
                            setSavingName(false);
                            setEditingName(null);
                          }
                        }}
                        className="text-xs px-2 py-0.5 bg-theme-accent text-white rounded hover:bg-theme-accent-hover"
                      >✓</button>
                      <button onClick={() => setEditingName(null)} className="text-xs px-2 py-0.5 border rounded hover:bg-theme-surface-hover">✗</button>
                    </>
                  ) : (
                    <button
                      onClick={() => setEditingName(currentGen.name)}
                      className="text-xs text-theme-text-muted hover:text-theme-link underline"
                      title={t('testCasePanel.editName')}
                    ><Pencil className="w-3.5 h-3.5 inline-block align-[-2px] mr-1" aria-hidden="true" />{t('testCasePanel.rename')}</button>
                  )}
                </div>
              ) : null;
            })()}
          </div>
        )}

        {testcases.length > 0 && (
          <div className="flex gap-2 ml-auto items-center">
            <span className="text-xs text-theme-text-muted">{t('testCasePanel.count', { count })}</span>
            {/* REQ-3052: Client-seitiger CSV-Export */}
            <button onClick={exportTableAsCSV}
              className="px-3 py-1.5 text-xs bg-theme-success-fill text-white rounded-lg hover:bg-theme-success-fill font-medium"
              title={t('testCasePanel.exportCsvTitle')}>
              <Download className="w-4 h-4" aria-hidden="true" />{t('testCasePanel.exportCsvTable')}
            </button>
            <button onClick={() => handleExport("json")}
              className="px-3 py-1.5 text-xs border border-theme-border rounded-lg hover:bg-theme-surface-hover">
              JSON
            </button>
            <button onClick={() => handleExport("xlsx")}
              className="px-3 py-1.5 text-xs border border-theme-border rounded-lg hover:bg-theme-surface-hover">
              Excel
            </button>
            <button onClick={() => handleExport("csv")}
              className="px-3 py-1.5 text-xs border border-theme-border rounded-lg hover:bg-theme-surface-hover">
              CSV (API)
            </button>
          </div>
        )}
      </div>

      {error && (
        <div className="px-4 py-2 bg-theme-danger-soft border border-theme-danger-border rounded-lg text-theme-danger text-sm">{error}</div>
      )}

      {/* BUG R-05: Hinweise der Generierung (z. B. nicht angewendete Constraints) */}
      {warnings.length > 0 && (
        <ul role="status" data-testid="generation-warnings" className="px-4 py-2 bg-theme-warning-soft border border-theme-warning-border rounded-lg text-theme-warning text-sm list-disc list-inside">
          {warnings.map((w, i) => <li key={i}>{w}</li>)}
        </ul>
      )}

      {/* REQ-3051: Risikoabdeckungs-Badge */}
      {riskSummary && riskSummary.testcase_count > 0 && (
        <div className="flex items-center gap-2">
          <div
            className={`inline-flex items-center gap-2 px-3 py-1.5 rounded-full text-sm font-medium ${
              riskSummary.risk_coverage_percent >= 80
                ? "bg-theme-success-soft text-theme-success border border-theme-success-border"
                : riskSummary.risk_coverage_percent >= 50
                ? "bg-theme-warning-soft text-theme-warning border border-theme-warning-border"
                : "bg-theme-danger-soft text-theme-danger border border-theme-danger-border"
            }`}
            title={t('testCasePanel.riskTitle', { percent: riskSummary.risk_coverage_percent })}
          >
            <span className="text-base">🛡️</span>
            <span>{t('testCasePanel.riskBadge', { percent: riskSummary.risk_coverage_percent })}</span>
          </div>
          <span className="text-xs text-theme-text-muted">
            ({formatNumber(riskSummary.total_risk)} / {formatNumber(riskSummary.max_possible_risk)})
          </span>
        </div>
      )}

      {testcases.length === 0 && !loading ? (
        <div className="flex-1 flex flex-col items-center justify-center text-theme-text-muted border-2 border-dashed border-theme-border rounded-xl">
          <span className="text-3xl mb-2">?</span>
          <p className="text-sm font-medium">{t('testCasePanel.emptyTitle')}</p>
          <p className="text-xs mt-1">
            {generations.length > 0
              ? t('testCasePanel.emptyHintWithHistory')
              : t('testCasePanel.emptyHint')}
          </p>
        </div>
      ) : loading ? (
        <div className="flex-1 flex items-center justify-center text-theme-text-muted text-sm animate-pulse">
          {t('testCasePanel.loading')}
        </div>
      ) : (
        <div className="flex-1 overflow-auto rounded-xl border border-theme-border shadow-sm">
          <table className="w-full text-sm border-collapse">
            {/* REQ-3052: Sticky Header mit Schatten beim Scrollen */}
            <thead className="sticky top-0 z-10 bg-theme-surface-2 shadow-md">
              <tr>
                <th className="px-3 py-2 text-left text-xs font-medium text-theme-text-secondary bg-theme-surface-2 border-b-2 border-theme-border w-12 select-none">
                  #
                </th>
                {/* REQ-3050: Risiko-Spalte */}
                <th
                  onClick={() => toggleSort("Risiko")}
                  className="px-3 py-2 text-left text-xs font-medium text-theme-text-secondary bg-theme-surface-2 border-b-2 border-theme-border cursor-pointer hover:bg-theme-surface-hover select-none whitespace-nowrap w-16"
                  title={t('testCasePanel.riskColumnTitle')}
                >
                  Risiko{sortIcon("Risiko")}
                </th>
                {columns.map((col) => (
                  <th key={col}
                    onClick={() => toggleSort(col)}
                    className="px-3 py-2 text-left text-xs font-medium text-theme-text-secondary bg-theme-surface-2 border-b-2 border-theme-border cursor-pointer hover:bg-theme-surface-hover select-none whitespace-nowrap">
                    {col}{sortIcon(col)}
                  </th>
                ))}
              </tr>
            </thead>
            <tbody>
              {sorted.map((row, i) => {
                const testcaseId = Number(row["__testcaseId"] ?? 0);
                const testcaseName = String(row["__testcaseName"] ?? `TC_${row["#"]}`);
                const tc = testcases.find((testcase) => testcase.id === testcaseId);
                const hasError = tc?.has_error_value ?? false;
                const risk = Number(row["Risiko"] ?? 0);
                return (
                  <tr key={i} className={
                    "border-b border-theme-border hover:bg-theme-accent-soft transition-colors " +
                    (hasError 
                      ? "bg-theme-danger-soft border-l-4 border-l-theme-danger" 
                      : i % 2 === 0 ? "bg-theme-surface" : "bg-theme-surface-2")
                  }>
                    <td className="px-3 py-1.5 text-theme-text-muted text-xs flex items-center gap-1">
                      {String(row["#"] ?? "")}
                      {hasError && <span title={t('testCasePanel.errorCaseTitle')} className="text-theme-danger"><TriangleAlert className="w-4 h-4 inline-block" aria-hidden="true" /></span>}
                    </td>
                    {/* REQ-3050: Risiko-Zelle */}
                    <td className="px-3 py-1.5 text-theme-text font-medium text-xs">{formatNumber(risk)}</td>
                    {columns.map((col) => {
                      const resultCategory = resultCategoryByName[col];
                      const currentValue = String(row[col] ?? "");
                      if (!resultCategory?.editable) {
                        // Restbefund 9c: von der Generierung aufgefuellte Seed-Felder kennzeichnen
                        const filled = (row["__filled"] as string[]).includes(col);
                        return (
                          <td key={col} className={"px-3 py-1.5 text-theme-text" + (filled ? " italic" : "")}
                            title={filled ? t('testCasePanel.filledBySeed') : undefined}
                            data-filled={filled || undefined}>
                            {currentValue || "-"}
                            {filled && <span className="sr-only"> ({t('testCasePanel.filledBySeed')})</span>}
                          </td>
                        );
                      }

                      const draftValue = getDraftValue(testcaseId, col, currentValue);
                      return (
                        <td key={col} className="px-3 py-1.5">
                          <input
                            aria-label={`${testcaseName} – ${col}`}
                            list={`result-options-${resultCategory.id}`}
                            value={draftValue}
                            onChange={(event) =>
                              setDraftAssignments((current) => ({
                                ...current,
                                [draftKey(testcaseId, col)]: event.target.value,
                              }))
                            }
                            onBlur={() => {
                              void saveDraftValue(testcaseId, col, currentValue);
                            }}
                            onKeyDown={(event) => {
                              if (event.key === "Enter") {
                                void saveDraftValue(testcaseId, col, currentValue);
                              } else if (event.key === "Escape") {
                                resetDraftValue(testcaseId, col);
                              }
                            }}
                            placeholder={t('testCasePanel.resultPlaceholder')}
                            className={
                              "w-full min-w-36 rounded border px-2 py-1 text-sm focus:outline-none focus:ring-2 focus:ring-theme-accent " +
                              (draftValue.trim()
                                ? "border-theme-border bg-theme-surface text-theme-text"
                                : "border-theme-warning-border bg-theme-warning-soft text-theme-text-secondary")
                            }
                          />
                          <datalist id={`result-options-${resultCategory.id}`}>
                            {resultCategory.values.map((valueOption) => (
                              <option key={valueOption.id} value={valueOption.value}>
                                {valueOption.value}
                              </option>
                            ))}
                          </datalist>
                        </td>
                      );
                    })}
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
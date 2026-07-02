// REQ-1208 + REQ-1214 + REQ-2001 + REQ-2004 + REQ-3052: Testfall-Generierung mit Office-ähnlicher Tabelle
import { useEffect, useState } from "react";
import { useGenerateStore } from "../store/generateStore";
import { useSortableTable } from "../hooks/useSortableTable";
import type { Strategy } from "../types";

const STRATEGIES: { value: Strategy; label: string }[] = [
  { value: "each", label: "Each Choice (empfohlen)" },
  { value: "linear", label: "Lineare Expansion" },
  { value: "all", label: "All Combinations" },
  { value: "pairwise", label: "Pairwise" },
  { value: "t_wise", label: "T-Wise (parametrisiert)" }, // BUG-3 BLOCKER
  { value: "mcdc", label: "MC/DC (Modified Condition/Decision Coverage)" }, // BUG-3 BLOCKER
  { value: "risk_based", label: "Risikobasiert" },
];

interface Props { projectId: number; }

export default function TestCasePanel({ projectId }: Props) {
  const {
    testcases, count, loading, error, strategy, setStrategy, generate,
    generations, generationsLoading, fetchGenerations, loadGeneration, generationId, renameGeneration,
    riskSummary, // REQ-3051
  } = useGenerateStore();

  const [editingName, setEditingName] = useState<string | null>(null);
  const [applyRules, setApplyRules] = useState(false); // REQ-3005
  const [savingName, setSavingName] = useState(false);
  const [tStrength, setTStrength] = useState(2); // BUG-3: T-Wise Stärke

  useEffect(() => {
    fetchGenerations(projectId);
  }, [projectId, fetchGenerations]);

  const rows = testcases.map((tc, i) => ({
    "#": i + 1,
    "Risiko": tc.risk_coverage ?? 0,
    ...tc.assignments,
  } as Record<string, unknown>));
  const { sorted, sortCol, sortDir, toggleSort } = useSortableTable(rows);
  const columns = testcases.length > 0 ? Object.keys(testcases[0].assignments) : [];

  const handleExport = (format: "json" | "xlsx" | "csv") => {
    const genId = useGenerateStore.getState().generationId;
    if (!genId) return;
    window.open("/api/generations/" + genId + "/export/" + format, "_blank");
  };

  // REQ-3052: Client-seitiger CSV-Export
  const exportTableAsCSV = () => {
    if (testcases.length === 0) return;
    
    // Header-Zeile erstellen
    const headers = ["#", "Risiko", ...columns];
    const csvHeader = headers.map(h => `"${h}"`).join(";");
    
    // Datenzeilen erstellen
    const csvRows = sorted.map((row) => {
      const values = [
        String(row["#"] ?? ""),
        String(Number(row["Risiko"] ?? 0).toFixed(1)),
        ...columns.map(col => {
          const val = String(row[col] ?? "-");
          return `"${val.replace(/"/g, '""')}"`;
        })
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
    link.download = `testfaelle_${generationId ?? Date.now()}.csv`;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    URL.revokeObjectURL(url);
  };

  const sortIcon = (col: string) => {
    if (sortCol !== col) return <span className="text-slate-300 ml-1">↕</span>;
    return <span className="text-sky-600 ml-1">{sortDir === "asc" ? "↑" : "↓"}</span>;
  };

  return (
    <div className="flex flex-col h-full gap-3">
      {/* Steuerung – Neu generieren */}
      <div className="flex gap-3 items-end flex-wrap border-b border-slate-100 pb-3">
        <div>
          <label className="block text-xs text-slate-500 mb-1 font-medium">Strategie</label>
          <select value={strategy} onChange={(e) => setStrategy(e.target.value as Strategy)}
            className="px-3 py-1.5 text-sm rounded-lg border border-slate-200 focus:outline-none focus:ring-2 focus:ring-sky-400">
            {STRATEGIES.map((s) => (
              <option key={s.value} value={s.value}>{s.label}</option>
            ))}
          </select>
        </div>
        {/* REQ-3005: Mit Regeln generieren */}
        <label className="flex items-center gap-2 text-sm text-slate-600 cursor-pointer">
          <input
            type="checkbox"
            checked={applyRules}
            onChange={(e) => setApplyRules(e.target.checked)}
            className="rounded border-slate-300 text-sky-600 focus:ring-sky-400"
          />
          Mit Regeln generieren
        </label>
        {/* BUG-3: T-Wise Stärke Eingabe */}
        {strategy === "t_wise" && (
          <div>
            <label className="block text-xs text-slate-500 mb-1 font-medium">T-Stärke</label>
            <input
              type="number"
              min="1"
              max="5"
              value={tStrength}
              onChange={(e) => setTStrength(Number(e.target.value))}
              className="px-3 py-1.5 text-sm w-16 rounded-lg border border-slate-200 focus:outline-none focus:ring-2 focus:ring-sky-400"
            />
          </div>
        )}
        <button onClick={() => generate(projectId, applyRules, strategy === "t_wise" ? tStrength : undefined)} disabled={loading}
          className="px-4 py-1.5 bg-sky-600 text-white text-sm rounded-lg hover:bg-sky-700 disabled:opacity-50 font-medium">
          {loading ? "Generiere..." : "Neu generieren"}
        </button>

        {/* History-Dropdown – vorherige Generierungen laden */}
        {generations.length > 0 && (
          <div className="ml-2">
            <label className="block text-xs text-slate-500 mb-1 font-medium">
              Vorherige Generierung laden
            </label>
            <select
              value={generationId ?? ""}
              onChange={(e) => { if (e.target.value) loadGeneration(Number(e.target.value)); }}
              className="px-3 py-1.5 text-sm rounded-lg border border-slate-200 focus:outline-none focus:ring-2 focus:ring-sky-400 max-w-xs"
              disabled={generationsLoading}
            >
              <option value="">-- Generierung wählen --</option>
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
                        className="text-xs px-2 py-0.5 border border-sky-400 rounded focus:outline-none"
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
                        className="text-xs px-2 py-0.5 bg-sky-500 text-white rounded hover:bg-sky-600"
                      >✓</button>
                      <button onClick={() => setEditingName(null)} className="text-xs px-2 py-0.5 border rounded hover:bg-slate-50">✗</button>
                    </>
                  ) : (
                    <button
                      onClick={() => setEditingName(currentGen.name)}
                      className="text-xs text-slate-400 hover:text-sky-500 underline"
                      title="Name bearbeiten"
                    >✏️ umbenennen</button>
                  )}
                </div>
              ) : null;
            })()}
          </div>
        )}

        {testcases.length > 0 && (
          <div className="flex gap-2 ml-auto items-center">
            <span className="text-xs text-slate-400">{count} Testfälle</span>
            {/* REQ-3052: Client-seitiger CSV-Export */}
            <button onClick={exportTableAsCSV}
              className="px-3 py-1.5 text-xs bg-green-600 text-white rounded-lg hover:bg-green-700 font-medium"
              title="Aktuelle Tabellen-Ansicht als CSV exportieren (inkl. Sortierung)">
              📥 CSV (Tabelle)
            </button>
            <button onClick={() => handleExport("json")}
              className="px-3 py-1.5 text-xs border border-slate-200 rounded-lg hover:bg-slate-50">
              JSON
            </button>
            <button onClick={() => handleExport("xlsx")}
              className="px-3 py-1.5 text-xs border border-slate-200 rounded-lg hover:bg-slate-50">
              Excel
            </button>
            <button onClick={() => handleExport("csv")}
              className="px-3 py-1.5 text-xs border border-slate-200 rounded-lg hover:bg-slate-50">
              CSV (API)
            </button>
          </div>
        )}
      </div>

      {error && (
        <div className="px-4 py-2 bg-red-50 border border-red-200 rounded-lg text-red-700 text-sm">{error}</div>
      )}

      {/* REQ-3051: Risikoabdeckungs-Badge */}
      {riskSummary && riskSummary.testcase_count > 0 && (
        <div className="flex items-center gap-2">
          <div
            className={`inline-flex items-center gap-2 px-3 py-1.5 rounded-full text-sm font-medium ${
              riskSummary.risk_coverage_percent >= 80
                ? "bg-green-100 text-green-800 border border-green-300"
                : riskSummary.risk_coverage_percent >= 50
                ? "bg-yellow-100 text-yellow-800 border border-yellow-300"
                : "bg-red-100 text-red-800 border border-red-300"
            }`}
            title={`Summe: ${riskSummary.total_risk.toFixed(1)} / Max: ${riskSummary.max_possible_risk.toFixed(1)}`}
          >
            <span className="text-base">🛡️</span>
            <span>Risikoabdeckung: {riskSummary.risk_coverage_percent}%</span>
          </div>
          <span className="text-xs text-slate-400">
            ({riskSummary.total_risk.toFixed(1)} / {riskSummary.max_possible_risk.toFixed(1)})
          </span>
        </div>
      )}

      {testcases.length === 0 && !loading ? (
        <div className="flex-1 flex flex-col items-center justify-center text-slate-400 border-2 border-dashed border-slate-200 rounded-xl">
          <span className="text-3xl mb-2">?</span>
          <p className="text-sm font-medium">Noch keine Testfälle</p>
          <p className="text-xs mt-1">
            {generations.length > 0
              ? "Strategie wählen und neu generieren oder vorherige Generierung laden"
              : "Strategie wählen und auf Generieren klicken"}
          </p>
        </div>
      ) : loading ? (
        <div className="flex-1 flex items-center justify-center text-slate-400 text-sm animate-pulse">
          Lade Testfälle...
        </div>
      ) : (
        <div className="flex-1 overflow-auto rounded-xl border border-slate-200 shadow-sm">
          <table className="w-full text-sm border-collapse">
            {/* REQ-3052: Sticky Header mit Schatten beim Scrollen */}
            <thead className="sticky top-0 z-10 bg-slate-50 shadow-md">
              <tr>
                <th className="px-3 py-2 text-left text-xs font-medium text-slate-500 bg-slate-50 border-b-2 border-slate-200 w-12 select-none">
                  #
                </th>
                {/* REQ-3050: Risiko-Spalte */}
                <th
                  onClick={() => toggleSort("Risiko")}
                  className="px-3 py-2 text-left text-xs font-medium text-slate-500 bg-slate-50 border-b-2 border-slate-200 cursor-pointer hover:bg-slate-100 select-none whitespace-nowrap w-16"
                  title="Risikoabdeckung (Summe der risk_weight-Werte)"
                >
                  Risiko{sortIcon("Risiko")}
                </th>
                {columns.map((col) => (
                  <th key={col}
                    onClick={() => toggleSort(col)}
                    className="px-3 py-2 text-left text-xs font-medium text-slate-500 bg-slate-50 border-b-2 border-slate-200 cursor-pointer hover:bg-slate-100 select-none whitespace-nowrap">
                    {col}{sortIcon(col)}
                  </th>
                ))}
              </tr>
            </thead>
            <tbody>
              {sorted.map((row, i) => {
                // Finde Original-Testcase für _has_error_value
                const tc = testcases.find(t => t.name === (row["name"] ?? `TC_${row["#"]}`));
                const hasError = tc?._has_error_value ?? false;
                const risk = Number(row["Risiko"] ?? 0);
                return (
                  <tr key={i} className={
                    "border-b border-slate-100 hover:bg-sky-50 transition-colors " +
                    (hasError 
                      ? "bg-red-50 border-l-4 border-l-red-500" 
                      : i % 2 === 0 ? "bg-white" : "bg-slate-50/50")
                  }>
                    <td className="px-3 py-1.5 text-slate-400 text-xs">{String(row["#"] ?? "")}</td>
                    {/* REQ-3050: Risiko-Zelle */}
                    <td className="px-3 py-1.5 text-slate-700 font-medium text-xs">{risk.toFixed(1)}</td>
                    {columns.map((col) => (
                      <td key={col} className="px-3 py-1.5 text-slate-700">{String(row[col] ?? "-")}</td>
                    ))}
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
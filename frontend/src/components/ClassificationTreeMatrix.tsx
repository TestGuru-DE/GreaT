// REQ-6006: Testfallmatrix unter Klassifikationsbaum
import { useState, useEffect } from "react";
import { useTranslation } from "react-i18next";
import type { Category, TestCaseOut } from "../types";
import { generateApi } from "../api/client";

interface Props {
  categories: Category[];
  projectId: number;
}

export default function ClassificationTreeMatrix({ categories, projectId }: Props) {
  const { t } = useTranslation();
  const [generations, setGenerations] = useState<{ id: number; name: string }[]>([]);
  const [selectedGenId, setSelectedGenId] = useState<number | undefined>();
  const [testcases, setTestcases] = useState<TestCaseOut[]>([]);
  const [loading, setLoading] = useState(false);

  // Load generations on mount
  useEffect(() => {
    (async () => {
      try {
        const list = await generateApi.listGenerations(projectId);
        setGenerations(list);
        if (list.length > 0 && !selectedGenId) {
          setSelectedGenId(list[0].id);
        }
      } catch (e) {
        console.error("Failed to load generations:", e);
        setGenerations([]);
      }
    })();
  }, [projectId]);

  // Load testcases when generation changes
  useEffect(() => {
    if (!selectedGenId) return;
    (async () => {
      setLoading(true);
      try {
        const resp = await generateApi.getTestcases(selectedGenId);
        // TestcasesResponse has testcases array inside
        setTestcases(resp.testcases ?? []);
      } catch (e) {
        console.error("Failed to load testcases:", e);
        setTestcases([]);
      } finally {
        setLoading(false);
      }
    })();
  }, [selectedGenId]);

  const handleAddTestCase = () => {
    // TODO: Dialog for manual test case creation
    // For now, just show alert
    alert(t("classificationTree.addTestCaseComingSoon", {
      defaultValue: "Manuelle Testfaelle folgen in naechster Version."
    }));
  };

  return (
    <div className="border-t border-slate-200 mt-4">
      <div className="flex items-center gap-3 px-3 py-2 bg-slate-50">
        <label className="text-xs font-medium text-slate-500">
          {t("classificationTree.selectGeneration", { defaultValue: "Generierung:" })}
        </label>
        <select
          value={selectedGenId ?? ""}
          onChange={(e) => setSelectedGenId(Number(e.target.value))}
          className="text-xs border border-slate-300 rounded px-2 py-1 bg-white text-black"
        >
          {generations.map((g) => (
            <option key={g.id} value={g.id}>
              {g.name || `#${g.id}`}
            </option>
          ))}
        </select>
        <button
          onClick={handleAddTestCase}
          className="px-2 py-1 text-xs bg-white border border-slate-300 rounded hover:bg-slate-50"
        >
          + {t("classificationTree.addTestCase", { defaultValue: "Testfall" })}
        </button>
      </div>

      <div className="overflow-x-auto">
        {loading ? (
          <div className="px-3 py-6 text-center text-slate-400 text-xs">
            {t("classificationTree.loading", { defaultValue: "Laden..." })}
          </div>
        ) : (
          <table className="w-full text-xs">
            <thead>
              <tr className="bg-slate-50 border-b border-slate-200">
                <th className="px-2 py-1 text-left font-medium text-slate-500 w-8">#</th>
                {categories.map((cat) => (
                  <th
                    key={cat.id}
                    className="px-2 py-1 text-center font-medium text-slate-600 min-w-[80px]"
                  >
                    {cat.name}
                    {cat.is_result && " ★"}
                  </th>
                ))}
                <th className="px-2 py-1 text-center font-medium text-slate-500 w-16">
                  {t("classificationTree.origin", { defaultValue: "Herkunft" })}
                </th>
              </tr>
            </thead>
            <tbody>
              {testcases.map((tc, idx) => (
                <tr key={tc.id} className="border-b border-slate-100 hover:bg-slate-50">
                  <td className="px-2 py-1 text-slate-400 font-mono">{idx + 1}</td>
                  {categories.map((cat) => {
                    const val = tc.assignments?.[cat.name];
                    return (
                      <td key={cat.id} className="px-2 py-1 text-center text-slate-700">
                        {val ? (
                          <span className="inline-flex items-center justify-center">
                            <span className="w-2 h-2 rounded-full bg-sky-500 mr-1" />
                            {val}
                          </span>
                        ) : (
                          <span className="text-slate-300">–</span>
                        )}
                      </td>
                    );
                  })}
                  <td className="px-2 py-1 text-center text-slate-400">
                    {tc.has_error_value
                      ? t("classificationTree.errorValue", { defaultValue: "Fehlerwert" })
                      : tc.name}
                  </td>
                </tr>
              ))}
              {testcases.length === 0 && (
                <tr>
                  <td
                    colSpan={categories.length + 2}
                    className="px-3 py-6 text-center text-slate-400"
                  >
                    {t("classificationTree.noTestcases", {
                      defaultValue: "Keine Testfaelle. Zuerst generieren.",
                    })}
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        )}
      </div>
    </div>
  );
}
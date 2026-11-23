// REQ-6006: Testfallmatrix unter Klassifikationsbaum
import { useTranslation } from "react-i18next";
import type { Category } from "../types";

interface TestCase {
  id: number;
  generation_id: number;
  assignment?: Record<string, string>;
  origin?: string;
}

interface Props {
  categories: Category[];
  testcases: TestCase[];
  generations: { id: number; name: string }[];
  selectedGenId?: number;
}

export default function ClassificationTreeMatrix({
  categories,
  testcases,
  generations,
}: Props) {
  const { t } = useTranslation();

  return (
    <div className="border-t border-slate-200 mt-4">
      <div className="flex items-center gap-3 px-3 py-2 bg-slate-50">
        <label className="text-xs font-medium text-slate-500">
          {t("classificationTree.selectGeneration", { defaultValue: "Generierung:" })}
        </label>
        <select
          className="text-xs border border-slate-300 rounded px-2 py-1 bg-white text-black"
        >
          {generations.map((g) => (
            <option key={g.id} value={g.id}>
              {g.name}
            </option>
          ))}
        </select>
        <button
          className="px-2 py-1 text-xs bg-white border border-slate-300 rounded hover:bg-slate-50"
        >
          + {t("classificationTree.addTestCase", { defaultValue: "Testfall" })}
        </button>
      </div>

      <div className="overflow-x-auto">
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
                  const val = tc.assignment?.[cat.name];
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
                  {tc.origin === "seed"
                    ? t("classificationTree.seed", { defaultValue: "Seed" })
                    : t("classificationTree.generated", { defaultValue: "ergaenzt" })}
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
      </div>
    </div>
  );
}
// REQ-6013: Aenderungsvorschau-Komponente
import { useTranslation } from "react-i18next";
import type { ModelDiffResult } from "../api/modelApi";

interface Props {
  diff: ModelDiffResult;
}

type DiffCategory = "categories" | "values" | "rules";

const diffConfig: Record<DiffCategory, { labelKey: string; icon: string; colorAdded: string; colorModified: string; colorRemoved: string }> = {
  categories: {
    labelKey: "modelImport.categories",
    icon: "📁",
    colorAdded: "text-theme-success ",
    colorModified: "text-theme-warning ",
    colorRemoved: "text-theme-danger ",
  },
  values: {
    labelKey: "modelImport.values",
    icon: "🏷️",
    colorAdded: "text-theme-success ",
    colorModified: "text-theme-warning ",
    colorRemoved: "text-theme-danger ",
  },
  rules: {
    labelKey: "modelImport.rules",
    icon: "📏",
    colorAdded: "text-theme-success ",
    colorModified: "text-theme-warning ",
    colorRemoved: "text-theme-danger ",
  },
};

function DiffSection({ category, diff }: { category: DiffCategory; diff: ModelDiffResult }) {
  const { t } = useTranslation();
  const config = diffConfig[category];

  const totalAdded = diff.added[category].length;
  const totalModified = diff.modified[category].length;
  const totalRemoved = diff.removed[category].length;
  const hasChanges = totalAdded > 0 || totalModified > 0 || totalRemoved > 0;

  if (!hasChanges) return null;

  return (
    <div className="mb-3">
      <h4 className="text-xs font-semibold text-theme-text-secondary uppercase tracking-wide mb-1 flex items-center gap-1">
        <span>{config.icon}</span>
        <span>{t(config.labelKey)}</span>
      </h4>
      <ul className="space-y-0.5 ml-4">
        {diff.added[category].map((item, i) => (
          <li key={`added-${i}`} className={`text-xs flex items-center gap-1 ${config.colorAdded}`}>
            <span className="font-mono font-bold">+</span>
            <span>{item}</span>
          </li>
        ))}
        {diff.modified[category].map((item, i) => (
          <li key={`modified-${i}`} className={`text-xs flex items-center gap-1 ${config.colorModified}`}>
            <span className="font-mono font-bold">~</span>
            <span>{item}</span>
          </li>
        ))}
        {diff.removed[category].map((item, i) => (
          <li key={`removed-${i}`} className={`text-xs flex items-center gap-1 ${config.colorRemoved}`}>
            <span className="font-mono font-bold">-</span>
            <span>{item}</span>
          </li>
        ))}
      </ul>
    </div>
  );
}

export default function ModelDiffPreview({ diff }: Props) {
  const { t } = useTranslation();

  const totalChanges =
    diff.added.categories.length + diff.added.values.length + diff.added.rules.length +
    diff.modified.categories.length + diff.modified.values.length + diff.modified.rules.length +
    diff.removed.categories.length + diff.removed.values.length + diff.removed.rules.length;

  if (totalChanges === 0) {
    return (
      <p className="text-sm text-theme-text-muted italic">
        {t("modelImport.noChanges")}
      </p>
    );
  }

  return (
    <div className="bg-theme-bg rounded-lg border border-theme-border p-3 max-h-64 overflow-y-auto">
      <p className="text-xs font-semibold text-theme-text mb-2">
        {t("modelImport.previewTitle")}
      </p>
      {(Object.keys(diffConfig) as DiffCategory[]).map((category) => (
        <DiffSection key={category} category={category} diff={diff} />
      ))}
    </div>
  );
}
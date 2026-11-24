// REQ-6006: Klassifikationsbaum Tab (Baum + Matrix + Export)
import { useTranslation } from "react-i18next";
import ClassificationTreeView from "./ClassificationTreeView";
import ClassificationTreeMatrix from "./ClassificationTreeMatrix";
import { useCategoryStore } from "../store/categoryStore";

interface Props {
  projectId: number;
}

export default function ClassificationTreeTab({ projectId }: Props) {
  const { t } = useTranslation();
  const { categories } = useCategoryStore();

  const handleExportSvg = () => {
    const svgEl = document.querySelector("svg[data-tree]");
    if (!svgEl) return;
    const blob = new Blob([svgEl.outerHTML], { type: "image/svg+xml" });
    downloadBlob(blob, `baum-${projectId}.svg`);
  };

  const handleExportPng = () => {
    // TODO: PNG export via canvas
    console.log("PNG export not yet implemented");
  };

  return (
    <div className="flex flex-col h-full">
      {/* Toolbar */}
      <div className="flex items-center gap-2 px-3 py-2 border-b border-slate-200 bg-slate-50">
        <h2 className="text-sm font-semibold text-slate-700">
          {t("classificationTree.title", { defaultValue: "Klassifikationsbaum" })}
        </h2>
        <div className="flex-1" />
        <button
          onClick={handleExportSvg}
          className="px-2 py-1 text-xs bg-white border border-slate-300 rounded hover:bg-slate-50"
        >
          {t("classificationTree.exportSvg", { defaultValue: "SVG" })}
        </button>
        <button
          onClick={handleExportPng}
          className="px-2 py-1 text-xs bg-white border border-slate-300 rounded hover:bg-slate-50"
        >
          {t("classificationTree.exportPng", { defaultValue: "PNG" })}
        </button>
      </div>

      {/* Tree View */}
      <div className="flex-1 overflow-hidden">
        <ClassificationTreeView projectId={projectId} />
      </div>

      {/* Matrix */}
      <ClassificationTreeMatrix
        categories={categories}
        projectId={projectId}
      />
    </div>
  );
}

function downloadBlob(blob: Blob, filename: string) {
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = filename;
  a.click();
  URL.revokeObjectURL(url);
}
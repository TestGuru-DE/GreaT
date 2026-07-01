// REQ-1207 + REQ-1208 + REQ-1215 + REQ-1216 + REQ-3001 + REQ-3009: Projektdetail – zweispaltige Ansicht
import { useEffect, useState } from "react";
import { useParams, useNavigate } from "react-router-dom";
import { useProjectStore } from "../store/projectStore";
import CategoryTree from "../components/CategoryTree";
import TestCasePanel from "../components/TestCasePanel";
import RulesPanel from "../components/RulesPanel";
import GenerationsPanel from "../components/GenerationsPanel";

type RightTab = "generate" | "rules" | "generations";

export default function ProjectDetailPage() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const projectId = Number(id);
  const [rightTab, setRightTab] = useState<RightTab>("generate");

  const { projects, fetchProjects } = useProjectStore();
  useEffect(() => { if (projects.length === 0) fetchProjects(); }, [projects.length, fetchProjects]);
  const project = projects.find((p) => p.id === projectId);
  const projectName = project?.name ?? `#${projectId}`;

  if (!id || isNaN(projectId)) {
    return <div className="p-8 text-red-500">Ungültige Projekt-ID</div>;
  }

  const tabClass = (tab: RightTab) =>
    "px-4 py-2 text-sm font-medium rounded-t-lg mr-1 transition-colors " +
    (rightTab === tab
      ? "bg-sky-50 text-sky-700 border border-slate-200 border-b-white"
      : "text-slate-500 hover:text-slate-700 hover:bg-slate-50");

  return (
    <div className="flex flex-col" style={{ minHeight: "calc(100vh - 56px)" }}>
      {/* Breadcrumb-Header */}
      <header className="bg-white border-b border-slate-200 px-6 py-3 flex items-center gap-4">
        <button onClick={() => navigate("/")}
          className="text-slate-400 hover:text-slate-700 text-sm flex items-center gap-1">
          &larr; Projekte
        </button>
        <h1 className="text-base font-bold text-slate-800">
          G.R.E.A.T. &ndash; Projekt {projectName}
        </h1>
      </header>

      {/* Zweispaltige Ansicht */}
      <div className="flex-1 grid grid-cols-1 lg:grid-cols-[380px_1fr] gap-4 p-4 min-h-0">
        {/* Linke Spalte: Kategorienbaum */}
        <div className="bg-white rounded-2xl border border-slate-200 shadow-sm p-4 overflow-auto">
          <h2 className="text-base font-semibold text-slate-700 mb-3">
            Kategorien &amp; Werte
          </h2>
          <CategoryTree projectId={projectId} />
        </div>

        {/* Rechte Spalte: Tabs */}
        <div className="bg-white rounded-2xl border border-slate-200 shadow-sm flex flex-col min-h-0">
          <div className="flex border-b border-slate-200 px-4 pt-3">
            <button onClick={() => setRightTab("generate")} className={tabClass("generate")}>
              Testfall-Generierung
            </button>
            <button onClick={() => setRightTab("rules")} className={tabClass("rules")}>
              Regeln
            </button>
            <button onClick={() => setRightTab("generations")} className={tabClass("generations")}>
              Generierte Testfälle
            </button>
          </div>

          <div className="flex-1 p-4 flex flex-col min-h-0 overflow-auto">
            {rightTab === "generate" && <TestCasePanel projectId={projectId} />}
            {rightTab === "rules" && <RulesPanel projectId={projectId} />}
            {rightTab === "generations" && <GenerationsPanel projectId={projectId} />}
          </div>
        </div>
      </div>
    </div>
  );
}
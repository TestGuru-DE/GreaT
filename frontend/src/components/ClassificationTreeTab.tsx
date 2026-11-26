// REQ-6006: Klassifikationsbaum-Reiter (Baum, Testfallmatrix, Bearbeiten, Export)
import { useTranslation } from "react-i18next";
import ClassificationTreeView from "./ClassificationTreeView";

interface Props {
  projectId: number;
}

export default function ClassificationTreeTab({ projectId }: Props) {
  const { t } = useTranslation();
  return (
    <div className="flex flex-col h-full min-h-0 min-w-0 w-full gap-2">
      <h2 className="text-sm font-semibold text-theme-text">{t("classificationTree.title")}</h2>
      <ClassificationTreeView projectId={projectId} />
    </div>
  );
}

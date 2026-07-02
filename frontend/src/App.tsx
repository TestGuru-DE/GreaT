// REQ-1204 + REQ-2003 + REQ-3001: Routing + Toast-Container + Top-Navigation
import { Routes, Route } from "react-router-dom";
import ProjectsPage from "./pages/ProjectsPage";
import ProjectDetailPage from "./pages/ProjectDetailPage";
import DataClassesPage from "./pages/DataClassesPage";
import GenerationsPage from "./pages/GenerationsPage";
import SettingsPage from "./pages/SettingsPage";
import TopNav from "./components/TopNav";
import { ToastContainer } from "./components/Toast";

export default function App() {
  return (
    <div className="min-h-screen bg-theme-bg text-theme-text flex flex-col">
      <TopNav />
      <div className="flex-1">
        <Routes>
          <Route path="/" element={<ProjectsPage />} />
          <Route path="/app" element={<ProjectsPage />} />
          <Route path="/app/*" element={<ProjectsPage />} />
          <Route path="/projects/:id" element={<ProjectDetailPage />} />
          <Route path="/dataclasses" element={<DataClassesPage />} />
          <Route path="/generations" element={<GenerationsPage />} />
          <Route path="/settings" element={<SettingsPage />} />
        </Routes>
      </div>
      <ToastContainer />
    </div>
  );
}
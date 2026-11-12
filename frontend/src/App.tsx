// REQ-1204 + REQ-2003 + REQ-3001: Routing + Toast-Container + Top-Navigation
// REQ-3062: System theme sync
import { useEffect, useState } from "react";
import { Routes, Route } from "react-router-dom";
import ProjectsPage from "./pages/ProjectsPage";
import ProjectDetailPage from "./pages/ProjectDetailPage";
import DataClassesPage from "./pages/DataClassesPage";
import GenerationsPage from "./pages/GenerationsPage";
import SettingsPage from "./pages/SettingsPage";
import LoginPage from "./pages/LoginPage";
import ChangePasswordPage from "./pages/ChangePasswordPage";
import HelpPage from "./pages/HelpPage";
import ProtectedRoute from "./components/ProtectedRoute";
import TopNav from "./components/TopNav";
import { ToastContainer } from "./components/Toast";
import { setupSystemThemeSync } from "./lib/theme";

export default function App() {
  const [, setThemeUpdate] = useState(0);

  useEffect(() => {
    // REQ-3062: Listen for OS theme changes
    const cleanup = setupSystemThemeSync(() => {
      setThemeUpdate(prev => prev + 1);
    });
    return cleanup;
  }, []);

  return (
    <div className="min-h-screen bg-theme-bg text-theme-text flex flex-col">
      <TopNav />
      <div className="flex-1">
        <Routes>
          {/* REQ-4001 / REQ-4028: Login ist oeffentlich, alles andere nur mit Anmeldung */}
          <Route path="/login" element={<LoginPage />} />
          <Route element={<ProtectedRoute />}>
            {/* REQ-4028 AK-1: Pflicht-Passwortwechsel (Ziel der Route-Sperre) */}
            <Route path="/account/password" element={<ChangePasswordPage />} />
            <Route path="/" element={<ProjectsPage />} />
            <Route path="/app" element={<ProjectsPage />} />
            <Route path="/app/*" element={<ProjectsPage />} />
            <Route path="/projects/:id" element={<ProjectDetailPage />} />
            <Route path="/dataclasses" element={<DataClassesPage />} />
            <Route path="/generations" element={<GenerationsPage />} />
            <Route path="/settings" element={<SettingsPage />} />
            <Route path="/help" element={<HelpPage />} />
          </Route>
        </Routes>
      </div>
      <ToastContainer />
    </div>
  );
}
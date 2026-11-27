// REQ-3001: Einheitliche Navigation in jeder Ansicht – seit dem Redesign als linke Seitenleiste
// (Suche, Abschnitte, farbige Icon-Kacheln; einklappbar).
// REQ-4028 AK-3: "Passwort aendern" fuer alle Rollen
// REQ-6005: i18n + LanguageSwitcher
import { useEffect, useRef, useState, type ComponentType, type FormEvent } from "react";
import { NavLink, useNavigate } from "react-router-dom";
import { useTranslation } from "react-i18next";
import { useAuthStore } from "../store/authStore";
import {
  CircleHelp, Database, FileCode2, FolderKanban, KeyRound, LayoutGrid, ListChecks, LogOut,
  PanelLeftClose, PanelLeftOpen, Search, Settings,
} from "lucide-react";
import LanguageSwitcher from "./LanguageSwitcher";

type Item = { to: string; key: string; icon: ComponentType<{ className?: string }>; tile: string; end?: boolean };

const WORK_ITEMS: Item[] = [
  { to: "/projects", key: "nav.projects", icon: FolderKanban, tile: "tile-blue", end: true },
  { to: "/generations", key: "nav.generations", icon: ListChecks, tile: "tile-green" },
  { to: "/dataclasses", key: "nav.dataclasses", icon: Database, tile: "tile-violet" },
];

const ACCOUNT_ITEMS: Item[] = [
  { to: "/settings", key: "nav.settings", icon: Settings, tile: "tile-gray" },
  // REQ-4028: "Passwort aendern" fuer alle Rollen (Editor/Viewer haben keinen anderen Weg)
  { to: "/account/password", key: "nav.changePassword", icon: KeyRound, tile: "tile-orange" },
  { to: "/help", key: "nav.help", icon: CircleHelp, tile: "tile-teal" },
];

const COLLAPSE_KEY = "great-sidebar-collapsed";

function readCollapsed(): boolean {
  try {
    const stored = localStorage.getItem(COLLAPSE_KEY);
    if (stored !== null) return stored === "1";
  } catch {
    // Speicher nicht verfuegbar
  }
  // Ohne gespeicherte Wahl: auf schmalen Bildschirmen eingeklappt starten
  return typeof window !== "undefined" && window.innerWidth < 900;
}

const itemClass = (collapsed: boolean) => ({ isActive }: { isActive: boolean }) =>
  "flex items-center gap-3 rounded-lg px-2 py-1.5 text-[0.9375rem] font-medium transition-colors " +
  (collapsed ? "justify-center " : "") +
  (isActive
    ? "bg-theme-surface-hover text-theme-text"
    : "text-theme-text-secondary hover:bg-theme-surface-hover hover:text-theme-text");

export default function TopNav() {
  const { t } = useTranslation();
  const navigate = useNavigate();
  const user = useAuthStore((s) => s.user);
  const logout = useAuthStore((s) => s.logout);
  const [collapsed, setCollapsed] = useState(readCollapsed);
  const [query, setQuery] = useState("");
  const searchRef = useRef<HTMLInputElement>(null);

  // F1 oeffnet die Hilfe, Strg+K springt in die Suche
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === "F1") {
        e.preventDefault();
        navigate("/help");
      } else if ((e.ctrlKey || e.metaKey) && e.key.toLowerCase() === "k") {
        e.preventDefault();
        setCollapsed(false);
        setTimeout(() => searchRef.current?.focus(), 0);
      }
    };
    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, [navigate]);

  const toggleCollapsed = () => {
    setCollapsed((prev) => {
      try {
        localStorage.setItem(COLLAPSE_KEY, prev ? "0" : "1");
      } catch {
        // Speicher nicht verfuegbar – Zustand gilt nur fuer diese Sitzung
      }
      return !prev;
    });
  };

  const handleSearch = (e: FormEvent) => {
    e.preventDefault();
    const q = query.trim();
    navigate(q ? `/projects?q=${encodeURIComponent(q)}` : "/projects");
  };

  const handleLogout = async () => {
    await logout();
    navigate("/login");
  };

  const renderItem = (item: Item) => {
    const Icon = item.icon;
    return (
      <NavLink key={item.to} to={item.to} end={item.end} className={itemClass(collapsed)} title={collapsed ? t(item.key) : undefined}>
        <span className={`icon-tile icon-tile-sm ${item.tile}`} aria-hidden="true"><Icon className="w-3.5 h-3.5" /></span>
        {!collapsed && <span className="truncate">{t(item.key)}</span>}
      </NavLink>
    );
  };

  return (
    // REQ-3045: Theme-Tokens statt fester Farben; das Theme-System setzt "theme-*" auf <html>.
    <header
      className={`bg-theme-sidebar border-r border-theme-border flex flex-col shrink-0 h-screen sticky top-0 ${
        collapsed ? "w-16" : "w-64"
      } transition-[width] duration-200`}
    >
      <div className={`flex items-center gap-2 px-3 pt-4 pb-3 ${collapsed ? "flex-col" : ""}`}>
        <button
          onClick={() => navigate("/")}
          className="flex items-center gap-2 min-w-0 hover:opacity-90"
          title="Startseite"
        >
          <span className="icon-tile tile-blue" aria-hidden="true"><LayoutGrid className="w-4 h-4" /></span>
          {!collapsed && <span className="text-lg font-bold tracking-tight text-theme-text">G.R.E.A.T.</span>}
        </button>
        <button
          onClick={toggleCollapsed}
          className={`btn-ghost btn-icon ${collapsed ? "" : "ml-auto"}`}
          aria-label={t("nav.toggleSidebar")}
          title={t("nav.toggleSidebar")}
        >
          {collapsed ? <PanelLeftOpen className="w-4 h-4" /> : <PanelLeftClose className="w-4 h-4" />}
        </button>
      </div>

      {!collapsed && (
        <form onSubmit={handleSearch} className="px-3 pb-3" role="search">
          <label className="flex items-center gap-2 rounded-lg bg-theme-surface-2 px-2.5 py-1.5">
            <Search className="w-4 h-4 text-theme-text-muted shrink-0" aria-hidden="true" />
            <input
              ref={searchRef}
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              placeholder={t("nav.search")}
              aria-label={t("nav.search")}
              className="!bg-transparent flex-1 min-w-0 text-sm outline-none"
            />
            <kbd className="text-[0.6875rem] font-medium text-theme-text-secondary border border-theme-border rounded px-1.5 py-0.5">
              {t("nav.searchShortcut")}
            </kbd>
          </label>
        </form>
      )}

      <nav className="flex-1 overflow-y-auto px-3 space-y-5 pb-4">
        <div className="space-y-0.5">
          <NavLink to="/" end className={itemClass(collapsed)} title={collapsed ? t("nav.home") : undefined}>
            <span className="icon-tile icon-tile-sm tile-gray" aria-hidden="true"><LayoutGrid className="w-3.5 h-3.5" /></span>
            {!collapsed && <span>{t("nav.home")}</span>}
          </NavLink>
        </div>
        <div className="space-y-0.5">
          {!collapsed && <p className="px-2 pb-1 text-xs font-semibold text-theme-text-secondary">{t("nav.sectionWork")}</p>}
          {WORK_ITEMS.map(renderItem)}
        </div>
        <div className="space-y-0.5">
          {!collapsed && <p className="px-2 pb-1 text-xs font-semibold text-theme-text-secondary">{t("nav.sectionAccount")}</p>}
          {ACCOUNT_ITEMS.map(renderItem)}
          <a
            href="/docs"
            target="_blank"
            rel="noopener noreferrer"
            className={itemClass(collapsed)({ isActive: false })}
            title={collapsed ? t("nav.apiDocs") : undefined}
          >
            <span className="icon-tile icon-tile-sm tile-pink" aria-hidden="true"><FileCode2 className="w-3.5 h-3.5" /></span>
            {!collapsed && <span>{t("nav.apiDocs")}</span>}
          </a>
        </div>
      </nav>

      <div className={`border-t border-theme-border p-3 flex items-center gap-2 ${collapsed ? "flex-col" : ""}`}>
        {/* REQ-6005: LanguageSwitcher */}
        <LanguageSwitcher />
        {user && (
          <button
            onClick={handleLogout}
            className={`btn-ghost text-sm ${collapsed ? "btn-icon" : "ml-auto"}`}
            title={t("nav.logoutTitle", { username: user.username })}
          >
            <LogOut className="w-4 h-4" aria-hidden="true" />
            {!collapsed && <span>{t("nav.logout")}</span>}
          </button>
        )}
      </div>
    </header>
  );
}

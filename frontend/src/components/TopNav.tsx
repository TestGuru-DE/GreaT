// REQ-3001: Einheitliche Top-Navigation in jeder Ansicht
import { NavLink } from "react-router-dom";

const NAV_ITEMS = [
  { to: "/",              label: "Projekte" },
  { to: "/dataclasses",  label: "Datenklassen" },
  { to: "/generations",  label: "Generierungen" },
  { to: "/settings",     label: "Einstellungen" },
];

export default function TopNav() {
  return (
    <header className="bg-white dark:bg-slate-900 border-b border-slate-200 dark:border-slate-700 px-6 py-0 flex items-center gap-1">
      <span className="text-sm font-bold text-sky-700 dark:text-sky-400 mr-4 py-4 shrink-0">G.R.E.A.T.</span>
      <nav className="flex items-center gap-1 flex-1">
        {NAV_ITEMS.map((item) => (
          <NavLink
            key={item.to}
            to={item.to}
            end={item.to === "/"}
            className={({ isActive }) =>
              "px-4 py-4 text-sm border-b-2 transition-colors " +
              (isActive
                ? "border-sky-600 dark:border-sky-400 text-sky-700 dark:text-sky-300 font-semibold"
                : "border-transparent text-slate-500 dark:text-slate-400 hover:text-slate-800 dark:hover:text-slate-200 hover:border-slate-300 dark:hover:border-slate-600")
            }
          >
            {item.label}
          </NavLink>
        ))}
      </nav>
      <a
        href="/docs"
        target="_blank"
        rel="noopener noreferrer"
        className="px-3 py-1 text-xs text-slate-400 dark:text-slate-500 hover:text-sky-600 dark:hover:text-sky-400 border border-slate-200 dark:border-slate-700 rounded-lg ml-2"
      >
        API-Docs
      </a>
    </header>
  );
}
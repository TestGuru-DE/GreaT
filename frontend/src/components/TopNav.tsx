// REQ-3001: Einheitliche Top-Navigation in jeder Ansicht
// REQ-4028 AK-3: "Passwort aendern" fuer alle Rollen
import { NavLink, useNavigate } from "react-router-dom";
import { useAuthStore } from "../store/authStore";

const NAV_ITEMS = [
  { to: "/",              label: "Projekte" },
  { to: "/dataclasses",  label: "Datenklassen" },
  { to: "/generations",  label: "Generierungen" },
  { to: "/settings",     label: "Einstellungen" },
  // REQ-4028: "Passwort aendern" fuer alle Rollen (Editor/Viewer haben keinen anderen Weg)
  { to: "/account/password", label: "Passwort aendern" },
];

export default function TopNav() {
  const navigate = useNavigate();
  const user = useAuthStore((s) => s.user);
  const logout = useAuthStore((s) => s.logout);

  const handleLogout = async () => {
    await logout();
    navigate("/login");
  };

  return (
    // REQ-3045: Theme-Tokens statt hartkodiertem bg-white/dark:-Klassen.
    // Das Theme-System setzt "theme-dark" (nicht "dark") auf <html>, daher greifen
    // Tailwind "dark:"-Varianten hier nie - stattdessen ueber CSS-Custom-Properties themen.
    <header className="bg-theme-surface border-b border-theme-border px-6 py-0 flex items-center gap-1">
      <span className="text-sm font-bold text-theme-accent mr-4 py-4 shrink-0">G.R.E.A.T.</span>
      <nav className="flex items-center gap-1 flex-1">
        {NAV_ITEMS.map((item) => (
          <NavLink
            key={item.to}
            to={item.to}
            end={item.to === "/"}
            className={({ isActive }) =>
              "px-4 py-4 text-sm border-b-2 transition-colors " +
              (isActive
                ? "border-theme-accent text-theme-accent font-semibold"
                : "border-transparent text-theme-text-secondary hover:text-theme-text hover:border-theme-border")
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
        className="px-3 py-1 text-xs text-theme-text-secondary hover:text-theme-accent border border-theme-border rounded-lg ml-2"
      >
        API-Docs
      </a>
      {user && (
        <button
          onClick={handleLogout}
          className="px-3 py-1 text-xs text-theme-text-secondary hover:text-theme-danger border border-theme-border rounded-lg ml-1"
          title={`Abmelden (${user.username})`}
        >
          Logout
        </button>
      )}
    </header>
  );
}
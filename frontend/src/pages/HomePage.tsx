// Startseite mit Apple-Style Kacheln fuer Hauptaktivitaeten
// Erreichbar via: TopNav "Home"-Button oder Klick auf "G.R.E.A.T." Logo
import { useNavigate } from 'react-router-dom';
import {
  FolderOpen,
  Database,
  Play,
  Settings,
  KeyRound,
  Code2,
  ArrowUpRight,
} from 'lucide-react';

interface Tile {
  label: string;
  description: string;
  icon: typeof FolderOpen;
  to: string;
  color: string;
}

const TILES: Tile[] = [
  {
    label: 'Projekte',
    description: 'Testprojekte verwalten und bearbeiten',
    icon: FolderOpen,
    to: '/projects',
    color: 'from-blue-500 to-blue-600',
  },
  {
    label: 'Datenklassen',
    description: 'Aequivalenzklassen und Vorlagen',
    icon: Database,
    to: '/dataclasses',
    color: 'from-emerald-500 to-emerald-600',
  },
  {
    label: 'Generierungen',
    description: 'Testfaelle generieren und exportieren',
    icon: Play,
    to: '/generations',
    color: 'from-violet-500 to-violet-600',
  },
  {
    label: 'Einstellungen',
    description: 'Theme, Limits und Datensicherung',
    icon: Settings,
    to: '/settings',
    color: 'from-amber-500 to-amber-600',
  },
  {
    label: 'Passwort aendern',
    description: 'Sicherheits-einstellungen',
    icon: KeyRound,
    to: '/account/password',
    color: 'from-rose-500 to-rose-600',
  },
  {
    label: 'API-Docs',
    description: 'OpenAPI-Schnittstelle',
    icon: Code2,
    to: '/docs',
    color: 'from-slate-500 to-slate-600',
  },
];

export default function HomePage() {
  const navigate = useNavigate();

  return (
    <div className="min-h-[calc(100vh-80px)] bg-gradient-to-br from-theme-bg to-theme-surface flex flex-col items-center justify-center px-6 py-12">
      {/* Header */}
      <div className="text-center mb-12">
        <h1 className="text-4xl font-bold text-theme-text mb-3 tracking-tight">
          G.R.E.A.T.
        </h1>
        <p className="text-lg text-theme-text-secondary max-w-md mx-auto">
          Georgs Radikal Einfacher Automatisierter TestcaseDesigner
        </p>
      </div>

      {/* Kacheln Grid */}
      <div className="grid grid-cols-2 md:grid-cols-3 gap-5 max-w-3xl w-full">
        {TILES.map((tile) => {
          const Icon = tile.icon;
          const isExternal = tile.to.startsWith('/docs');

          return (
            <button
              key={tile.label}
              onClick={() => {
                if (isExternal) {
                  window.open('http://localhost:8000' + tile.to, '_blank', 'noopener');
                } else {
                  navigate(tile.to);
                }
              }}
              className="group relative flex flex-col items-start text-left p-6 rounded-2xl
                         bg-white/60 dark:bg-white/5 backdrop-blur-xl
                         border border-gray-200/50 dark:border-white/10
                         shadow-lg shadow-black/5 dark:shadow-black/20
                         hover:shadow-xl hover:shadow-black/10 dark:hover:shadow-black/30
                         hover:-translate-y-1 hover:border-gray-300/60 dark:hover:border-white/20
                         transition-all duration-300 ease-out
                         focus:outline-none focus:ring-2 focus:ring-theme-accent/50 focus:ring-offset-2"
            >
              {/* Icon mit Gradient-Hintergrund */}
              <div
                className={`flex items-center justify-center w-12 h-12 rounded-xl
                           bg-gradient-to-br ${tile.color} mb-4
                           shadow-md group-hover:scale-110 transition-transform duration-300`}
              >
                <Icon className="w-6 h-6 text-white" strokeWidth={2} />
              </div>

              {/* Label und Beschreibung */}
              <h3 className="text-base font-semibold text-theme-text mb-1 group-hover:text-theme-accent transition-colors">
                {tile.label}
              </h3>
              <p className="text-xs text-theme-text-secondary leading-snug">
                {tile.description}
              </p>

              {/* Externer-Link Indikator */}
              {isExternal && (
                <ArrowUpRight className="absolute top-4 right-4 w-4 h-4 text-theme-text-secondary/40 group-hover:text-theme-accent/60 transition-colors" />
              )}
            </button>
          );
        })}
      </div>

      {/* Footer */}
      <p className="mt-12 text-xs text-theme-text-secondary/50">
        v1.8.0 &middot; F1 fuer Hilfe
      </p>
    </div>
  );
}
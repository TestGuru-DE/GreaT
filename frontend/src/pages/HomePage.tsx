// Startseite mit Apple-Style Kacheln fuer Hauptaktivitaeten
// Erreichbar via: TopNav "Home"-Button oder Klick auf "G.R.E.A.T." Logo
// REQ-6005: i18n
import { useNavigate } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
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
  labelKey: string;
  descriptionKey: string;
  icon: typeof FolderOpen;
  to: string;
  color: string;
}

const TILES: Tile[] = [
  {
    labelKey: 'home.tiles.projects.label',
    descriptionKey: 'home.tiles.projects.description',
    icon: FolderOpen,
    to: '/projects',
    color: 'tile-blue',
  },
  {
    labelKey: 'home.tiles.dataclasses.label',
    descriptionKey: 'home.tiles.dataclasses.description',
    icon: Database,
    to: '/dataclasses',
    color: 'tile-green',
  },
  {
    labelKey: 'home.tiles.generations.label',
    descriptionKey: 'home.tiles.generations.description',
    icon: Play,
    to: '/generations',
    color: 'tile-violet',
  },
  {
    labelKey: 'home.tiles.settings.label',
    descriptionKey: 'home.tiles.settings.description',
    icon: Settings,
    to: '/settings',
    color: 'tile-orange',
  },
  {
    labelKey: 'home.tiles.changePassword.label',
    descriptionKey: 'home.tiles.changePassword.description',
    icon: KeyRound,
    to: '/account/password',
    color: 'tile-pink',
  },
  {
    labelKey: 'home.tiles.apiDocs.label',
    descriptionKey: 'home.tiles.apiDocs.description',
    icon: Code2,
    to: '/docs',
    color: 'tile-gray',
  },
];

export default function HomePage() {
  const navigate = useNavigate();
  const { t } = useTranslation();

  return (
    <div className="max-w-6xl px-6 md:px-10 py-10">
      {/* Kopf: grosser Titel und Untertitel (Redesign) */}
      <header className="mb-10">
        <h1 className="text-4xl md:text-5xl font-bold text-theme-text tracking-tight mb-3">
          {t('home.title')}
        </h1>
        <p className="text-lg text-theme-text-secondary max-w-2xl">
          {t('home.subtitle')}
        </p>
      </header>

      <h2 className="text-theme-text mb-4">{t('home.sectionTitle')}</h2>
      <div className="grid grid-cols-1 sm:grid-cols-2 xl:grid-cols-3 gap-4">
        {TILES.map((tile) => {
          const Icon = tile.icon;
          const isExternal = tile.to.startsWith('/docs');

          return (
            <button
              key={tile.labelKey}
              onClick={() => {
                if (isExternal) {
                  // API-Doku liegt auf demselben Server wie die Oberflaeche
                  window.open(tile.to, '_blank', 'noopener');
                } else {
                  navigate(tile.to);
                }
              }}
              className="card group relative flex items-start gap-4 text-left p-5 hover:bg-theme-surface-hover hover:border-theme-border-strong transition-colors"
            >
              <span className={`icon-tile icon-tile-lg ${tile.color}`} aria-hidden="true">
                <Icon className="w-6 h-6" strokeWidth={2} />
              </span>
              <span className="min-w-0">
                <span className="block text-lg font-semibold text-theme-text mb-1">{t(tile.labelKey)}</span>
                <span className="block text-sm text-theme-text-secondary leading-snug">{t(tile.descriptionKey)}</span>
              </span>
              {isExternal && (
                <ArrowUpRight className="absolute top-4 right-4 w-4 h-4 text-theme-text-muted" aria-hidden="true" />
              )}
            </button>
          );
        })}
      </div>

      <p className="mt-12 text-xs text-theme-text-muted">
        {t('home.footer', { version: __APP_VERSION__ })}
      </p>
    </div>
  );
}

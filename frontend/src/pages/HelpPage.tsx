// In-App-Hilfe: Rendert das Handbuch als Markdown + INFO-Section
// Erreichbar via: TopNav "?"-Button oder F1-Taste
import { useState, useEffect } from 'react';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import handbookContent from '../docs/handbuch.md?raw';

// Screenshot-Importe (Vite resolved URLs)
import s01 from '../docs/screenshots/01-login.png';
import s02 from '../docs/screenshots/02-passwortwechsel.png';
import s03 from '../docs/screenshots/03-projektuebersicht.png';
import s0301 from '../docs/screenshots/03-01-kategorie-anlegen.png';
import s0304 from '../docs/screenshots/03-04-werte-verwalten.png';
import s0305 from '../docs/screenshots/03-05-fehlerwert.png';
import s0306 from '../docs/screenshots/03-06-default-wert.png';
import s0307 from '../docs/screenshots/03-07-risiko.png';
import s0309 from '../docs/screenshots/03-09-bva.png';
import s0401 from '../docs/screenshots/04-01-uebersicht.png';
import s0403 from '../docs/screenshots/04-03-tabelle.png';
import s0406 from '../docs/screenshots/04-06-constraint-dialog.png';
import s0414 from '../docs/screenshots/04-14-graph.png';
import s0502 from '../docs/screenshots/05-02-forbidden.png';
import s0503 from '../docs/screenshots/05-03-dependency.png';
import s0504 from '../docs/screenshots/05-04-combine.png';
import s0505 from '../docs/screenshots/05-05-visualisierung.png';
import s0901 from '../docs/screenshots/09-01-themes.png';

// Mapping: relativer Pfad aus Markdown -> importierte URL
const SCREENSHOT_MAP: Record<string, string> = {
  './screenshots/01-login.png': s01,
  './screenshots/02-passwortwechsel.png': s02,
  './screenshots/03-projektuebersicht.png': s03,
  './screenshots/03-01-kategorie-anlegen.png': s0301,
  './screenshots/03-04-werte-verwalten.png': s0304,
  './screenshots/03-05-fehlerwert.png': s0305,
  './screenshots/03-06-default-wert.png': s0306,
  './screenshots/03-07-risiko.png': s0307,
  './screenshots/03-09-bva.png': s0309,
  './screenshots/04-01-uebersicht.png': s0401,
  './screenshots/04-03-tabelle.png': s0403,
  './screenshots/04-06-constraint-dialog.png': s0406,
  './screenshots/04-14-graph.png': s0414,
  './screenshots/05-02-forbidden.png': s0502,
  './screenshots/05-03-dependency.png': s0503,
  './screenshots/05-04-combine.png': s0504,
  './screenshots/05-05-visualisierung.png': s0505,
  './screenshots/09-01-themes.png': s0901,
};

// Kapitel-Liste fuer Sidebar-Navigation
const CHAPTERS = [
  { id: 'info', label: 'Info & Lizenz' },
  { id: '1-erste-schritte', label: '1. Erste Schritte' },
  { id: '2-projekte-verwalten', label: '2. Projekte verwalten' },
  { id: '3-kategorien--werte', label: '3. Kategorien & Werte' },
  { id: '4-entscheidungstabelle', label: '4. Entscheidungstabelle' },
  { id: '5-regeln-klassisch', label: '5. Regeln (klassisch)' },
  { id: '6-testfall-generierung', label: '6. Testfall-Generierung' },
  { id: '7-risikoabdeckung', label: '7. Risikoabdeckung' },
  { id: '8-export', label: '8. Export' },
  { id: '9-datenklassen', label: '9. Datenklassen' },
  { id: '10-einstellungen', label: '10. Einstellungen' },
  { id: '11-benutzer--rollen', label: '11. Benutzer & Rollen' },
  { id: '12-tastaturnavigation--shortcuts', label: '12. Tastaturnavigation' },
  { id: '13-glossar', label: '13. Glossar' },
  { id: '14-haeufige-fragen-faq', label: '14. FAQ' },
];

// INFO-Section als Markdown
const INFO_CONTENT = `
## Info & Lizenz

### Lizenz

G.R.E.A.T. wird unter der **MIT-Lizenz** vertrieben. Sie duerfen das Programm frei verwenden, aendern und verteilen, solange der Lizenztext enthalten bleibt.

### Haftungsausschluss

Dieses Programm wird **ohne Garantie** bereitgestellt, weder ausdruecklich noch stillschweigend. Die Entwickler uebernehmen keine Haftung fuer Schaeden, die durch die Nutzung dieses Programms entstehen koennen. Verwenden Sie das Programm auf eigene Verantwortung.

### KI-unterstuetzte Entwicklung

Teile dieses Programms wurden mit Hilfe von **Kuenstlicher Intelligenz (KI)** entwickelt. Dies umfasst:

- Code-Generierung und -Vervollstaendigung
- Testfall-Design und -Generierung
- Dokumentation und Kommentare
- Architektur-Entscheidungen und Reviews

Alle KI-generierten Inhalte wurden von Menschen ueberprueft und freigegeben.

### Projekt auf GitHub

Das vollständige Quellcode-Projekt findest du unter:

**https://github.com/TestGuru-DE/GreaT**

Dort findest du Issue-Tracking, Dokumentation und die Möglichkeit, zum Projekt beizutragen.
`;

export default function HelpPage() {
  const [activeChapter, setActiveChapter] = useState('info');

  // Smooth scrolling zu Ankern
  useEffect(() => {
    const handleClick = (e: MouseEvent) => {
      const target = e.target as HTMLElement;
      if (target.tagName === 'A' && target.getAttribute('href')?.startsWith('#')) {
        e.preventDefault();
        const id = target.getAttribute('href')!.slice(1);
        const element = document.getElementById(id);
        if (element) {
          element.scrollIntoView({ behavior: 'smooth' });
          setActiveChapter(id);
        }
      }
    };

    document.addEventListener('click', handleClick);
    return () => document.removeEventListener('click', handleClick);
  }, []);

  // Setze initial auf Info oder Handbuch je nach aktuellem Kapitel
  const content = activeChapter === 'info' ? INFO_CONTENT : handbookContent;

  return (
    <div className="flex min-h-[calc(100vh-80px)]">
      {/* Sidebar Navigation */}
      <aside className="w-64 flex-shrink-0 bg-theme-surface border-r border-theme-border p-4 overflow-y-auto max-h-[calc(100vh-80px)]">
        <h2 className="text-sm font-bold text-theme-accent mb-3">Inhaltsverzeichnis</h2>
        <nav className="space-y-1">
          {CHAPTERS.map((chapter) => (
            <button
              key={chapter.id}
              onClick={() => setActiveChapter(chapter.id)}
              className={`block w-full text-left text-xs py-1 px-2 rounded transition-colors ${
                activeChapter === chapter.id
                  ? 'bg-theme-accent/20 text-theme-accent font-medium'
                  : 'text-theme-text-secondary hover:text-theme-text hover:bg-theme-surface-hover'
              }`}
            >
              {chapter.label}
            </button>
          ))}
        </nav>
      </aside>

      {/* Hauptinhalt */}
      <main className="flex-1 p-8 overflow-y-auto max-h-[calc(100vh-80px)]">
        <div className="max-w-3xl mx-auto">
          <ReactMarkdown remarkPlugins={[remarkGfm]} components={{
            h1: ({ children }) => <h1 id={extractId(children as string)} className="text-2xl font-bold text-theme-text mb-4 pb-2 border-b border-theme-border">{children}</h1>,
            h2: ({ children }) => <h2 id={extractId(children as string)} className="text-xl font-semibold text-theme-text mt-8 mb-3">{children}</h2>,
            h3: ({ children }) => <h3 id={extractId(children as string)} className="text-lg font-medium text-theme-text mt-6 mb-2">{children}</h3>,
            p: ({ children }) => <p className="text-sm text-theme-text-secondary mb-4 leading-relaxed">{children}</p>,
            ul: ({ children }) => <ul className="list-disc list-inside text-sm text-theme-text-secondary mb-4 space-y-1">{children}</ul>,
            ol: ({ children }) => <ol className="list-decimal list-inside text-sm text-theme-text-secondary mb-4 space-y-1">{children}</ol>,
            li: ({ children }) => <li className="ml-4">{children}</li>,
            table: ({ children }) => <div className="overflow-x-auto my-4"><table className="w-full text-xs border-collapse border border-theme-border">{children}</table></div>,
            thead: ({ children }) => <thead className="bg-theme-surface">{children}</thead>,
            th: ({ children }) => <th className="border border-theme-border px-3 py-2 text-left font-semibold text-theme-text">{children}</th>,
            td: ({ children }) => <td className="border border-theme-border px-3 py-2 text-theme-text-secondary">{children}</td>,
            code: ({ children }) => <code className="bg-theme-surface-hover text-theme-text px-1 py-0.5 rounded text-xs font-mono">{children}</code>,
            pre: ({ children }) => <pre className="bg-theme-surface-hover text-theme-text p-4 rounded my-4 overflow-x-auto text-xs font-mono">{children}</pre>,
            blockquote: ({ children }) => <blockquote className="border-l-4 border-theme-accent pl-4 my-4 text-sm text-theme-text-secondary italic">{children}</blockquote>,
            a: ({ href, children }) => <a href={href} className="text-theme-accent hover:underline">{children}</a>,
            img: ({ src, alt }) => {
              // Mappe relativen Pfad zur importierten URL
              const resolvedSrc = SCREENSHOT_MAP[src as string] || src;
              return <img src={resolvedSrc} alt={alt || ''} className="max-w-full h-auto border border-theme-border rounded my-4" />;
            },
          }}>
            {content}
          </ReactMarkdown>
        </div>
      </main>
    </div>
  );
}

// Helper: Erzeugt eine ID aus dem Heading-Text
function extractId(text: string): string {
  return text
    .toLowerCase()
    .replace(/[^a-z0-9\u00c0-\u017f\s-]/gi, '')
    .replace(/[\s]+/g, '-')
    .replace(/-+$/, '')
    .replace(/[^a-z0-9-]/g, c => {
      // Uebersetze deutsche Sonderzeichen
      const map: Record<string, string> = {
        'a': 'a', 'e': 'e', 'i': 'i', 'o': 'o', 'u': 'u', 's': 'ss',
        'A': 'a', 'E': 'e', 'I': 'i', 'O': 'o', 'U': 'u', 'S': 'ss',
      };
      return map[c] || '';
    });
}
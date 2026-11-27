// In-App-Hilfe: Rendert das Handbuch als Markdown + INFO-Section
// Erreichbar via: TopNav "?"-Button oder F1-Taste
// REQ-6005: i18n for chapter labels and UI elements
import { useState, useEffect, useRef } from 'react';
import { useTranslation } from 'react-i18next';
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
// IDs MUESSEN mit extractId(Heading-Text) uebereinstimmen!
// REQ-6005: i18n keys for chapter labels
const CHAPTER_KEYS = [
  { id: 'info', key: 'help.chapters.info' },
  { id: '1-erste-schritte', key: 'help.chapters.firstSteps' },
  { id: '2-projekte-verwalten', key: 'help.chapters.manageProjects' },
  { id: '3-kategorien-werte', key: 'help.chapters.categoriesValues' },
  { id: '4-entscheidungstabelle', key: 'help.chapters.decisionTable' },
  { id: '5-regeln-klassisch', key: 'help.chapters.rulesClassic' },
  { id: '6-testfall-generierung', key: 'help.chapters.testcaseGeneration' },
  { id: '7-risikoabdeckung', key: 'help.chapters.riskCoverage' },
  { id: '8-export', key: 'help.chapters.export' },
  { id: '9-datenklassen', key: 'help.chapters.dataclasses' },
  { id: '10-einstellungen', key: 'help.chapters.settings' },
  { id: '11-benutzer-rollen', key: 'help.chapters.usersRoles' },
  { id: '12-tastaturnavigation-shortcuts', key: 'help.chapters.keyboardNav' },
  { id: '13-glossar', key: 'help.chapters.glossary' },
  { id: '14-haeufige-fragen-faq', key: 'help.chapters.faq' },
  { id: '15-api-einbindung-fuer-entwickler', key: 'help.chapters.apiIntegration' },
];

// INFO-Section als Markdown (A-14: deutsch und englisch)
const INFO_CONTENT_DE = `
## Info & Lizenz

### Lizenz

G.R.E.A.T. wird unter der **MIT-Lizenz** vertrieben. Du darfst das Programm frei verwenden, ändern und verteilen, solange der Lizenztext enthalten bleibt.

### Haftungsausschluss

Dieses Programm wird **ohne Garantie** bereitgestellt, weder ausdrücklich noch stillschweigend. Die Entwickler übernehmen keine Haftung für Schäden, die durch die Nutzung dieses Programms entstehen können. Die Nutzung erfolgt auf eigene Verantwortung.

### KI-unterstützte Entwicklung

Teile dieses Programms wurden mit Hilfe von **Künstlicher Intelligenz (KI)** entwickelt. Dies umfasst:

- Code-Generierung und -Vervollständigung
- Testfall-Design und -Generierung
- Dokumentation und Kommentare
- Architektur-Entscheidungen und Reviews

Alle KI-generierten Inhalte wurden von Menschen überprüft und freigegeben.

### Projekt auf GitHub

Das vollständige Quellcode-Projekt findest du unter:

**https://github.com/TestGuru-DE/GreaT**

Dort findest du Issue-Tracking, Dokumentation und die Möglichkeit, zum Projekt beizutragen.
`;

const INFO_CONTENT_EN = `
## Info & License

### License

G.R.E.A.T. is distributed under the **MIT License**. You may use, modify and distribute the program freely as long as the license text is retained.

### Disclaimer

This program is provided **without warranty**, either express or implied. The developers accept no liability for damage that may result from using this program. Use it at your own risk.

### AI-assisted development

Parts of this program were developed with the help of **artificial intelligence (AI)**. This includes:

- code generation and completion
- test case design and generation
- documentation and comments
- architecture decisions and reviews

All AI-generated content was reviewed and approved by humans.

### Project on GitHub

You can find the complete source code at:

**https://github.com/TestGuru-DE/GreaT**

There you will find issue tracking, documentation and the opportunity to contribute to the project.
`;

// Helper: Extrahiert Text aus React-Children (kann string | ReactNode[] sein)
function extractText(children: React.ReactNode): string {
  if (typeof children === 'string') return children;
  if (Array.isArray(children)) return children.map(extractText).join('');
  if (children && typeof children === 'object' && 'props' in children) {
    return extractText((children as any).props?.children ?? '');
  }
  return String(children ?? '');
}

// Helper: Erzeugt eine ID aus dem Heading-Text
// Muss mit den IDs in CHAPTER_KEYS uebereinstimmen!
function extractId(children: React.ReactNode): string {
  const text = extractText(children);
  return text
    .toLowerCase()
    // Behalte nur a-z, 0-9, Umlaute (\u00c0-\u017f), Leerzeichen, Bindestriche
    .replace(/[^a-z0-9\u00c0-\u017f\s-]/gi, '')
    // Mehrere Leerzeichen -> ein Bindestrich
    .replace(/[\s]+/g, '-')
    // Fuerende Bindestriche entfernen
    .replace(/-+$/, '')
    // Deutsche Sonderzeichen uebersetzen (nach Leerzeichen->Bindestrich)
    .replace(/[^a-z0-9-]/g, (c: string) => {
      const map: Record<string, string> = {
        '\u00e4': 'a', // ä
        '\u00f6': 'o', // ö
        '\u00fc': 'u', // ü
        '\u00df': 'ss', // ß
        '\u00c4': 'a', // Ä
        '\u00d6': 'o', // Ö
        '\u00dc': 'u', // Ü
      };
      return map[c] || '';
    })
    // Doppelte Bindestriche ausgleichen (z.B. wenn Umlaut zwischen Wörtern war)
    .replace(/-{2,}/g, '-')
    // Restliche Sonderzeichen entfernen (sollte nicht mehr vorkommen)
    .replace(/[^a-z0-9-]/g, '');
}

export default function HelpPage() {
  const { t, i18n } = useTranslation();
  const [activeChapter, setActiveChapter] = useState('info');
  const mainRef = useRef<HTMLDivElement>(null);

  // Scroll to target section when activeChapter changes
  useEffect(() => {
    // Give React time to render the new content
    requestAnimationFrame(() => {
      requestAnimationFrame(() => {
        if (activeChapter === 'info') {
          // Scroll to top for INFO section
          mainRef.current?.scrollTo({ top: 0, behavior: 'smooth' });
        } else {
          // Find the target element by ID and scroll to it
          const target = document.getElementById(activeChapter);
          if (target && mainRef.current) {
            // Scroll within the main container
            const container = mainRef.current;
            const targetTop = target.offsetTop - 20; // small offset for readability
            container.scrollTo({ top: targetTop, behavior: 'smooth' });
          }
        }
      });
    });
  }, [activeChapter]);

  // Handle anchor link clicks within the handbook (TOC links in the markdown)
  useEffect(() => {
    const handleClick = (e: MouseEvent) => {
      const target = e.target as HTMLElement;
      // Walk up to find the <a> element (user might click on text inside <a>)
      const anchor = target.tagName === 'A' ? target : target.closest('a');
      if (anchor && anchor.getAttribute('href')?.startsWith('#')) {
        e.preventDefault();
        const id = anchor.getAttribute('href')!.slice(1);
        const element = document.getElementById(id);
        if (element && mainRef.current) {
          const container = mainRef.current;
          const targetTop = element.offsetTop - 20;
          container.scrollTo({ top: targetTop, behavior: 'smooth' });
          setActiveChapter(id);
        }
      }
    };

    document.addEventListener('click', handleClick);
    return () => document.removeEventListener('click', handleClick);
  }, []);

  // Setze initial auf Info oder Handbuch je nach aktuellem Kapitel
  const content = activeChapter === 'info'
    ? (i18n.language === 'en' ? INFO_CONTENT_EN : INFO_CONTENT_DE)
    : handbookContent;

  return (
    <div className="flex min-h-screen">
      {/* Sidebar Navigation */}
      <aside className="w-64 flex-shrink-0 border-r border-theme-border p-4 overflow-y-auto max-h-screen sticky top-0">
        <h2 className="text-xs font-semibold text-theme-text-secondary px-2 mb-2">{t('help.toc')}</h2>
        <nav className="space-y-1">
          {CHAPTER_KEYS.map((chapter) => (
            <button
              key={chapter.id}
              onClick={() => setActiveChapter(chapter.id)}
              className={`block w-full text-left text-sm py-1.5 px-2 rounded-lg transition-colors ${
                activeChapter === chapter.id
                  ? 'bg-theme-surface-hover text-theme-text font-medium'
                  : 'text-theme-text-secondary hover:text-theme-text hover:bg-theme-surface-hover'
              }`}
            >
              {t(chapter.key)}
            </button>
          ))}
        </nav>
      </aside>

      {/* Hauptinhalt */}
      <main ref={mainRef} className="flex-1 px-10 py-10 overflow-y-auto max-h-screen">
        <div className="max-w-3xl mx-auto">
          <ReactMarkdown remarkPlugins={[remarkGfm]} components={{
            h1: ({ children }) => <h1 id={extractId(children)} className="page-title mb-6">{children}</h1>,
            h2: ({ children }) => <h2 id={extractId(children)} className="text-2xl font-bold text-theme-text mt-10 mb-3">{children}</h2>,
            h3: ({ children }) => <h3 id={extractId(children)} className="text-lg font-medium text-theme-text mt-6 mb-2">{children}</h3>,
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
            a: ({ href, children }) => <a href={href} className="text-theme-link hover:underline">{children}</a>,
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
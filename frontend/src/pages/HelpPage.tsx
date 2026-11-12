// In-App-Hilfe: Rendert das Handbuch als Markdown
// Erreichbar via: TopNav "?"-Button oder F1-Taste
import { useState, useEffect } from 'react';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import handbookContent from '../docs/handbuch.md?raw';

// Kapitel-Liste fuer Sidebar-Navigation
const CHAPTERS = [
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

export default function HelpPage() {
  const [activeChapter, setActiveChapter] = useState('');

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

  return (
    <div className="flex min-h-[calc(100vh-80px)]">
      {/* Sidebar Navigation */}
      <aside className="w-64 flex-shrink-0 bg-theme-surface border-r border-theme-border p-4 overflow-y-auto max-h-[calc(100vh-80px)]">
        <h2 className="text-sm font-bold text-theme-accent mb-3">Inhaltsverzeichnis</h2>
        <nav className="space-y-1">
          {CHAPTERS.map((chapter) => (
            <a
              key={chapter.id}
              href={`#${chapter.id}`}
              className={`block text-xs py-1 px-2 rounded transition-colors ${
                activeChapter === chapter.id
                  ? 'bg-theme-accent/20 text-theme-accent font-medium'
                  : 'text-theme-text-secondary hover:text-theme-text hover:bg-theme-surface-hover'
              }`}
            >
              {chapter.label}
            </a>
          ))}
        </nav>
      </aside>

      {/* Hauptinhalt */}
      <main className="flex-1 p-8 overflow-y-auto max-h-[calc(100vh-80px)]">
        <div className="max-w-3xl mx-auto">
          <ReactMarkdown remarkPlugins={[remarkGfm]} components={{
            // Custom styling fuer Markdown-Elemente
            h1: ({ children }) => <h1 className="text-2xl font-bold text-theme-text mb-4 pb-2 border-b border-theme-border">{children}</h1>,
            h2: ({ children }) => <h2 id={extractId(children as string)} className="text-xl font-semibold text-theme-text mt-8 mb-3">{children}</h2>,
            h3: ({ children }) => <h3 className="text-lg font-medium text-theme-text mt-6 mb-2">{children}</h3>,
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
            img: ({ src, alt }) => <img src={src} alt={alt} className="max-w-full h-auto border border-theme-border rounded my-4" />,
          }}>
            {handbookContent}
          </ReactMarkdown>
        </div>
      </main>
    </div>
  );
}

// Helper: Erzeugt eine ID aus dem Heading-Text (z.B. "1. Erste Schritte" -> "1-erste-schritte")
function extractId(text: string): string {
  return text
    .toLowerCase()
    .replace(/[^\w\s-]/g, '')
    .replace(/\s+/g, '-')
    .replace(/-+$/, '');
}
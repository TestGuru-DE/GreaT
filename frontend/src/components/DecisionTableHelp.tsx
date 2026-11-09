/**
 * REQ-5000: Entscheidungstabelle Hilfe-Dialog
 * Erklaert dem User schrittweise, wie die Entscheidungstabelle funktioniert.
 */
import { useState } from "react";

interface HelpDialogProps {
  onClose: () => void;
}

export default function HelpDialog({ onClose }: HelpDialogProps) {
  const [step, setStep] = useState(0);

  const steps = [
    {
      title: "Schritt 1: Kategorien erstellen",
      icon: "📂",
      content: (
        <div className="space-y-2">
          <p>
            Erstelle mindestens <strong>eine Ursache</strong> und <strong>eine Wirkung</strong>:
          </p>
          <ul className="list-disc pl-5 space-y-1 text-sm">
            <li>
              <span className="text-blue-600 font-medium">Ursache (Condition):</span> Eine
              Bedingung, die eintreten kann (z.B. "Benutzer ist angemeldet")
            </li>
            <li>
              <span className="text-green-600 font-medium">Wirkung (Effect):</span> Eine Aktion oder
              Ergebnis (z.B. "Zugriff gewaehrt")
            </li>
          </ul>
          <div className="bg-amber-50 border border-amber-200 rounded p-2 text-sm text-amber-800">
            ⚠️ Der Button "Entscheidungstabelle" ist erst aktiv, wenn BEIDE Typen existieren!
          </div>
        </div>
      ),
    },
    {
      title: "Schritt 2: Werte zuweisen (optional)",
      icon: "🏷️",
      content: (
        <div className="space-y-2">
          <p>
            Standardmaessig verwendet die Tabelle <strong>Y/N</strong> (Ja/Nein) fuer Ursachen.
          </p>
          <p className="text-sm">
            Du kannst auch eigene Werte fuer Ursachen erstellen (Extended Entry), z.B.:
          </p>
          <ul className="list-disc pl-5 space-y-1 text-sm">
            <li>Größe: S, M, L, XL</li>
            <li>Farbe: Rot, Gruen, Blau</li>
          </ul>
          <p className="text-sm">
            Fuer Wirkungen kannst du den <strong>Text-Modus</strong> aktivieren, um freitextliche
            Werte einzugeben.
          </p>
        </div>
      ),
    },
    {
      title: "Schritt 3: Tabelle generieren",
      icon: "⚡",
      content: (
        <div className="space-y-2">
          <p>Klicke auf den Button <strong>"📋 Entscheidungstabelle"</strong>:</p>
          <ul className="list-disc pl-5 space-y-1 text-sm">
            <li>Erster Klick: Aktiviert den Modus</li>
            <li>Zweiter Klick ("⚡ Generieren"): Erstellt die Tabelle</li>
          </ul>
          <p className="text-sm">
            Die Tabelle zeigt alle moeglichen Kombinationen deiner Ursachen (2^N Regeln).
          </p>
          <div className="bg-blue-50 border border-blue-200 rounded p-2 text-sm text-blue-800">
            💡 Bei 3 Ursachen = 2³ = 8 Regeln. Bei 5 Ursachen = 2⁵ = 32 Regeln.
          </div>
        </div>
      ),
    },
    {
      title: "Schritt 4: Wirkungen ausfuellen",
      icon: "✏️",
      content: (
        <div className="space-y-2">
          <p>Fuer jede Regel trage ein, welche Wirkungen eintreten:</p>
          <ul className="list-disc pl-5 space-y-1 text-sm">
            <li>
              <strong>X</strong> = Diese Wirkung tritt ein
            </li>
            <li>
              <strong>—</strong> = Diese Wirkung tritt nicht ein (Don't Care)
            </li>
            <li>
              <strong>·</strong> = Noch nicht festgelegt
            </li>
          </ul>
          <p className="text-sm">
            Im <strong>Text-Modus</strong> kannst du statt X/— auch freitextliche Werte eingeben.
          </p>
        </div>
      ),
    },
    {
      title: "Schritt 5: Constraints hinzufuegen",
      icon: "🔒",
      content: (
        <div className="space-y-2">
          <p>
            Constraints beschreiben logische Zusammenhaenge zwischen Ursachen oder Wirkungen:
          </p>
          <ul className="list-disc pl-5 space-y-1 text-sm">
            <li>
              <strong>E (Exclusive):</strong> Maximal eine Ursache kann wahr sein
            </li>
            <li>
              <strong>O (One-and-Only-One):</strong> Genau eine Ursache muss wahr sein
            </li>
            <li>
              <strong>I (Inclusive):</strong> Mindestens eine Ursache muss wahr sein
            </li>
            <li>
              <strong>R (Requires):</strong> Wenn Ursache A wahr, dann auch Ursache B
            </li>
            <li>
              <strong>M (Mask):</strong> Wenn Wirkung A aktiv, dann Wirkung B blockiert
            </li>
          </ul>
        </div>
      ),
    },
    {
      title: "Schritt 6: Pruefen und optimieren",
      icon: "🔍",
      content: (
        <div className="space-y-2">
          <p>
            Nutze die Buttons <strong>"📦 Zusammenfassen"</strong> und{" "}
            <strong>"🔍 Pruefen"</strong>:
          </p>
          <ul className="list-disc pl-5 space-y-1 text-sm">
            <li>
              <strong>Zusammenfassen:</strong> Fasst redundante Regeln automatisch zusammen
              (Collapsing)
            </li>
            <li>
              <strong>Pruefen:</strong> Zeigt an, ob die Tabelle vollstaendig ist, ob
              Widersprueche oder Luecken existieren
            </li>
          </ul>
          <div className="bg-green-50 border border-green-200 rounded p-2 text-sm text-green-800">
            ✅ Gruen = Vollstaendig | 🟡 Gelb = Uberschneidungen | 🔴 Rot = Luecken
          </div>
        </div>
      ),
    },
  ];

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black bg-opacity-50">
      <div className="bg-white rounded-lg shadow-xl max-w-lg w-full mx-4 max-h-[85vh] overflow-hidden flex flex-col">
        {/* Header */}
        <div className="flex items-center justify-between p-4 border-b border-slate-200">
          <h2 className="text-lg font-bold text-slate-800">📋 Entscheidungstabelle – Hilfe</h2>
          <button
            onClick={onClose}
            className="text-slate-400 hover:text-slate-600 text-xl"
            aria-label="Schliessen"
          >
            ✕
          </button>
        </div>

        {/* Progress Bar */}
        <div className="w-full bg-slate-100 h-1">
          <div
            className="bg-blue-500 h-1 transition-all duration-300"
            style={{ width: `${((step + 1) / steps.length) * 100}%` }}
          />
        </div>

        {/* Content */}
        <div className="flex-1 overflow-y-auto p-4">
          <div className="flex items-center gap-2 mb-3">
            <span className="text-2xl">{steps[step].icon}</span>
            <h3 className="text-base font-semibold text-slate-700">{steps[step].title}</h3>
          </div>
          <div className="text-sm text-slate-600">{steps[step].content}</div>
        </div>

        {/* Footer */}
        <div className="flex items-center justify-between p-4 border-t border-slate-200">
          <button
            onClick={() => setStep(Math.max(0, step - 1))}
            disabled={step === 0}
            className="px-4 py-2 text-sm text-slate-600 hover:text-slate-800 disabled:opacity-30 disabled:cursor-not-allowed"
          >
            ← Zurueck
          </button>
          <span className="text-xs text-slate-400">
            {step + 1} / {steps.length}
          </span>
          {step < steps.length - 1 ? (
            <button
              onClick={() => setStep(step + 1)}
              className="px-4 py-2 text-sm bg-blue-600 text-white rounded-lg hover:bg-blue-700"
            >
              Weiter →
            </button>
          ) : (
            <button
              onClick={onClose}
              className="px-4 py-2 text-sm bg-green-600 text-white rounded-lg hover:bg-green-700"
            >
              Verstanden ✓
            </button>
          )}
        </div>
      </div>
    </div>
  );
}
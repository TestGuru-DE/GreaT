/**
 * REQ-5000: Entscheidungstabelle Hilfe-Dialog
 * Erklaert dem User schrittweise, wie die Entscheidungstabelle funktioniert.
 * REQ-6005: i18n
 */
import { useState } from "react";
import { useTranslation } from "react-i18next";

interface HelpDialogProps {
  onClose: () => void;
}

export default function HelpDialog({ onClose }: HelpDialogProps) {
  const { t } = useTranslation();
  const [step, setStep] = useState(0);

  const steps = [
    {
      titleKey: "decisionTableHelp.step1.title",
      icon: "📂",
      content: (
        <div className="space-y-2">
          <p dangerouslySetInnerHTML={{ __html: t('decisionTableHelp.step1.content') }} />
          <ul className="list-disc pl-5 space-y-1 text-sm">
            <li>
              <span className="text-blue-600 font-medium">{t('decisionTableHelp.step1.cause')}</span>
            </li>
            <li>
              <span className="text-green-600 font-medium">{t('decisionTableHelp.step1.effect')}</span>
            </li>
          </ul>
          <div className="bg-amber-50 border border-amber-200 rounded p-2 text-sm text-amber-800">
            {t('decisionTableHelp.step1.warning')}
          </div>
        </div>
      ),
    },
    {
      titleKey: "decisionTableHelp.step2.title",
      icon: "🏷️",
      content: (
        <div className="space-y-2">
          <p dangerouslySetInnerHTML={{ __html: t('decisionTableHelp.step2.content') }} />
          <p className="text-sm">
            {t('decisionTableHelp.step2.customValues')}
          </p>
          <ul className="list-disc pl-5 space-y-1 text-sm">
            <li>{t('decisionTableHelpExamples.size')}</li>
            <li>{t('decisionTableHelpExamples.color')}</li>
          </ul>
          <p className="text-sm" dangerouslySetInnerHTML={{ __html: t('decisionTableHelp.step2.textMode') }} />
        </div>
      ),
    },
    {
      titleKey: "decisionTableHelp.step3.title",
      icon: "⚡",
      content: (
        <div className="space-y-2">
          <p dangerouslySetInnerHTML={{ __html: t('decisionTableHelp.step3.content') }} />
          <ul className="list-disc pl-5 space-y-1 text-sm">
            <li>{t('decisionTableHelp.step3.firstClick')}</li>
            <li>{t('decisionTableHelp.step3.secondClick')}</li>
          </ul>
          <p className="text-sm">
            {t('decisionTableHelp.step3.info')}
          </p>
          <div className="bg-blue-50 border border-blue-200 rounded p-2 text-sm text-blue-800">
            {t('decisionTableHelp.step3.tip')}
          </div>
        </div>
      ),
    },
    {
      titleKey: "decisionTableHelp.step4.title",
      icon: "✏️",
      content: (
        <div className="space-y-2">
          <p>{t('decisionTableHelp.step4.content')}</p>
          <ul className="list-disc pl-5 space-y-1 text-sm">
            <li dangerouslySetInnerHTML={{ __html: t('decisionTableHelp.step4.x') }} />
            <li dangerouslySetInnerHTML={{ __html: t('decisionTableHelp.step4.dash') }} />
            <li dangerouslySetInnerHTML={{ __html: t('decisionTableHelp.step4.dot') }} />
          </ul>
          <p className="text-sm" dangerouslySetInnerHTML={{ __html: t('decisionTableHelp.step4.textMode') }} />
        </div>
      ),
    },
    {
      titleKey: "decisionTableHelp.step5.title",
      icon: "🔒",
      content: (
        <div className="space-y-2">
          <p>
            {t('decisionTableHelp.step5.content')}
          </p>
          <ul className="list-disc pl-5 space-y-1 text-sm">
            <li dangerouslySetInnerHTML={{ __html: t('decisionTableHelp.step5.exclusive') }} />
            <li dangerouslySetInnerHTML={{ __html: t('decisionTableHelp.step5.oneOnlyOne') }} />
            <li dangerouslySetInnerHTML={{ __html: t('decisionTableHelp.step5.inclusive') }} />
            <li dangerouslySetInnerHTML={{ __html: t('decisionTableHelp.step5.requires') }} />
            <li dangerouslySetInnerHTML={{ __html: t('decisionTableHelp.step5.mask') }} />
          </ul>
        </div>
      ),
    },
    {
      titleKey: "decisionTableHelp.step6.title",
      icon: "🔍",
      content: (
        <div className="space-y-2">
          <p dangerouslySetInnerHTML={{ __html: t('decisionTableHelp.step6.content') }} />
          <ul className="list-disc pl-5 space-y-1 text-sm">
            <li dangerouslySetInnerHTML={{ __html: t('decisionTableHelp.step6.collapse') }} />
            <li dangerouslySetInnerHTML={{ __html: t('decisionTableHelp.step6.check') }} />
          </ul>
          <div className="bg-green-50 border border-green-200 rounded p-2 text-sm text-green-800">
            {t('decisionTableHelp.step6.legend')}
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
          <h2 className="text-lg font-bold text-slate-800">{t('decisionTableHelp.title')}</h2>
          <button
            onClick={onClose}
            className="text-slate-400 hover:text-slate-600 text-xl"
            aria-label={t('decisionTableHelp.close')}
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
            <h3 className="text-base font-semibold text-slate-700">{t(steps[step].titleKey)}</h3>
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
            {t('decisionTableHelp.back')}
          </button>
          <span className="text-xs text-slate-400">
            {step + 1} / {steps.length}
          </span>
          {step < steps.length - 1 ? (
            <button
              onClick={() => setStep(step + 1)}
              className="px-4 py-2 text-sm bg-blue-600 text-white rounded-lg hover:bg-blue-700"
            >
              {t('decisionTableHelp.next')}
            </button>
          ) : (
            <button
              onClick={onClose}
              className="px-4 py-2 text-sm bg-green-600 text-white rounded-lg hover:bg-green-700"
            >
              {t('decisionTableHelp.done')}
            </button>
          )}
        </div>
      </div>
    </div>
  );
}
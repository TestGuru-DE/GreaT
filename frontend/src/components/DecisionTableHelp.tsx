/**
 * REQ-5000: Entscheidungstabelle Hilfe-Dialog
 * Erklaert dem User schrittweise, wie die Entscheidungstabelle funktioniert.
 * REQ-6005: i18n
 */
import { useState } from "react";
import { useTranslation } from "react-i18next";
import { FolderOpen, Lock, Pencil, Search, Tags, Zap } from "lucide-react";

interface HelpDialogProps {
  onClose: () => void;
}

export default function HelpDialog({ onClose }: HelpDialogProps) {
  const { t } = useTranslation();
  const [step, setStep] = useState(0);

  const steps = [
    {
      titleKey: "decisionTableHelp.step1.title",
      icon: FolderOpen, tile: "tile-blue",
      content: (
        <div className="space-y-2">
          <p dangerouslySetInnerHTML={{ __html: t('decisionTableHelp.step1.content') }} />
          <ul className="list-disc pl-5 space-y-1 text-sm">
            <li>
              <span className="text-theme-link font-medium">{t('decisionTableHelp.step1.cause')}</span>
            </li>
            <li>
              <span className="text-theme-success font-medium">{t('decisionTableHelp.step1.effect')}</span>
            </li>
          </ul>
          <div className="bg-theme-warning-soft border border-theme-warning-border rounded p-2 text-sm text-theme-warning">
            {t('decisionTableHelp.step1.warning')}
          </div>
        </div>
      ),
    },
    {
      titleKey: "decisionTableHelp.step2.title",
      icon: Tags, tile: "tile-violet",
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
      icon: Zap, tile: "tile-orange",
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
          <div className="bg-theme-accent-soft border border-theme-accent rounded p-2 text-sm text-theme-link">
            {t('decisionTableHelp.step3.tip')}
          </div>
        </div>
      ),
    },
    {
      titleKey: "decisionTableHelp.step4.title",
      icon: Pencil, tile: "tile-green",
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
      icon: Lock, tile: "tile-gray",
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
      icon: Search, tile: "tile-teal",
      content: (
        <div className="space-y-2">
          <p dangerouslySetInnerHTML={{ __html: t('decisionTableHelp.step6.content') }} />
          <ul className="list-disc pl-5 space-y-1 text-sm">
            <li dangerouslySetInnerHTML={{ __html: t('decisionTableHelp.step6.collapse') }} />
            <li dangerouslySetInnerHTML={{ __html: t('decisionTableHelp.step6.check') }} />
          </ul>
          <div className="bg-theme-success-soft border border-theme-success-border rounded p-2 text-sm text-theme-success">
            {t('decisionTableHelp.step6.legend')}
          </div>
        </div>
      ),
    },
  ];

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black bg-opacity-50">
      <div className="bg-theme-surface rounded-lg shadow-xl max-w-lg w-full mx-4 max-h-[85vh] overflow-hidden flex flex-col">
        {/* Header */}
        <div className="flex items-center justify-between p-4 border-b border-theme-border">
          <h2 className="text-lg font-bold text-theme-text">{t('decisionTableHelp.title')}</h2>
          <button
            onClick={onClose}
            className="text-theme-text-muted hover:text-theme-text-secondary text-xl"
            aria-label={t('decisionTableHelp.close')}
          >
            ✕
          </button>
        </div>

        {/* Progress Bar */}
        <div className="w-full bg-theme-surface-2 h-1">
          <div
            className="bg-theme-accent h-1 transition-all duration-300"
            style={{ width: `${((step + 1) / steps.length) * 100}%` }}
          />
        </div>

        {/* Content */}
        <div className="flex-1 overflow-y-auto p-4">
          <div className="flex items-center gap-2 mb-3">
            {(() => { const StepIcon = steps[step].icon; return (
              <span className={`icon-tile icon-tile-lg ${steps[step].tile}`} aria-hidden="true"><StepIcon className="w-6 h-6" /></span>
            ); })()}
            <h3 className="text-base font-semibold text-theme-text">{t(steps[step].titleKey)}</h3>
          </div>
          <div className="text-sm text-theme-text-secondary">{steps[step].content}</div>
        </div>

        {/* Footer */}
        <div className="flex items-center justify-between p-4 border-t border-theme-border">
          <button
            onClick={() => setStep(Math.max(0, step - 1))}
            disabled={step === 0}
            className="px-4 py-2 text-sm text-theme-text-secondary hover:text-theme-text disabled:opacity-30 disabled:cursor-not-allowed"
          >
            {t('decisionTableHelp.back')}
          </button>
          <span className="text-xs text-theme-text-muted">
            {step + 1} / {steps.length}
          </span>
          {step < steps.length - 1 ? (
            <button
              onClick={() => setStep(step + 1)}
              className="px-4 py-2 text-sm bg-theme-accent text-white rounded-lg hover:bg-theme-accent-hover"
            >
              {t('decisionTableHelp.next')}
            </button>
          ) : (
            <button
              onClick={onClose}
              className="px-4 py-2 text-sm bg-theme-success-fill text-white rounded-lg hover:bg-theme-success-fill"
            >
              {t('decisionTableHelp.done')}
            </button>
          )}
        </div>
      </div>
    </div>
  );
}
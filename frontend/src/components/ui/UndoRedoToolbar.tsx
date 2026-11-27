// REQ-3053: Undo/Redo Toolbar-Komponente
// REQ-6005: i18n
import { useEffect } from 'react'
import { useTranslation } from 'react-i18next'

interface UndoRedoToolbarProps {
  canUndo: boolean
  canRedo: boolean
  onUndo: () => void
  onRedo: () => void
}

export default function UndoRedoToolbar({ canUndo, canRedo, onUndo, onRedo }: UndoRedoToolbarProps) {
  const { t } = useTranslation();
  // Keyboard-Shortcuts (Strg+Z / Strg+Y)
  useEffect(() => {
    function handleKey(e: KeyboardEvent) {
      if (e.ctrlKey && e.key === 'z' && !e.shiftKey && canUndo) {
        e.preventDefault()
        onUndo()
      }
      if (e.ctrlKey && (e.key === 'y' || (e.key === 'z' && e.shiftKey)) && canRedo) {
        e.preventDefault()
        onRedo()
      }
    }
    window.addEventListener('keydown', handleKey)
    return () => window.removeEventListener('keydown', handleKey)
  }, [onUndo, onRedo, canUndo, canRedo])

  return (
    <div className="flex gap-1 mb-3 pb-2 border-b border-theme-border">
      <button
        onClick={onUndo}
        disabled={!canUndo}
        title={t('undoRedo.undoTitle')}
        className="px-2 py-1 text-xs rounded border border-theme-border disabled:opacity-40 disabled:cursor-not-allowed hover:bg-theme-surface-hover hover:border-theme-border transition-colors"
      >
        ↩ {t('undoRedo.undo')}
      </button>
      <button
        onClick={onRedo}
        disabled={!canRedo}
        title={t('undoRedo.redoTitle')}
        className="px-2 py-1 text-xs rounded border border-theme-border disabled:opacity-40 disabled:cursor-not-allowed hover:bg-theme-surface-hover hover:border-theme-border transition-colors"
      >
        ↪ {t('undoRedo.redo')}
      </button>
    </div>
  )
}
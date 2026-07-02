// REQ-3053: Undo/Redo Toolbar-Komponente
import { useEffect } from 'react'

interface UndoRedoToolbarProps {
  canUndo: boolean
  canRedo: boolean
  onUndo: () => void
  onRedo: () => void
}

export default function UndoRedoToolbar({ canUndo, canRedo, onUndo, onRedo }: UndoRedoToolbarProps) {
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
    <div className="flex gap-1 mb-3 pb-2 border-b border-slate-100">
      <button
        onClick={onUndo}
        disabled={!canUndo}
        title="Rückgängig (Strg+Z)"
        className="px-2 py-1 text-xs rounded border border-slate-200 disabled:opacity-40 disabled:cursor-not-allowed hover:bg-slate-50 hover:border-slate-300 transition-colors"
      >
        ↩ Rückgängig
      </button>
      <button
        onClick={onRedo}
        disabled={!canRedo}
        title="Wiederholen (Strg+Y)"
        className="px-2 py-1 text-xs rounded border border-slate-200 disabled:opacity-40 disabled:cursor-not-allowed hover:bg-slate-50 hover:border-slate-300 transition-colors"
      >
        ↪ Wiederholen
      </button>
    </div>
  )
}

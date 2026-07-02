// REQ-3053: Undo/Redo Hook für Testfall-Konfiguration
import { useState, useCallback } from 'react'

interface UndoRedoState<T> {
  past: T[]
  present: T
  future: T[]
}

export function useUndoRedo<T>(initialState: T) {
  const [state, setState] = useState<UndoRedoState<T>>({
    past: [],
    present: initialState,
    future: [],
  })

  const canUndo = state.past.length > 0
  const canRedo = state.future.length > 0

  const set = useCallback((newPresent: T | ((prev: T) => T)) => {
    setState(s => {
      const next = typeof newPresent === 'function'
        ? (newPresent as (prev: T) => T)(s.present)
        : newPresent
      return {
        past: [...s.past.slice(-49), s.present], // max 50 Schritte
        present: next,
        future: [],
      }
    })
  }, [])

  const undo = useCallback(() => {
    setState(s => {
      if (s.past.length === 0) return s
      const previous = s.past[s.past.length - 1]
      return {
        past: s.past.slice(0, -1),
        present: previous,
        future: [s.present, ...s.future],
      }
    })
  }, [])

  const redo = useCallback(() => {
    setState(s => {
      if (s.future.length === 0) return s
      const next = s.future[0]
      return {
        past: [...s.past, s.present],
        present: next,
        future: s.future.slice(1),
      }
    })
  }, [])

  const reset = useCallback((newPresent: T) => {
    setState({
      past: [],
      present: newPresent,
      future: [],
    })
  }, [])

  return { state: state.present, set, undo, redo, reset, canUndo, canRedo }
}

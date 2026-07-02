// REQ-3053: Tests für useUndoRedo Hook
import { renderHook, act } from '@testing-library/react'
import { useUndoRedo } from '../useUndoRedo'

test('initial state', () => {
  const { result } = renderHook(() => useUndoRedo('a'))
  expect(result.current.state).toBe('a')
  expect(result.current.canUndo).toBe(false)
  expect(result.current.canRedo).toBe(false)
})

test('set + undo + redo', () => {
  const { result } = renderHook(() => useUndoRedo('a'))
  act(() => result.current.set('b'))
  expect(result.current.state).toBe('b')
  expect(result.current.canUndo).toBe(true)
  act(() => result.current.undo())
  expect(result.current.state).toBe('a')
  expect(result.current.canRedo).toBe(true)
  act(() => result.current.redo())
  expect(result.current.state).toBe('b')
})

test('undo clears future on new set', () => {
  const { result } = renderHook(() => useUndoRedo('a'))
  act(() => result.current.set('b'))
  act(() => result.current.undo())
  act(() => result.current.set('c'))
  expect(result.current.canRedo).toBe(false)
  expect(result.current.state).toBe('c')
})

test('functional update', () => {
  const { result } = renderHook(() => useUndoRedo(5))
  act(() => result.current.set(prev => prev + 1))
  expect(result.current.state).toBe(6)
})

test('max 50 steps history', () => {
  const { result } = renderHook(() => useUndoRedo(0))
  for (let i = 1; i <= 60; i++) {
    act(() => result.current.set(i))
  }
  let undoCount = 0
  while (result.current.canUndo) {
    act(() => result.current.undo())
    undoCount++
  }
  expect(undoCount).toBe(50) // maximal 50 Schritte zurück
  expect(result.current.state).toBe(10) // 60 - 50 = 10
})

test('reset clears history', () => {
  const { result } = renderHook(() => useUndoRedo('a'))
  act(() => result.current.set('b'))
  act(() => result.current.set('c'))
  act(() => result.current.reset('x'))
  expect(result.current.state).toBe('x')
  expect(result.current.canUndo).toBe(false)
  expect(result.current.canRedo).toBe(false)
})

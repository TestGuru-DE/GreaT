// REQ-3053: Test für CategoryStore Undo/Redo Integration
import { renderHook, act } from '@testing-library/react'
import { useCategoryStore } from '../categoryStore'
import { categoriesApi, valuesApi } from '../../api/client'

// Mock API
vi.mock('../../api/client', () => ({
  categoriesApi: {
    list: vi.fn(),
    create: vi.fn(),
    delete: vi.fn(),
  },
  valuesApi: {
    list: vi.fn(),
    create: vi.fn(),
    delete: vi.fn(),
  },
  generateApi: {},
  renameApi: {},
  reorderApi: {},
}))

describe('CategoryStore Undo/Redo', () => {
  beforeEach(async () => {
    // Reset store
    vi.mocked(categoriesApi.list).mockResolvedValue([])
    const { result } = renderHook(() => useCategoryStore())
    await act(async () => {
      await result.current.fetchCategories(1)
    })
  })

  test('initial state has no undo/redo', () => {
    const { result } = renderHook(() => useCategoryStore())
    expect(result.current.canUndo).toBe(false)
    expect(result.current.canRedo).toBe(false)
  })

  test('createCategory enables undo', async () => {
    const mockCat = { id: 99, name: 'Test', order_index: 0 }
    vi.mocked(categoriesApi.create).mockResolvedValue(mockCat)

    const { result } = renderHook(() => useCategoryStore())
    const initialLength = result.current.categories.length
    
    await act(async () => {
      await result.current.createCategory(1, 'Test')
    })

    expect(result.current.canUndo).toBe(true)
    expect(result.current.categories.length).toBe(initialLength + 1)
  })

  test('undo + redo work correctly', async () => {
    const mockCat = { id: 100, name: 'TestUndo', order_index: 0 }
    vi.mocked(categoriesApi.create).mockResolvedValue(mockCat)

    const { result } = renderHook(() => useCategoryStore())
    const initialLength = result.current.categories.length
    
    await act(async () => {
      await result.current.createCategory(1, 'TestUndo')
    })

    const afterAddLength = result.current.categories.length
    expect(afterAddLength).toBe(initialLength + 1)

    act(() => {
      result.current.undo()
    })

    expect(result.current.categories.length).toBe(initialLength)
    expect(result.current.canRedo).toBe(true)

    act(() => {
      result.current.redo()
    })

    expect(result.current.categories.length).toBe(afterAddLength)
  })

  test('fetchCategories resets history', async () => {
    const mockCat = { id: 102, name: 'TestFetch', order_index: 0 }
    vi.mocked(categoriesApi.create).mockResolvedValue(mockCat)
    vi.mocked(categoriesApi.list).mockResolvedValue([])

    const { result } = renderHook(() => useCategoryStore())
    
    await act(async () => {
      await result.current.createCategory(1, 'TestFetch')
    })

    expect(result.current.canUndo).toBe(true)

    await act(async () => {
      await result.current.fetchCategories(1)
    })

    expect(result.current.canUndo).toBe(false)
    expect(result.current.canRedo).toBe(false)
  })
})

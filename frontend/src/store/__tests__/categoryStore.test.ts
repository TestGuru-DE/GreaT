// REQ-3053 / BUG C-18: Undo/Redo des Kategorie-Stores wirkt auf dem Server
import { renderHook, act } from '@testing-library/react'
import { useCategoryStore } from '../categoryStore'
import { categoriesApi, valuesApi, renameApi, reorderApi } from '../../api/client'

vi.mock('../../api/client', () => ({
  categoriesApi: {
    list: vi.fn(),
    create: vi.fn(),
    delete: vi.fn(),
    updateProperties: vi.fn(),
    setDefault: vi.fn(),
    unsetDefault: vi.fn(),
  },
  valuesApi: {
    list: vi.fn(),
    create: vi.fn(),
    delete: vi.fn(),
    reorder: vi.fn(),
  },
  renameApi: { category: vi.fn(), value: vi.fn() },
  reorderApi: { categories: vi.fn() },
  generateApi: {},
}))

const cat = (id: number, name: string) => ({ id, name, order_index: 0, category_type: 'standard', is_result: false })

describe('CategoryStore Undo/Redo (serverseitig)', () => {
  beforeEach(async () => {
    vi.clearAllMocks()
    vi.mocked(categoriesApi.list).mockResolvedValue([])
    vi.mocked(valuesApi.list).mockResolvedValue([])
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
    vi.mocked(categoriesApi.create).mockResolvedValue(cat(99, 'Test') as never)
    const { result } = renderHook(() => useCategoryStore())
    await act(async () => {
      await result.current.createCategory(1, 'Test')
    })
    expect(result.current.canUndo).toBe(true)
    expect(result.current.categories.map((c) => c.id)).toEqual([99])
  })

  test('Undo eines Anlegens loescht auf dem Server, Redo legt neu an (C-18)', async () => {
    vi.mocked(categoriesApi.create)
      .mockResolvedValueOnce(cat(100, 'Neu') as never)
      .mockResolvedValueOnce(cat(101, 'Neu') as never)
    const { result } = renderHook(() => useCategoryStore())
    await act(async () => {
      await result.current.createCategory(1, 'Neu')
    })

    vi.mocked(categoriesApi.list).mockResolvedValueOnce([])
    await act(async () => {
      await result.current.undo()
    })
    expect(categoriesApi.delete).toHaveBeenCalledWith(100, true)
    expect(result.current.categories).toEqual([])
    expect(result.current.canRedo).toBe(true)

    vi.mocked(categoriesApi.list).mockResolvedValueOnce([cat(101, 'Neu')] as never)
    await act(async () => {
      await result.current.redo()
    })
    expect(categoriesApi.create).toHaveBeenCalledTimes(2)
    expect(result.current.categories.map((c) => c.id)).toEqual([101])

    // erneutes Undo nutzt die neue ID (Ref wurde nachgefuehrt)
    await act(async () => {
      await result.current.undo()
    })
    expect(categoriesApi.delete).toHaveBeenLastCalledWith(101, true)
  })

  test('Undo einer Loeschung stellt Kategorie mit Werten und Reihenfolge wieder her', async () => {
    vi.mocked(categoriesApi.list).mockResolvedValue([cat(1, 'A'), cat(2, 'B')] as never)
    vi.mocked(valuesApi.list).mockResolvedValue([
      { id: 10, value: 'a1', risk_weight: 2, vtype: 'string', allowed: false, is_default: true },
    ] as never)
    const { result } = renderHook(() => useCategoryStore())
    await act(async () => {
      await result.current.fetchCategories(1)
      await result.current.fetchAllValues()
      await result.current.deleteCategory(1)
    })
    vi.mocked(categoriesApi.create).mockResolvedValue(cat(5, 'A') as never)
    vi.mocked(valuesApi.create).mockResolvedValue({ id: 50, value: 'a1', risk_weight: 2, vtype: 'string', allowed: true, is_default: false } as never)
    await act(async () => {
      await result.current.undo()
    })
    expect(valuesApi.create).toHaveBeenCalledWith(5, { value: 'a1', risk_weight: 2 })
    expect(categoriesApi.updateProperties).toHaveBeenCalledWith(50, { allowed: false, vtype: 'string' })
    expect(categoriesApi.setDefault).toHaveBeenCalledWith(50)
    expect(reorderApi.categories).toHaveBeenCalledWith(1, [5, 2])
  })

  test('Umbenennen und Sortieren sind rueckgaengig zu machen', async () => {
    vi.mocked(categoriesApi.list).mockResolvedValue([cat(1, 'A'), cat(2, 'B')] as never)
    vi.mocked(renameApi.category).mockResolvedValue(cat(1, 'A2') as never)
    const { result } = renderHook(() => useCategoryStore())
    await act(async () => {
      await result.current.fetchCategories(1)
      await result.current.renameCategory(1, 'A2')
      await result.current.reorderCategories(1, [2, 1])
    })
    await act(async () => {
      await result.current.undo()
      await result.current.undo()
    })
    expect(reorderApi.categories).toHaveBeenLastCalledWith(1, [1, 2])
    expect(renameApi.category).toHaveBeenLastCalledWith(1, 'A')
  })

  test('fetchCategories resets history', async () => {
    vi.mocked(categoriesApi.create).mockResolvedValue(cat(102, 'X') as never)
    const { result } = renderHook(() => useCategoryStore())
    await act(async () => {
      await result.current.createCategory(1, 'X')
    })
    expect(result.current.canUndo).toBe(true)
    await act(async () => {
      await result.current.fetchCategories(1)
    })
    expect(result.current.canUndo).toBe(false)
    expect(result.current.canRedo).toBe(false)
  })
})

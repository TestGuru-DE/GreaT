// REQ-3054: Pfeiltasten-Navigation und Fokus-Management für Office-ähnliche UX
import { useEffect, useState, useCallback } from "react";

export interface NavigableItem {
  id: number | string;
  onSelect?: () => void;
  onDelete?: () => void;
  onRename?: () => void;
}

/**
 * Hook für Office-ähnliche Tastaturnavigation in Listen.
 * Verwaltet Fokus-Index und reagiert auf Pfeiltasten, Enter, Delete, F2, Escape.
 * 
 * @param items - Array von Elementen mit ID und optionalen Callbacks
 * @param enabled - ob Navigation aktiv ist
 * @returns focusedIndex, setFocusedIndex, Handlers
 */
export function useKeyboardNav<T extends NavigableItem>(
  items: T[],
  enabled = true
) {
  const [focusedIndex, setFocusedIndex] = useState(-1);

  // Pfeiltasten-Navigation
  const handleArrowDown = useCallback(() => {
    if (!enabled || items.length === 0) return;
    setFocusedIndex((i) => (i < items.length - 1 ? i + 1 : i));
  }, [enabled, items.length]);

  const handleArrowUp = useCallback(() => {
    if (!enabled || items.length === 0) return;
    setFocusedIndex((i) => (i > 0 ? i - 1 : i));
  }, [enabled, items.length]);

  // Enter: Element auswählen
  const handleEnter = useCallback(() => {
    if (!enabled || focusedIndex < 0 || focusedIndex >= items.length) return;
    const item = items[focusedIndex];
    item.onSelect?.();
  }, [enabled, focusedIndex, items]);

  // Delete: Element löschen
  const handleDelete = useCallback(() => {
    if (!enabled || focusedIndex < 0 || focusedIndex >= items.length) return;
    const item = items[focusedIndex];
    item.onDelete?.();
  }, [enabled, focusedIndex, items]);

  // F2: Element umbenennen
  const handleF2 = useCallback(() => {
    if (!enabled || focusedIndex < 0 || focusedIndex >= items.length) return;
    const item = items[focusedIndex];
    item.onRename?.();
  }, [enabled, focusedIndex, items]);

  // Escape: Fokus aufheben
  const handleEscape = useCallback(() => {
    if (!enabled) return;
    setFocusedIndex(-1);
  }, [enabled]);

  useEffect(() => {
    if (!enabled) return;

    const handler = (e: KeyboardEvent) => {
      // Keine Navigation wenn in Input/Textarea
      if ((e.target as HTMLElement)?.tagName === "INPUT" || 
          (e.target as HTMLElement)?.tagName === "TEXTAREA") {
        return;
      }

      switch (e.key) {
        case "ArrowDown":
          e.preventDefault();
          handleArrowDown();
          break;
        case "ArrowUp":
          e.preventDefault();
          handleArrowUp();
          break;
        case "Enter":
          e.preventDefault();
          handleEnter();
          break;
        case "Delete":
          e.preventDefault();
          handleDelete();
          break;
        case "F2":
          e.preventDefault();
          handleF2();
          break;
        case "Escape":
          e.preventDefault();
          handleEscape();
          break;
      }
    };

    window.addEventListener("keydown", handler);
    return () => window.removeEventListener("keydown", handler);
  }, [enabled, handleArrowDown, handleArrowUp, handleEnter, handleDelete, handleF2, handleEscape]);

  return {
    focusedIndex,
    setFocusedIndex,
  };
}

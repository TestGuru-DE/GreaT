// REQ-1210: Keyboard-Shortcuts Hook
import { useEffect } from "react";

interface ShortcutMap {
  [key: string]: (e: KeyboardEvent) => void;
}

/**
 * Registriert Keyboard-Shortcuts.
 * Key-Format: "ctrl+n", "f2", "delete", "escape"
 */
export function useKeyboardShortcuts(shortcuts: ShortcutMap) {
  useEffect(() => {
    const handler = (e: KeyboardEvent) => {
      const key = [
        e.ctrlKey ? "ctrl" : "",
        e.shiftKey ? "shift" : "",
        e.key.toLowerCase(),
      ]
        .filter(Boolean)
        .join("+");
      if (shortcuts[key]) {
        e.preventDefault();
        shortcuts[key](e);
      }
    };
    window.addEventListener("keydown", handler);
    return () => window.removeEventListener("keydown", handler);
  }, [shortcuts]);
}
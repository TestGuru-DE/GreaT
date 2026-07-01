// REQ-1214: Testfalltabelle sortieren
import { useState, useMemo } from "react";

type SortDir = "asc" | "desc" | null;

export function useSortableTable<T extends Record<string, unknown>>(rows: T[]) {
  const [sortCol, setSortCol] = useState<string | null>(null);
  const [sortDir, setSortDir] = useState<SortDir>(null);

  const toggleSort = (col: string) => {
    if (sortCol !== col) { setSortCol(col); setSortDir("asc"); return; }
    if (sortDir === "asc") { setSortDir("desc"); return; }
    setSortCol(null); setSortDir(null);
  };

  const sorted = useMemo(() => {
    if (!sortCol || !sortDir) return rows;
    return [...rows].sort((a, b) => {
      const av = String(a[sortCol] ?? "");
      const bv = String(b[sortCol] ?? "");
      return sortDir === "asc" ? av.localeCompare(bv) : bv.localeCompare(av);
    });
  }, [rows, sortCol, sortDir]);

  return { sorted, sortCol, sortDir, toggleSort };
}
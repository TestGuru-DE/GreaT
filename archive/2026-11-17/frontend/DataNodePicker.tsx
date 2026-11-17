// REQ-4018: Hierarchische Datenklassen - Picker für Projekt-Kategorien
import { useState, useEffect, useRef } from 'react';
import type { DataNode } from '../types';
import { datanodesApi } from '../api/client';

interface Props {
  onSelect: (value: string) => void;
  placeholder?: string;
}

function flattenValues(nodes: DataNode[], prefix = ''): { label: string; value: string }[] {
  const result: { label: string; value: string }[] = [];
  for (const node of nodes) {
    const path = prefix ? `${prefix} › ${node.name}` : node.name;
    for (const v of node.values) {
      result.push({ label: `${path}: ${v.value}`, value: v.value });
    }
    if (node.children.length > 0) {
      result.push(...flattenValues(node.children, path));
    }
  }
  return result;
}

export function DataNodePicker({ onSelect, placeholder = 'Wert aus Bibliothek wählen...' }: Props) {
  const [tree, setTree] = useState<DataNode[]>([]);
  const [open, setOpen] = useState(false);
  const [search, setSearch] = useState('');
  const dropdownRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (open && tree.length === 0) {
      datanodesApi.getTree().then(setTree).catch(console.error);
    }
  }, [open, tree.length]);

  // Click outside schließt das Dropdown
  useEffect(() => {
    const handleClickOutside = (e: MouseEvent) => {
      if (dropdownRef.current && !dropdownRef.current.contains(e.target as Node)) {
        setOpen(false);
        setSearch('');
      }
    };
    if (open) {
      document.addEventListener('mousedown', handleClickOutside);
      return () => document.removeEventListener('mousedown', handleClickOutside);
    }
  }, [open]);

  const allValues = flattenValues(tree);
  const filtered = search
    ? allValues.filter((v) => v.label.toLowerCase().includes(search.toLowerCase()))
    : allValues;

  return (
    <div className="relative" ref={dropdownRef}>
      <button
        onClick={() => setOpen(!open)}
        className="px-3 py-1.5 text-sm border border-theme-border rounded bg-theme-surface text-theme-text hover:bg-theme-border"
        type="button"
      >
        📚 {placeholder}
      </button>
      {open && (
        <div className="absolute z-50 top-full mt-1 w-96 bg-white border border-theme-border rounded-lg shadow-lg">
          <div className="p-2 border-b border-theme-border">
            <input
              autoFocus
              className="w-full px-2 py-1 text-sm border border-theme-border rounded"
              placeholder="Suchen..."
              value={search}
              onChange={(e) => setSearch(e.target.value)}
            />
          </div>
          <ul className="max-h-64 overflow-y-auto">
            {filtered.slice(0, 50).map((item, i) => (
              <li key={i}>
                <button
                  type="button"
                  className="w-full text-left px-3 py-1.5 text-sm hover:bg-theme-surface text-theme-text"
                  onClick={() => {
                    onSelect(item.value);
                    setOpen(false);
                    setSearch('');
                  }}
                >
                  <span className="text-theme-text-muted text-xs">
                    {item.label.split(': ')[0]}:{' '}
                  </span>
                  <span>{item.value}</span>
                </button>
              </li>
            ))}
            {filtered.length === 0 && (
              <li className="px-3 py-2 text-sm text-theme-text-muted">Keine Treffer</li>
            )}
            {filtered.length > 50 && (
              <li className="px-3 py-2 text-xs text-theme-text-muted border-t border-theme-border">
                ... und {filtered.length - 50} weitere
              </li>
            )}
          </ul>
        </div>
      )}
    </div>
  );
}

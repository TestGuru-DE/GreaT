// REQ-4018: Hierarchische Datenklassen - Baumansicht
import { useState } from 'react';
import type { DataNode } from '../types';

interface Props {
  nodes: DataNode[];
  depth?: number;
  onAddChild?: (parentId: number, name: string) => void;
  onAddValue?: (nodeId: number, value: string) => void;
  onDelete?: (nodeId: number) => void;
  onRename?: (nodeId: number, name: string) => void;
}

function getNodeLabel(node: DataNode, depth: number): string {
  const hasChildren = node.children.length > 0;
  if (!hasChildren) return 'Klasse';
  if (depth === 0) return 'Kategorie';
  return 'Gruppe';
}

export function DataNodeTree({
  nodes,
  depth = 0,
  onAddChild,
  onAddValue,
  onDelete,
  onRename,
}: Props) {
  const [expanded, setExpanded] = useState<Set<number>>(new Set());
  const [addingChild, setAddingChild] = useState<number | null>(null);
  const [childName, setChildName] = useState('');
  const [addingValue, setAddingValue] = useState<number | null>(null);
  const [valueName, setValueName] = useState('');

  const toggleExpand = (id: number) => {
    setExpanded((prev) => {
      const next = new Set(prev);
      next.has(id) ? next.delete(id) : next.add(id);
      return next;
    });
  };

  return (
    <ul className={`space-y-1 ${depth > 0 ? 'ml-4 border-l border-theme-border pl-3' : ''}`}>
      {nodes.map((node) => {
        const label = getNodeLabel(node, depth);
        const isExpanded = expanded.has(node.id);
        const hasContent = node.children.length > 0 || node.values.length > 0;

        return (
          <li key={node.id}>
            <div className="flex items-center gap-2 py-1 px-2 rounded hover:bg-theme-surface group">
              {/* Expand Toggle */}
              {hasContent ? (
                <button
                  onClick={() => toggleExpand(node.id)}
                  className="text-theme-text-muted w-4 text-xs"
                  aria-label={isExpanded ? 'Zuklappen' : 'Aufklappen'}
                >
                  {isExpanded ? '▼' : '▶'}
                </button>
              ) : (
                <span className="w-4" />
              )}

              {/* Label (Kategorie/Gruppe/Klasse) */}
              <span className="text-xs text-theme-text-muted w-16 shrink-0">{label}</span>

              {/* Name */}
              <span className="flex-1 text-sm text-theme-text font-medium">{node.name}</span>

              {/* Wert-Count */}
              {node.values.length > 0 && (
                <span className="text-xs text-theme-text-muted">
                  {node.values.length} Werte
                </span>
              )}

              {/* Aktionen (nur on hover, nicht system) */}
              {!node.is_system && (
                <div className="hidden group-hover:flex gap-1">
                  <button
                    title="Untergruppe hinzufügen"
                    onClick={() => { setAddingChild(node.id); setAddingValue(null); }}
                    className="text-xs px-1.5 py-0.5 rounded bg-theme-primary text-white hover:bg-opacity-90"
                  >
                    + Gruppe
                  </button>
                  <button
                    title="Wert hinzufügen"
                    onClick={() => { setAddingValue(node.id); setAddingChild(null); }}
                    className="text-xs px-1.5 py-0.5 rounded bg-theme-surface border border-theme-border text-theme-text hover:bg-theme-border"
                  >
                    + Wert
                  </button>
                  <button
                    title="Löschen"
                    onClick={() => onDelete?.(node.id)}
                    className="text-xs px-1.5 py-0.5 rounded text-red-500 hover:bg-red-50"
                  >
                    ✕
                  </button>
                </div>
              )}
            </div>

            {/* Inline-Formular: Neue Gruppe */}
            {addingChild === node.id && (
              <div className="ml-6 mt-1 flex gap-2 items-center">
                <input 
                  autoFocus 
                  type="text" 
                  value={childName}
                  onChange={e => setChildName(e.target.value)}
                  onKeyDown={e => {
                    if (e.key === 'Enter' && childName.trim()) {
                      onAddChild?.(node.id, childName.trim());
                      setChildName(''); 
                      setAddingChild(null);
                    }
                    if (e.key === 'Escape') { 
                      setChildName(''); 
                      setAddingChild(null); 
                    }
                  }}
                  placeholder="Name der Gruppe/Klasse..."
                  className="px-2 py-1 text-xs border border-theme-border rounded bg-white flex-1"
                />
                <button 
                  onClick={() => {
                    if (childName.trim()) {
                      onAddChild?.(node.id, childName.trim());
                      setChildName(''); 
                      setAddingChild(null);
                    }
                  }} 
                  className="text-xs px-2 py-1 bg-theme-primary text-white rounded"
                >
                  ✓
                </button>
                <button 
                  onClick={() => { setChildName(''); setAddingChild(null); }}
                  className="text-xs px-2 py-1 text-theme-text-muted"
                >
                  ✕
                </button>
              </div>
            )}

            {/* Inline-Formular: Neuer Wert */}
            {addingValue === node.id && (
              <div className="ml-6 mt-1 flex gap-2 items-center">
                <input 
                  autoFocus 
                  type="text" 
                  value={valueName}
                  onChange={e => setValueName(e.target.value)}
                  onKeyDown={e => {
                    if (e.key === 'Enter' && valueName.trim()) {
                      onAddValue?.(node.id, valueName.trim());
                      setValueName(''); 
                      setAddingValue(null);
                    }
                    if (e.key === 'Escape') { 
                      setValueName(''); 
                      setAddingValue(null); 
                    }
                  }}
                  placeholder="Neuer Wert..."
                  className="px-2 py-1 text-xs border border-theme-border rounded bg-white flex-1"
                />
                <button 
                  onClick={() => {
                    if (valueName.trim()) {
                      onAddValue?.(node.id, valueName.trim());
                      setValueName(''); 
                      setAddingValue(null);
                    }
                  }} 
                  className="text-xs px-2 py-1 bg-theme-primary text-white rounded"
                >
                  ✓
                </button>
                <button 
                  onClick={() => { setValueName(''); setAddingValue(null); }}
                  className="text-xs px-2 py-1 text-theme-text-muted"
                >
                  ✕
                </button>
              </div>
            )}

            {/* Kinder und Werte (aufgeklappt) */}
            {isExpanded && (
              <div className="ml-4">
                {/* Direkte Werte dieses Knotens */}
                {node.values.length > 0 && (
                  <ul className="ml-4 border-l border-theme-border pl-3 space-y-0.5">
                    {node.values.map((v) => (
                      <li key={v.id} className="text-xs text-theme-text-muted py-0.5 px-2">
                        • {v.value}
                      </li>
                    ))}
                  </ul>
                )}
                {/* Kindknoten rekursiv */}
                {node.children.length > 0 && (
                  <DataNodeTree
                    nodes={node.children}
                    depth={depth + 1}
                    onAddChild={onAddChild}
                    onAddValue={onAddValue}
                    onDelete={onDelete}
                    onRename={onRename}
                  />
                )}
              </div>
            )}
          </li>
        );
      })}
    </ul>
  );
}

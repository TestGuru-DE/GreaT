// REQ-4018: DataClassesPage komplett auf DataNode-Baum umgestellt
import React, { useState, useEffect, useCallback } from 'react';
import { DataNode } from '../types';
import { DataNodeTree } from '../components/DataNodeTree';
import { datanodesApi } from '../api/client';

export default function DataClassesPage() {
  const [tree, setTree] = useState<DataNode[]>([]);
  const [loading, setLoading] = useState(false);
  const [bugmagnetImported, setBugmagnetImported] = useState(false);
  const [importing, setImporting] = useState(false);
  const [importMsg, setImportMsg] = useState<string | null>(null);
  const [activeTab, setActiveTab] = useState<'mine' | 'system'>('mine');
  const [addingRoot, setAddingRoot] = useState(false);
  const [newRootName, setNewRootName] = useState('');

  const reload = useCallback(async () => {
    setLoading(true);
    try {
      const t = await datanodesApi.getTree();
      setTree(t);
    } catch (err) {
      console.error('Failed to load DataNode tree:', err);
    }
    setLoading(false);
  }, []);

  useEffect(() => {
    reload();
    datanodesApi.getBugMagnetStatus()
      .then(d => setBugmagnetImported(d.imported))
      .catch(console.error);
  }, [reload]);

  const systemNodes = tree.filter(n => n.is_system);
  const userNodes = tree.filter(n => !n.is_system);

  async function handleAddRoot() {
    if (!newRootName.trim()) return;
    try {
      await datanodesApi.create({ name: newRootName.trim(), parent_id: null, is_system: false });
      setNewRootName('');
      setAddingRoot(false);
      reload();
    } catch (err) {
      alert('Fehler beim Anlegen: ' + String(err));
    }
  }

  async function handleAddChild(parentId: number, name: string) {
    try {
      await datanodesApi.create({ name, parent_id: parentId, is_system: false });
      reload();
    } catch (err) {
      alert('Fehler beim Anlegen: ' + String(err));
    }
  }

  async function handleAddValue(nodeId: number, value: string) {
    try {
      await datanodesApi.addValue(nodeId, value);
      reload();
    } catch (err) {
      alert('Fehler beim Hinzufügen: ' + String(err));
    }
  }

  async function handleDelete(nodeId: number) {
    if (!confirm('Knoten und alle Unterpunkte löschen?')) return;
    try {
      await datanodesApi.delete(nodeId);
      reload();
    } catch (err) {
      alert('Fehler beim Löschen: ' + String(err));
    }
  }

  async function handleBugMagnetImport() {
    setImporting(true);
    setImportMsg(null);
    try {
      const r = await datanodesApi.importBugMagnet();
      setBugmagnetImported(true);
      setImportMsg(`✅ ${r.nodes_created ?? '?'} Knoten importiert`);
      reload();
    } catch (err) {
      setImportMsg('❌ Import fehlgeschlagen: ' + String(err));
    }
    setImporting(false);
  }

  async function handleImportJSON(e: React.ChangeEvent<HTMLInputElement>) {
    const file = e.target.files?.[0];
    if (!file) return;
    const fd = new FormData();
    fd.append('file', file);
    try {
      const r = await fetch('/api/datanodes/import-user', { method: 'POST', body: fd });
      const d = await r.json();
      if (r.ok) {
        alert(`✅ ${d.imported} Klassen importiert`);
        reload();
      } else {
        alert(`❌ ${d.detail}`);
      }
    } catch (err) {
      alert('Fehler beim Import: ' + String(err));
    }
    e.target.value = '';
  }

  return (
    <div className="p-6 space-y-6 max-w-5xl mx-auto">
      <h1 className="text-2xl font-bold text-theme-text">🗂️ Datenklassen-Bibliothek</h1>

      {/* Tabs */}
      <div className="flex gap-2 border-b border-theme-border">
        <button
          onClick={() => setActiveTab('mine')}
          className={`px-4 py-2 text-sm font-medium border-b-2 transition-colors ${
            activeTab === 'mine'
              ? 'border-primary-600 text-primary-600'
              : 'border-transparent text-theme-text-muted hover:text-theme-text'
          }`}
        >
          📁 Meine Datenklassen ({userNodes.length})
        </button>
        <button
          onClick={() => setActiveTab('system')}
          className={`px-4 py-2 text-sm font-medium border-b-2 transition-colors ${
            activeTab === 'system'
              ? 'border-primary-600 text-primary-600'
              : 'border-transparent text-theme-text-muted hover:text-theme-text'
          }`}
        >
          {bugmagnetImported ? '🐛 Bug Magnet Import' : '📋 Beispiele'} ({systemNodes.length})
        </button>
      </div>

      {activeTab === 'mine' && (
        <div className="space-y-4">
          {/* Import/Export (REQ-4013 erhalten) */}
          <div className="flex gap-3 items-center p-3 bg-theme-surface rounded-lg border border-theme-border">
            <span className="text-sm text-theme-text-muted font-medium">Import / Export:</span>
            <a
              href="/api/datanodes/export-user"
              download="my-dataclasses.json"
              className="px-3 py-1.5 text-sm bg-primary-600 text-white rounded hover:opacity-90 transition-opacity"
            >
              📤 Exportieren
            </a>
            <label className="px-3 py-1.5 text-sm border border-theme-border rounded cursor-pointer hover:bg-theme-border text-theme-text transition-colors">
              📥 Importieren (JSON)
              <input type="file" accept=".json" className="hidden" onChange={handleImportJSON} />
            </label>
          </div>

          {/* Neue Kategorie */}
          {addingRoot ? (
            <div className="flex gap-2 items-center p-3 bg-theme-surface rounded-lg border border-theme-border">
              <input
                autoFocus
                type="text"
                value={newRootName}
                onChange={e => setNewRootName(e.target.value)}
                onKeyDown={e => {
                  if (e.key === 'Enter') handleAddRoot();
                  if (e.key === 'Escape') { setAddingRoot(false); setNewRootName(''); }
                }}
                placeholder="Name der neuen Kategorie..."
                className="flex-1 px-3 py-1.5 text-sm border border-theme-border rounded bg-white text-theme-text"
              />
              <button 
                onClick={handleAddRoot}
                className="px-3 py-1.5 text-sm bg-primary-600 text-white rounded hover:opacity-90 transition-opacity"
              >
                Anlegen
              </button>
              <button 
                onClick={() => { setAddingRoot(false); setNewRootName(''); }}
                className="px-3 py-1.5 text-sm border border-theme-border rounded text-theme-text-muted hover:bg-theme-border transition-colors"
              >
                Abbrechen
              </button>
            </div>
          ) : (
            <button
              onClick={() => setAddingRoot(true)}
              className="px-4 py-2 bg-primary-600 text-white rounded hover:opacity-90 text-sm font-medium transition-opacity"
            >
              + Neue Kategorie anlegen
            </button>
          )}

          {loading ? (
            <p className="text-theme-text-muted text-sm">Lade...</p>
          ) : userNodes.length === 0 ? (
            <div className="p-8 text-center text-theme-text-muted border-2 border-dashed border-theme-border rounded-lg">
              <p className="text-lg mb-2">Noch keine eigenen Datenklassen</p>
              <p className="text-sm">Klicke auf "+ Neue Kategorie anlegen" um zu starten</p>
            </div>
          ) : (
            <div className="bg-theme-surface rounded-lg border border-theme-border p-3">
              <DataNodeTree
                nodes={userNodes}
                onAddChild={handleAddChild}
                onAddValue={handleAddValue}
                onDelete={handleDelete}
              />
            </div>
          )}
        </div>
      )}

      {activeTab === 'system' && (
        <div className="space-y-4">
          {/* BugMagnet Import */}
          <div className="p-4 bg-theme-surface rounded-lg border border-theme-border space-y-2">
            <p className="text-sm text-theme-text">
              Beispielklassen von <strong>Bug Magnet</strong> – für die Inhalte ist der Urheber verantwortlich.
            </p>
            <a
              href="https://github.com/gojko/bugmagnet/blob/master/template/config.json"
              target="_blank"
              rel="noopener noreferrer"
              className="text-xs text-primary-600 hover:underline block"
            >
              github.com/gojko/bugmagnet/blob/master/template/config.json
            </a>
            <button
              onClick={handleBugMagnetImport}
              disabled={importing}
              className="px-4 py-2 bg-primary-600 text-white rounded hover:opacity-90 disabled:opacity-40 text-sm transition-opacity"
            >
              {importing ? '⏳ Importiere...' : bugmagnetImported ? '🔄 Aktualisieren' : '📥 Importieren'}
            </button>
            {importMsg && <p className="text-sm text-theme-text">{importMsg}</p>}
          </div>

          {loading ? (
            <p className="text-theme-text-muted text-sm">Lade...</p>
          ) : systemNodes.length === 0 ? (
            <p className="text-theme-text-muted text-sm p-4">
              Noch keine Beispieldaten – klicke auf "Importieren".
            </p>
          ) : (
            <div className="bg-theme-surface rounded-lg border border-theme-border p-3">
              <DataNodeTree nodes={systemNodes} />
            </div>
          )}
        </div>
      )}
    </div>
  );
}

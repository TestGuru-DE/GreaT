// REQ-3002 + REQ-3045: Einstellungen + Theme-System
// REQ-4011: Datensicherung & Wiederherstellung
// REQ-4012: BugMagnet-Import
// REQ-4025: Benutzerverwaltung
import { useState, useEffect } from 'react'
import { ThemeSwitcher } from '../components/ThemeSwitcher'
import { PortSettingsCard } from '../components/PortSettingsCard'
import { MaxTestCasesSettingsCard } from '../components/MaxTestCasesSettingsCard' // REQ-4018
import UserManagement from '../components/UserManagement' // REQ-4025

export default function SettingsPage() {
  const [backupPassword, setBackupPassword] = useState('')
  const [restorePassword, setRestorePassword] = useState('')
  const [restoreFile, setRestoreFile] = useState<File | null>(null)
  const [restoreStatus, setRestoreStatus] = useState<string | null>(null)
  const [isLoading, setIsLoading] = useState(false)
  const [resetDialogOpen, setResetDialogOpen] = useState(false)
  const [resetStatus, setResetStatus] = useState<string | null>(null)

  const [bugmagnetImported, setBugmagnetImported] = useState(false)
  const [importing, setImporting] = useState(false)
  const [importStatus, setImportStatus] = useState<string | null>(null)

  async function handleBackup() {
    setIsLoading(true)
    try {
      const url = backupPassword
        ? `/api/backup?password=${encodeURIComponent(backupPassword)}`
        : '/api/backup'
      const response = await fetch(url)
      const blob = await response.blob()
      const a = document.createElement('a')
      a.href = URL.createObjectURL(blob)
      a.download = `great_backup_${new Date().toISOString().split('T')[0]}.zip`
      a.click()
      setBackupPassword('')
    } finally {
      setIsLoading(false)
    }
  }

  async function handleRestore() {
    if (!restoreFile) return
    setIsLoading(true)
    setRestoreStatus(null)
    try {
      const form = new FormData()
      form.append('file', restoreFile)
      const url = restorePassword
        ? `/api/backup/restore?password=${encodeURIComponent(restorePassword)}`
        : '/api/backup/restore'
      const r = await fetch(url, { method: 'POST', body: form })
      const data = await r.json()
      if (r.ok) {
        setRestoreStatus(`OK ${data.projects_restored} Projekte wiederhergestellt`)
        setRestoreFile(null)
        setRestorePassword('')
      } else {
        setRestoreStatus(`Fehler: ${data.detail}`)
      }
    } catch (e) {
      setRestoreStatus(`Fehler: ${e instanceof Error ? e.message : 'Unbekannter Fehler'}`)
    } finally {
      setIsLoading(false)
    }
  }

  async function handleDatabaseReset(action: 'confirm' | 'backup') {
    try {
      if (action === 'backup') {
        const backupResponse = await fetch('/api/backup')
        if (!backupResponse.ok) {
          throw new Error('Backup konnte nicht erstellt werden')
        }
        const blob = await backupResponse.blob()
        const a = document.createElement('a')
        a.href = URL.createObjectURL(blob)
        a.download = `great_backup_${new Date().toISOString().split('T')[0]}.zip`
        a.click()
      }

      const resetResponse = await fetch('/api/backup/reset', { method: 'POST' })
      const data = await resetResponse.json()
      if (!resetResponse.ok) {
        throw new Error(data.detail || 'Reset fehlgeschlagen')
      }

      setResetDialogOpen(false)

      // REQ-4027 AK-12 / REQ-4028: Kein Passwort mehr anzeigen.
      // Nach Reset nur noch Hinweis basierend auf default_admin_created/default_admin_username.
      if (data.default_admin_created) {
        const username = data.default_admin_username || "admin";
        setResetStatus(
          `OK Datenbank wurde zurueckgesetzt.\n\n` +
          `Ein Standard-Admin wurde erstellt:\n` +
          `Benutzername: ${username}\n\n` +
          `Bitte aendere das Passwort nach dem Login!`
        )
      } else {
        setResetStatus(
          'OK Datenbank wurde zurueckgesetzt. Deine Session bleibt aktiv.'
        )
      }
    } catch (error) {
      setResetStatus(`Fehler: ${error instanceof Error ? error.message : 'Unbekannter Fehler'}`)
    }
  }

  useEffect(() => {
    (async () => {
      try {
        const r = await fetch('/api/datanodes/bugmagnet-status')
        if (r.ok) {
          const d = await r.json()
          setBugmagnetImported(d.imported)
        }
      } catch (err) {
        console.error('BugMagnet-Status konnte nicht abgerufen werden:', err)
      }
    })()
  }, [])

  async function handleBugMagnetImport() {
    setImporting(true)
    setImportStatus(null)
    try {
      const r = await fetch('/api/datanodes/bugmagnet-import', { method: 'POST' })
      const d = await r.json()
      if (r.ok) {
        setBugmagnetImported(true)
        setImportStatus(`OK Import abgeschlossen (${d.nodes_created} Knoten)`)
      } else {
        setImportStatus(`Fehler: ${d.detail}`)
      }
    } catch (e) {
      setImportStatus(`Fehler: ${e instanceof Error ? e.message : 'Unbekannter Fehler'}`)
    } finally {
      setImporting(false)
    }
  }

  return (
    <main className="max-w-2xl mx-auto px-6 py-12 bg-theme-bg">
      <h1 className="text-2xl font-bold text-theme-text mb-6">Einstellungen</h1>

      <PortSettingsCard />
      <MaxTestCasesSettingsCard />

      <section className="bg-theme-surface rounded-2xl border border-theme-border shadow-sm p-6 mb-6">
        <h2 className="text-lg font-semibold text-theme-text mb-3">Erscheinungsbild</h2>
        <p className="text-sm text-theme-text-secondary mb-4">
          Waehle ein Theme fuer die Oberflaeche. Die Einstellung wird automatisch gespeichert.
        </p>
        <ThemeSwitcher />
      </section>

      <section className="bg-theme-surface rounded-2xl border border-theme-border shadow-sm p-6 mb-6">
        <h2 className="text-lg font-semibold text-theme-text mb-4">Datensicherung</h2>
        <div className="space-y-4">
          <div className="border border-theme-border rounded-lg p-4">
            <h3 className="font-medium text-theme-text mb-3">Sicherung erstellen</h3>
            <div className="space-y-2">
              <input
                type="password"
                placeholder="Passwort (optional, fuer Verschluesselung)"
                value={backupPassword}
                onChange={e => setBackupPassword(e.target.value)}
                className="w-full px-3 py-2 rounded border border-theme-border bg-theme-bg text-theme-text placeholder-theme-text-muted"
              />
              <button
                onClick={handleBackup}
                disabled={isLoading}
                className="w-full px-4 py-2 bg-theme-accent hover:bg-theme-accent-hover disabled:opacity-50 text-theme-accent-text rounded transition"
              >
                {isLoading ? 'L?dt...' : 'Sicherung herunterladen'}
              </button>
            </div>
          </div>

          <div className="border border-theme-border rounded-lg p-4">
            <h3 className="font-medium text-theme-text mb-3">Sicherung wiederherstellen</h3>
            <div className="space-y-2">
              <input
                type="file"
                accept=".zip"
                onChange={e => setRestoreFile(e.target.files?.[0] ?? null)}
                className="w-full px-3 py-2 rounded border border-theme-border bg-theme-bg text-theme-text"
              />
              <input
                type="password"
                placeholder="Passwort (falls verschluesselt)"
                value={restorePassword}
                onChange={e => setRestorePassword(e.target.value)}
                className="w-full px-3 py-2 rounded border border-theme-border bg-theme-bg text-theme-text placeholder-theme-text-muted"
              />
              <button
                onClick={handleRestore}
                disabled={!restoreFile || isLoading}
                className="w-full px-4 py-2 bg-theme-accent hover:bg-theme-accent-hover disabled:opacity-50 text-theme-accent-text rounded transition"
              >
                {isLoading ? 'Verarbeitet...' : 'Wiederherstellen'}
              </button>
              {restoreStatus && (
                <p className="text-sm text-theme-text mt-2 p-2 bg-theme-bg rounded border border-theme-border">
                  {restoreStatus}
                </p>
              )}
            </div>
          </div>
        </div>
      </section>

      <section className="bg-theme-surface rounded-2xl border border-theme-border shadow-sm p-6 mb-6">
        <h2 className="text-lg font-semibold text-theme-text mb-4">Datenbank</h2>
        <div className="space-y-3">
          <p className="text-sm text-theme-text-secondary">
            Alle Projekte, Kategorien, Werte und Generierungen werden vollstaendig auf den Startzustand zurueckgesetzt.
          </p>
          <button
            type="button"
            onClick={() => setResetDialogOpen(true)}
            disabled={isLoading}
            className="px-4 py-2 bg-theme-danger hover:opacity-90 disabled:opacity-50 text-theme-accent-text rounded transition"
          >
            Datenbank zuruecksetzen
          </button>
          {resetStatus && (
            <p className="text-sm text-theme-text p-2 bg-theme-bg border border-theme-border rounded whitespace-pre-line">{resetStatus}</p>
          )}
        </div>
      </section>

      {resetDialogOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40" role="dialog" aria-label="Datenbank wirklich zuruecksetzen?">
          <div className="bg-theme-surface rounded-2xl shadow-xl max-w-md w-full mx-4 p-6 border border-theme-border">
            <h3 className="text-lg font-semibold text-theme-text mb-3">Datenbank wirklich zuruecksetzen?</h3>
            <p className="text-sm text-theme-text-secondary mb-2">
              Bist du sicher? Du loescht damit alles.
            </p>
            <p className="text-sm text-theme-warning bg-theme-bg border-2 border-theme-warning rounded-lg px-3 py-2 mb-5">
              Das Zuruecksetzen entfernt alle Projekte, Kategorien, Werte, Regeln und Generierungen von der Datenbank.
            </p>

            <div className="flex flex-col gap-2">
              <button type="button" onClick={() => handleDatabaseReset('confirm')} className="w-full px-4 py-2 bg-theme-danger text-theme-accent-text rounded-lg hover:opacity-90 font-medium text-sm">
                Ja mach
              </button>

              <button type="button" onClick={() => handleDatabaseReset('backup')} className="w-full px-4 py-2 border border-theme-border text-theme-text rounded-lg hover:bg-theme-surface-hover text-sm">
                Vorher Backup
              </button>

              <button type="button" onClick={() => { setResetDialogOpen(false); setResetStatus(null); }} className="w-full px-4 py-2 border border-theme-border text-theme-text-muted rounded-lg hover:bg-theme-surface-hover text-sm mt-1">
                Upsi nein
              </button>
            </div>
          </div>
        </div>
      )}

      <section className="bg-theme-surface rounded-2xl border border-theme-border shadow-sm p-6 mb-6">
        <h2 className="text-lg font-semibold text-theme-text mb-4">Datenklassen</h2>
        <div className="space-y-3">
          <p className="text-sm text-theme-text-secondary">
            Beispielklassen importieren von Bug Magnet Git.<br />
            <span className="text-xs text-theme-text-muted">Fuer die Inhalte ist der Urheber verantwortlich.</span>
          </p>
          <a href="https://github.com/gojko/bugmagnet/blob/master/template/config.json" target="_blank" rel="noopener noreferrer" className="text-xs text-theme-accent hover:underline block">
            github.com/gojko/bugmagnet/blob/master/template/config.json
          </a>
          <button onClick={handleBugMagnetImport} disabled={importing} className="px-4 py-2 bg-theme-accent hover:bg-theme-accent-hover disabled:opacity-50 text-theme-accent-text rounded transition">
            {importing ? 'Importiere...' : bugmagnetImported ? 'Aktualisieren' : 'Importieren'}
          </button>
          {importStatus && <p className="text-sm text-theme-text p-2 bg-theme-bg border border-theme-border rounded">{importStatus}</p>}
        </div>
      </section>

      {/* REQ-4025: Benutzerverwaltung (nur fuer Admins sichtbar) */}
      <UserManagement />
    </main>
  )
}

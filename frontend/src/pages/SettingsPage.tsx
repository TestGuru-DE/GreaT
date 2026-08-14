// REQ-3002 + REQ-3045: Einstellungen + Theme-System
// REQ-4011: Datensicherung & Wiederherstellung
import { useState } from 'react'
import { ThemeSwitcher } from '../components/ThemeSwitcher'

export default function SettingsPage() {
  const [backupPassword, setBackupPassword] = useState('')
  const [restorePassword, setRestorePassword] = useState('')
  const [restoreFile, setRestoreFile] = useState<File | null>(null)
  const [restoreStatus, setRestoreStatus] = useState<string | null>(null)
  const [isLoading, setIsLoading] = useState(false)

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
        setRestoreStatus(`✅ ${data.projects_restored} Projekte wiederhergestellt`)
        setRestoreFile(null)
        setRestorePassword('')
      } else {
        setRestoreStatus(`❌ Fehler: ${data.detail}`)
      }
    } catch (e) {
      setRestoreStatus(`❌ Fehler: ${e instanceof Error ? e.message : 'Unbekannter Fehler'}`)
    } finally {
      setIsLoading(false)
    }
  }

  return (
    <main className="max-w-2xl mx-auto px-6 py-12">
      <h1 className="text-2xl font-bold text-slate-800 dark:text-slate-100 mb-6">Einstellungen</h1>
      
      <section className="bg-white dark:bg-slate-800 rounded-2xl border border-slate-200 dark:border-slate-700 shadow-sm p-6 mb-6">
        <h2 className="text-lg font-semibold text-slate-800 dark:text-slate-100 mb-3">Erscheinungsbild</h2>
        <p className="text-sm text-slate-500 dark:text-slate-400 mb-4">
          Wähle ein Theme für die Oberfläche. Die Einstellung wird automatisch gespeichert.
        </p>
        <ThemeSwitcher />
      </section>

      <section className="bg-white dark:bg-slate-800 rounded-2xl border border-slate-200 dark:border-slate-700 shadow-sm p-6 mb-6">
        <h2 className="text-lg font-semibold text-slate-800 dark:text-slate-100 mb-4">💾 Datensicherung (REQ-4011)</h2>
        
        <div className="space-y-4">
          {/* Export */}
          <div className="border border-slate-300 dark:border-slate-600 rounded-lg p-4">
            <h3 className="font-medium text-slate-800 dark:text-slate-100 mb-3">Sicherung erstellen</h3>
            <div className="space-y-2">
              <input
                type="password"
                placeholder="Passwort (optional, für Verschlüsselung)"
                value={backupPassword}
                onChange={e => setBackupPassword(e.target.value)}
                className="w-full px-3 py-2 rounded border border-slate-300 dark:border-slate-600 bg-white dark:bg-slate-700 text-slate-900 dark:text-slate-100 placeholder-slate-500 dark:placeholder-slate-400"
              />
              <button
                onClick={handleBackup}
                disabled={isLoading}
                className="w-full px-4 py-2 bg-blue-600 hover:bg-blue-700 disabled:bg-blue-400 text-white rounded transition"
              >
                {isLoading ? '⏳ Lädt...' : '📥 Sicherung herunterladen'}
              </button>
            </div>
          </div>

          {/* Import */}
          <div className="border border-slate-300 dark:border-slate-600 rounded-lg p-4">
            <h3 className="font-medium text-slate-800 dark:text-slate-100 mb-3">Sicherung wiederherstellen</h3>
            <div className="space-y-2">
              <input
                type="file"
                accept=".zip"
                onChange={e => setRestoreFile(e.target.files?.[0] ?? null)}
                className="w-full px-3 py-2 rounded border border-slate-300 dark:border-slate-600 bg-white dark:bg-slate-700 text-slate-900 dark:text-slate-100"
              />
              <input
                type="password"
                placeholder="Passwort (falls verschlüsselt)"
                value={restorePassword}
                onChange={e => setRestorePassword(e.target.value)}
                className="w-full px-3 py-2 rounded border border-slate-300 dark:border-slate-600 bg-white dark:bg-slate-700 text-slate-900 dark:text-slate-100 placeholder-slate-500 dark:placeholder-slate-400"
              />
              <button
                onClick={handleRestore}
                disabled={!restoreFile || isLoading}
                className="w-full px-4 py-2 bg-blue-600 hover:bg-blue-700 disabled:bg-blue-400 text-white rounded transition"
              >
                {isLoading ? '⏳ Verarbeitet...' : '📤 Wiederherstellen'}
              </button>
              {restoreStatus && (
                <p className="text-sm text-slate-700 dark:text-slate-300 mt-2 p-2 bg-slate-100 dark:bg-slate-700 rounded">
                  {restoreStatus}
                </p>
              )}
            </div>
          </div>
        </div>
      </section>
    </main>
  );
}
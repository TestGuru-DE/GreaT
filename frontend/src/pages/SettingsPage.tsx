// REQ-3002 + REQ-3045: Einstellungen + Theme-System
// REQ-4011: Datensicherung & Wiederherstellung
// REQ-4012: BugMagnet-Import
// REQ-4025: Benutzerverwaltung
// REQ-6005: i18n
// REQ-6012: API-Token-Verwaltung

import { useState, useEffect } from 'react'
import { useTranslation } from 'react-i18next'
import { ThemeSwitcher } from '../components/ThemeSwitcher'
import { MaxTestCasesSettingsCard } from '../components/MaxTestCasesSettingsCard' // REQ-4018
import UserManagement from '../components/UserManagement' // REQ-4025
import ApiTokensCard from '../components/ApiTokensCard' // REQ-6012
import { backupApi, datanodesApi } from '../api/client'

export default function SettingsPage() {
  const { t } = useTranslation()
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
      const blob = backupPassword
        ? await backupApi.create(backupPassword)
        : await backupApi.create()
      const a = document.createElement('a')
      a.href = URL.createObjectURL(blob)
      a.download = backupPassword
        ? `great_backup_encrypted_${new Date().toISOString().split('T')[0]}.zip`
        : `great_backup_${new Date().toISOString().split('T')[0]}.zip`
      a.click()
      setBackupPassword('')
    } catch (e) {
      console.error('Backup fehlgeschlagen:', e)
    } finally {
      setIsLoading(false)
    }
  }

  async function handleRestore() {
    if (!restoreFile) return
    setIsLoading(true)
    setRestoreStatus(null)
    try {
      const data = await backupApi.restore(restoreFile, restorePassword || undefined)
      setRestoreStatus(t('settings.backup.restore.success', { count: data.projects_restored }))
      setRestoreFile(null)
      setRestorePassword('')
    } catch (e: unknown) {
      setRestoreStatus(t('settings.backup.restore.error', { message: e instanceof Error ? e.message : String(e) }))
    } finally {
      setIsLoading(false)
    }
  }

  async function handleDatabaseReset(action: 'confirm' | 'backup') {
    try {
      if (action === 'backup') {
        const blob = await backupApi.create()
        const a = document.createElement('a')
        a.href = URL.createObjectURL(blob)
        a.download = `great_backup_${new Date().toISOString().split('T')[0]}.zip`
        a.click()
      }

      const data = await backupApi.reset()

      setResetDialogOpen(false)

      // REQ-4027 AK-12 / REQ-4028: Kein Passwort mehr anzeigen.
      // Nach Reset nur noch Hinweis basierend auf default_admin_created/default_admin_username.
      if (data.default_admin_created) {
        const username = data.default_admin_username || "admin";
        setResetStatus(
          t('settings.database.resetSuccessAdmin', { username })
        )
      } else {
        setResetStatus(
          t('settings.database.resetSuccess')
        )
      }
    } catch (error) {
      setResetStatus(t('settings.database.resetError', { message: error instanceof Error ? error.message : t('errors.unknown') }))
    }
  }

  useEffect(() => {
    (async () => {
      try {
        const d = await datanodesApi.getBugMagnetStatus()
        setBugmagnetImported(d.imported)
      } catch (err) {
        console.error('BugMagnet-Status konnte nicht abgerufen werden:', err)
      }
    })()
  }, [])

  async function handleBugMagnetImport() {
    setImporting(true)
    setImportStatus(null)
    try {
      const d = await datanodesApi.importBugMagnet()
      setBugmagnetImported(true)
      setImportStatus(t('settings.dataclasses.importSuccess', { count: d.nodes_created }))
    } catch (e) {
      setImportStatus(t('settings.dataclasses.importError', { message: e instanceof Error ? e.message : t('errors.unknown') }))
    } finally {
      setImporting(false)
    }
  }

  return (
    <main className="page page-narrow">
      <header className="page-header">
        <h1 className="page-title text-theme-text">{t('settings.title')}</h1>
      </header>

      {/* B-49: Der Server-Port wird beim Start festgelegt, nicht im Browser */}
      <section className="card bg-theme-surface p-6 mb-6">
        <h2 className="text-xl font-bold text-theme-text mb-3">{t('portInfo.title')}</h2>
        <p className="text-sm text-theme-text-secondary">
          {t('portInfo.text', { port: window.location.port || (window.location.protocol === 'https:' ? '443' : '80') })}
        </p>
        <pre className="mt-3 text-sm bg-theme-surface-2 text-theme-text rounded-lg px-3 py-2 overflow-x-auto"><code>{t('portInfo.example')}</code></pre>
      </section>
      <MaxTestCasesSettingsCard />

      <section className="card bg-theme-surface p-6 mb-6">
        <h2 className="text-xl font-bold text-theme-text mb-3">{t('settings.appearance.title')}</h2>
        <p className="text-sm text-theme-text-secondary mb-4">
          {t('settings.appearance.description')}
        </p>
        <ThemeSwitcher />
      </section>

      <section className="card bg-theme-surface p-6 mb-6">
        <h2 className="text-xl font-bold text-theme-text mb-4">{t('settings.backup.title')}</h2>
        <div className="space-y-4">
          <div className="border border-theme-border rounded-lg p-4">
            <h3 className="font-medium text-theme-text mb-3">{t('settings.backup.create.title')}</h3>
            <div className="space-y-2">
              <input
                type="password"
                placeholder={t('settings.backup.create.passwordPlaceholder')}
                value={backupPassword}
                onChange={e => setBackupPassword(e.target.value)}
                className="w-full px-3 py-2 rounded border border-theme-border bg-theme-bg text-theme-text placeholder-theme-text-muted"
              />
              <button
                onClick={handleBackup}
                disabled={isLoading}
                className="w-full px-4 py-2 bg-theme-accent hover:bg-theme-accent-hover disabled:opacity-50 text-theme-accent-text rounded transition"
              >
                {isLoading ? t('settings.backup.create.downloadBtnLoading') : t('settings.backup.create.downloadBtn')}
              </button>
            </div>
          </div>

          <div className="border border-theme-border rounded-lg p-4">
            <h3 className="font-medium text-theme-text mb-3">{t('settings.backup.restore.title')}</h3>
            <div className="space-y-2">
              <input
                type="file"
                accept=".zip"
                onChange={e => setRestoreFile(e.target.files?.[0] ?? null)}
                className="w-full px-3 py-2 rounded border border-theme-border bg-theme-bg text-theme-text"
              />
              <input
                type="password"
                placeholder={t('settings.backup.restore.passwordPlaceholder')}
                value={restorePassword}
                onChange={e => setRestorePassword(e.target.value)}
                className="w-full px-3 py-2 rounded border border-theme-border bg-theme-bg text-theme-text placeholder-theme-text-muted"
              />
              <button
                onClick={handleRestore}
                disabled={!restoreFile || isLoading}
                className="w-full px-4 py-2 bg-theme-accent hover:bg-theme-accent-hover disabled:opacity-50 text-theme-accent-text rounded transition"
              >
                {isLoading ? t('settings.backup.restore.restoreBtnLoading') : t('settings.backup.restore.restoreBtn')}
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

      <section className="card bg-theme-surface p-6 mb-6">
        <h2 className="text-xl font-bold text-theme-text mb-4">{t('settings.database.title')}</h2>
        <div className="space-y-3">
          <p className="text-sm text-theme-text-secondary">
            {t('settings.database.description')}
          </p>
          <button
            type="button"
            onClick={() => setResetDialogOpen(true)}
            disabled={isLoading}
            className="px-4 py-2 bg-theme-danger-fill hover:opacity-90 disabled:opacity-50 text-theme-accent-text rounded transition"
          >
            {t('settings.database.resetBtn')}
          </button>
          {resetStatus && (
            <p className="text-sm text-theme-text p-2 bg-theme-bg border border-theme-border rounded whitespace-pre-line">{resetStatus}</p>
          )}
        </div>
      </section>

      {resetDialogOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40" role="dialog" aria-label={t('settings.database.dialog.title')}>
          <div className="bg-theme-surface rounded-2xl shadow-xl max-w-md w-full mx-4 p-6 border border-theme-border">
            <h3 className="text-lg font-semibold text-theme-text mb-3">{t('settings.database.dialog.title')}</h3>
            <p className="text-sm text-theme-text-secondary mb-2">
              {t('settings.database.dialog.confirm')}
            </p>
            <p className="text-sm text-theme-warning bg-theme-bg border-2 border-theme-warning rounded-lg px-3 py-2 mb-5">
              {t('settings.database.dialog.warning')}
            </p>

            <div className="flex flex-col gap-2">
              <button type="button" onClick={() => handleDatabaseReset('confirm')} className="w-full px-4 py-2 bg-theme-danger-fill text-theme-accent-text rounded-lg hover:opacity-90 font-medium text-sm">
                {t('settings.database.dialog.yesDoIt')}
              </button>

              <button type="button" onClick={() => handleDatabaseReset('backup')} className="w-full px-4 py-2 border border-theme-border text-theme-text rounded-lg hover:bg-theme-surface-hover text-sm">
                {t('settings.database.dialog.backupFirst')}
              </button>

              <button type="button" onClick={() => { setResetDialogOpen(false); setResetStatus(null); }} className="w-full px-4 py-2 border border-theme-border text-theme-text-muted rounded-lg hover:bg-theme-surface-hover text-sm mt-1">
                {t('settings.database.dialog.cancel')}
              </button>
            </div>
          </div>
        </div>
      )}

      <section className="card bg-theme-surface p-6 mb-6">
        <h2 className="text-xl font-bold text-theme-text mb-4">{t('settings.dataclasses.title')}</h2>
        <div className="space-y-3">
          <p className="text-sm text-theme-text-secondary" dangerouslySetInnerHTML={{ __html: t('settings.dataclasses.description') }} />
          <a href="https://github.com/gojko/bugmagnet/blob/master/template/config.json" target="_blank" rel="noopener noreferrer" className="text-xs text-theme-link hover:underline block">
            {t('settings.dataclasses.source')}
          </a>
          <button onClick={handleBugMagnetImport} disabled={importing} className="px-4 py-2 bg-theme-accent hover:bg-theme-accent-hover disabled:opacity-50 text-theme-accent-text rounded transition">
            {importing ? t('settings.dataclasses.importing') : bugmagnetImported ? t('settings.dataclasses.refresh') : t('settings.dataclasses.importBtn')}
          </button>
          {importStatus && <p className="text-sm text-theme-text p-2 bg-theme-bg border border-theme-border rounded">{importStatus}</p>}
        </div>
      </section>

      {/* REQ-4025: Benutzerverwaltung (nur fuer Admins sichtbar) */}
      <UserManagement />

      {/* REQ-6012: API-Token-Verwaltung */}
      <ApiTokensCard />
    </main>
  )
}
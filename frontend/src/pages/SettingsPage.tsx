// REQ-3002 + REQ-3045: Einstellungen + Theme-System
import { ThemeSwitcher } from '../components/ThemeSwitcher'

export default function SettingsPage() {
  return (
    <main className="max-w-2xl mx-auto px-6 py-12">
      <h1 className="text-2xl font-bold text-slate-800 mb-6">Einstellungen</h1>
      
      <section className="bg-white rounded-2xl border border-slate-200 shadow-sm p-6 mb-6">
        <h2 className="text-lg font-semibold text-slate-800 mb-3">Erscheinungsbild</h2>
        <p className="text-sm text-slate-500 mb-4">
          Wähle ein Theme für die Oberfläche. Die Einstellung wird automatisch gespeichert.
        </p>
        <ThemeSwitcher />
      </section>

      <section className="bg-white rounded-2xl border border-slate-200 shadow-sm p-8 text-center">
        <p className="text-4xl mb-4">⚙️</p>
        <p className="text-slate-400 text-sm">Weitere Konfigurationsoptionen kommen bald.</p>
      </section>
    </main>
  );
}
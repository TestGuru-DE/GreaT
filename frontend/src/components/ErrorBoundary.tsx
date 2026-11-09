// BUGFIX: Error Boundary - verhindert schwarzen Bildschirm bei Render-Fehlern
// REQ-4001, REQ-1208, REQ-2001
import { Component, ReactNode } from "react";

interface Props {
  children: ReactNode;
  fallback?: ReactNode;
}

interface State {
  hasError: boolean;
  error: Error | null;
}

export default class ErrorBoundary extends Component<Props, State> {
  constructor(props: Props) {
    super(props);
    this.state = { hasError: false, error: null };
  }

  static getDerivedStateFromError(error: Error): State {
    return { hasError: true, error };
  }

  render() {
    if (this.state.hasError) {
      return this.props.fallback || (
        <div className="min-h-screen bg-theme-bg flex items-center justify-center p-8">
          <div className="max-w-md w-full bg-red-50 border border-red-200 rounded-2xl p-6 text-center">
            <div className="text-4xl mb-4">⚠️</div>
            <h2 className="text-lg font-bold text-red-800 mb-2">
              Ein Fehler ist aufgetreten
            </h2>
            <p className="text-sm text-red-600 mb-4">
              Die Anwendung konnte nicht korrekt geladen werden.
            </p>
            <pre className="text-xs text-left bg-red-100 rounded-lg p-3 text-red-700 overflow-auto max-h-48">
              {this.state.error?.message || "Unbekannter Fehler"}
            </pre>
            <button
              onClick={() => window.location.reload()}
              className="mt-4 px-4 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700 text-sm font-medium"
            >
              Seite neu laden
            </button>
          </div>
        </div>
      );
    }
    return this.props.children;
  }
}
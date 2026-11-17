// B-42: ApiError-Klasse fuer typsichere Fehlerbehandlung
export class ApiError extends Error {
  public readonly status: number;
  public readonly code?: string;
  public readonly detail: unknown;

  constructor(status: number, detail: unknown, code?: string) {
    super(buildMessage(status, detail));
    this.name = 'ApiError';
    this.status = status;
    this.code = code;
    this.detail = detail;
  }
}

function buildMessage(status: number, detail: unknown): string {
  // Status 0 = Netzwerkfehler / Server nicht erreichbar
  if (status === 0) return 'Server nicht erreichbar';
  if (Array.isArray(detail)) {
    return detail
      .map((e) => (typeof e === 'object' && e !== null && 'msg' in e ? (e as any).msg : String(e)))
      .join('; ');
  }
  if (typeof detail === 'string') return detail;
  if (typeof detail === 'object' && detail !== null) {
    const d = detail as Record<string, unknown>;
    if (typeof d.detail === 'string') return d.detail;
    if (typeof d.message === 'string') return d.message;
  }
  return `Fehler (${status})`;
}
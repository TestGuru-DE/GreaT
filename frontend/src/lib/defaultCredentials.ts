// REQ-4027 / RISK-S-016: Standard-Credentials fuer Erststart-Hinweis
// Risikoakzeptanz durch Projektinhaber (Georg Hartel, 2026-11-03).
// Der Security Architect hat die Anzeige des Standardpassworts im Klartext
// als Risiko abgelehnt. Der Projektinhaber akzeptiert das Risiko bewusst.
// Die Massnahme zur Risikoreduktion ist REQ-4028 (Pflicht-Passwortwechsel).
//
// AK-7: Der Wert muss mit Backend-Konstante DEFAULT_ADMIN_PASSWORD uebereinstimmen.
// AK-12/4028-AK-9: Kein Passwort in Logs, console.log oder Fehlermeldungen.

export const DEFAULT_ADMIN_USERNAME = "admin";
export const DEFAULT_ADMIN_PASSWORD = "changeme123!";
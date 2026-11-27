import "@testing-library/jest-dom";

// Tests laufen auf Deutsch (jsdom meldet die Browsersprache en-US; seit A-15 waere
// sonst Englisch voreingestellt). Einzelne Tests schalten die Sprache gezielt um.
try { localStorage.setItem("great_language", "de"); } catch { /* ohne localStorage */ }

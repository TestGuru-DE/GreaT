import { StrictMode } from "react";
import { createRoot } from "react-dom/client";
import { BrowserRouter } from "react-router-dom";
import "./index.css";
// REQ-6005: i18n initialisieren VOR React-Mount
import "./i18n";
import App from "./App";
import { initTheme } from "./lib/theme";

// Theme initialisieren vor React-Mount (verhindert FOUC)
initTheme();

createRoot(document.getElementById("root")!).render(
  <StrictMode>
    <BrowserRouter>
      <App />
    </BrowserRouter>
  </StrictMode>
);
/// <reference types="vite/client" />
// Vite ?raw Import fuer Markdown-Dateien
declare module '*.md?raw' {
  const content: string;
  export default content;
}

// Vite Static Asset Imports
declare module '*.png' {
  const src: string;
  export default src;
}
declare module '*.jpg' {
  const src: string;
  export default src;
}
declare module '*.jpeg' {
  const src: string;
  export default src;
}
declare module '*.gif' {
  const src: string;
  export default src;
}
declare module '*.svg' {
  const src: string;
  export default src;
}

/** Version aus package.json (vite.config.ts, define) */
declare const __APP_VERSION__: string;

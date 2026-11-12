// Vite ?raw Import fuer Markdown-Dateien
declare module '*.md?raw' {
  const content: string;
  export default content;
}
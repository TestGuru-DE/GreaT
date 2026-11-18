// REQ-6005 Slice 3: Test fuer hartkodierte Strings in JSX
// Scaniert frontend/src/**/*.tsx (außer __tests__/*) auf Textknoten ohne t()
//
// Ausnahmen per `// i18n-ignore` Kommentar in der vorherigen Zeile
// Emojis und Sonderzeichen (z.B. "&ndash;") sind erlaubt
// HTML-Entities wie "&lt;", "&gt;", "&amp;" sind erlaubt
//
// Bekannte Ausnahmen (Slice 4+):
// - BVA-Dialoge (Grenzwertanalyse)
// - DecisionTable (Entscheidungstabelle)
// - ConstraintDialog
// - CauseEffectGraph

import { describe, it, expect } from "vitest";
import * as fs from "fs";
import * as path from "path";

// Recursively find all .tsx files, excluding __tests__ directories
function findTsxFiles(dir: string): string[] {
  const results: string[] = [];
  const entries = fs.readdirSync(dir, { withFileTypes: true });
  for (const entry of entries) {
    const fullPath = path.join(dir, entry.name);
    if (entry.isDirectory()) {
      // Skip __tests__ directories
      if (entry.name === "__tests__") continue;
      results.push(...findTsxFiles(fullPath));
    } else if (entry.isFile() && entry.name.endsWith(".tsx")) {
      // Skip test files
      if (entry.name.endsWith(".test.tsx") || entry.name.endsWith(".test.ts")) continue;
      results.push(fullPath);
    }
  }
  return results;
}

// Regex patterns
const T_FUNCTION_PATTERN = /\bt\(/;
const I18N_IGNORE_PATTERN = /^\s*\/\/\s*i18n-ignore/;
const HTML_ENTITY_PATTERN = /&[a-z]+;/g;
const UNICODE_SYMBOL_PATTERN = /[\u{1F300}-\u{1F9FF}]|[\u{2600}-\u{26FF}]|[\u{2700}-\u{27BF}]|[\u{FE00}-\u{FEFF}]/gu;
const WHITESPACE_ONLY_PATTERN = /^\s*$/;
const IMPORT_EXPORT_PATTERN = /^\s*(import|export|interface|type|const|function|class)\b/;
const COMMENT_PATTERN = /^\s*(\/\/|\/\*|\*)/;
const JSX_EXPR_PATTERN = /^\s*\{.*\}\s*$/;

// Files known to have hardcoded strings (out of scope for Slice 3, planned for Slice 4+)
const KNOWN_EXCEPTIONS: (string | RegExp)[] = [
  /BVAInputPanel\.tsx$/,
  /NumberlineVisualization\.tsx$/,
  /PreviewTable\.tsx$/,
  /CauseEffectGraph\.tsx$/,
  /ConstraintDialog\.tsx$/,
  /DecisionTable\.tsx$/,
  /DecisionTableHelp\.tsx$/,
  /ModelExportDropdown\.tsx$/,
  /RuleVisualization\.tsx$/,
  /TestCasePanel\.tsx$/,
  /App\.tsx$/,
];

function shouldSkipFile(relativePath: string): boolean {
  for (const exception of KNOWN_EXCEPTIONS) {
    if (typeof exception === "string") {
      if (relativePath.includes(exception)) return true;
    } else {
      if (exception.test(relativePath)) return true;
    }
  }
  return false;
}

function hasHtmlEntities(text: string): boolean {
  return HTML_ENTITY_PATTERN.test(text);
}

function hasUnicodeSymbols(text: string): boolean {
  return UNICODE_SYMBOL_PATTERN.test(text);
}

function isWhitespaceOnly(text: string): boolean {
  return WHITESPACE_ONLY_PATTERN.test(text);
}

/**
 * Extracts potential hardcoded text from a line of JSX.
 * Looks for text between > and < that isn't a t() call or expression.
 * Skips JSX expressions like {variable}, {obj.prop}, {fn()}.
 */
function extractPotentialHardcodedText(line: string): string[] {
  const results: string[] = [];
  // Match text between > and <
  const matches = line.matchAll(/>([^<{}]*(?:\{[^}]*\}[^<{}{}]*)*)</g);
  for (const match of matches) {
    const text = match[1].trim();
    if (text && !isWhitespaceOnly(text)) {
      // Skip pure JSX expressions: {something}
      if (/^\{[^}]*\}$/.test(text)) continue;
      // Skip lines that are only JSX expressions mixed with whitespace
      const withoutExpr = text.replace(/\{[^}]*\}/g, "").trim();
      if (!withoutExpr) continue;
      results.push(withoutExpr);
    }
  }
  return results;
}

function checkFile(filePath: string): string[] {
  const content = fs.readFileSync(filePath, "utf-8");
  const lines = content.split("\n");
  const violations: string[] = [];

  // Build a set of line numbers that have i18n-ignore
  const ignoredLines = new Set<number>();
  for (let i = 0; i < lines.length; i++) {
    if (I18N_IGNORE_PATTERN.test(lines[i])) {
      ignoredLines.add(i + 1); // Next line is ignored
    }
  }

  // Check each line for hardcoded text
  for (let i = 0; i < lines.length; i++) {
    const lineNum = i + 1;
    const line = lines[i];

    // Skip ignored lines
    if (ignoredLines.has(lineNum)) continue;

    // Skip lines with t() calls
    if (T_FUNCTION_PATTERN.test(line)) continue;

    // Skip import/export/type lines
    if (IMPORT_EXPORT_PATTERN.test(line)) continue;

    // Skip comment lines
    if (COMMENT_PATTERN.test(line)) continue;

    // Skip lines that are only JSX expressions { ... }
    if (JSX_EXPR_PATTERN.test(line)) continue;

    // Check for potential hardcoded text
    const textNodes = extractPotentialHardcodedText(line);
    for (const node of textNodes) {
      // Allow HTML entities
      if (hasHtmlEntities(node)) continue;

      // Allow Unicode symbols / emojis
      if (hasUnicodeSymbols(node)) continue;

      // Allow lines that contain only special chars
      if (/^[^a-zA-Z0-9]+$/.test(node)) continue;

      // This is a potential hardcoded string
      violations.push(`Line ${lineNum}: "${node.trim()}"`);
    }
  }

  return violations;
}

describe("REQ-6005: No hardcoded strings in JSX (Slice 3)", () => {
  it("should have no hardcoded strings in frontend/src/**/*.tsx (excluding tests)", () => {
    const srcDir = path.resolve(__dirname, "..");
    const files = findTsxFiles(srcDir);

    const allViolations: { file: string; violations: string[] }[] = [];

    for (const filePath of files) {
      const relativePath = path.relative(srcDir, filePath);

      // Skip known exceptions (out of scope for Slice 3)
      if (shouldSkipFile(relativePath)) continue;

      const violations = checkFile(filePath);
      if (violations.length > 0) {
        allViolations.push({ file: relativePath, violations });
      }
    }

    if (allViolations.length > 0) {
      const messages = allViolations
        .map((v) =>
          v.violations.map((vi) => `  ${v.file}:${vi}`).join("\n")
        )
        .join("\n");

      // Fail the test with detailed output
      expect(
        allViolations.length,
        `Found hardcoded strings in ${allViolations.length} file(s):\n${messages}\n\nFix: Wrap text in t() or add // i18n-ignore comment above the line.`
      ).toBe(0);
    }
  });

  it("should detect hardcoded strings in test content (negative test)", () => {
    // Create a temporary test to verify the detector works
    const testContent = `
function TestComponent() {
  return (
    <div>
      <h1>Hello World</h1>
      <p>This is hardcoded text</p>
    </div>
  );
}
`;
    // Write to temp file
    const tempFile = path.join(__dirname, "__temp_test_file.tsx");
    fs.writeFileSync(tempFile, testContent);

    try {
      const violations = checkFile(tempFile);
      expect(violations.length).toBeGreaterThan(0);
    } finally {
      fs.unlinkSync(tempFile);
    }
  });

  it("should allow t() wrapped text", () => {
    const testContent = `
import { useTranslation } from "react-i18next";
function TestComponent() {
  const { t } = useTranslation();
  return (
    <div>
      <h1>{t("nav.home")}</h1>
      <p>{t("common.loading")}</p>
    </div>
  );
}
`;
    const tempFile = path.join(__dirname, "__temp_test_file2.tsx");
    fs.writeFileSync(tempFile, testContent);

    try {
      const violations = checkFile(tempFile);
      expect(violations.length).toBe(0);
    } finally {
      fs.unlinkSync(tempFile);
    }
  });

  it("should allow // i18n-ignore comments", () => {
    const testContent = `
function TestComponent() {
  return (
    <div>
      // i18n-ignore
      <span>⚠️</span>
    </div>
  );
}
`;
    const tempFile = path.join(__dirname, "__temp_test_file3.tsx");
    fs.writeFileSync(tempFile, testContent);

    try {
      const violations = checkFile(tempFile);
      expect(violations.length).toBe(0);
    } finally {
      fs.unlinkSync(tempFile);
    }
  });
});
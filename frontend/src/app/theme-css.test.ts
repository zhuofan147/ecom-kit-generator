import { describe, expect, it } from "vitest";
import { readFileSync } from "node:fs";
import { resolve } from "node:path";

const css = readFileSync(resolve(__dirname, "globals.css"), "utf8");

describe("theme CSS", () => {
  it("uses dark field and surface colors in the black theme", () => {
    const blackTheme = css.match(/html\[data-theme="black"\]\s*\{(?<body>[\s\S]*?)\}/)?.groups?.body ?? "";

    expect(blackTheme).toContain("--color-surface: #111827");
    expect(blackTheme).toContain("--color-field: #0b1220");
  });

  it("keeps white theme fields light", () => {
    const whiteTheme = css.match(/html\[data-theme="white"\]\s*\{(?<body>[\s\S]*?)\}/)?.groups?.body ?? "";

    expect(whiteTheme).toContain("--color-surface: #ffffff");
    expect(whiteTheme).toContain("--color-field: #ffffff");
  });

  it("maps common utility classes to theme variables", () => {
    expect(css).toContain("background-color: var(--color-field)");
    expect(css).toContain("background-color: var(--color-surface)");
    expect(css).toContain("color: var(--color-muted)");
  });

  it("uses theme-aware selected card colors", () => {
    expect(css).toContain("--color-selected-bg: #0f2638");
    expect(css).toContain(".selected-card");
    expect(css).toContain("background-color: var(--color-selected-bg)");
  });
});

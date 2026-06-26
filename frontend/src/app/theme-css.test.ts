import { describe, expect, it } from "vitest";
import { readFileSync } from "node:fs";
import { resolve } from "node:path";

const css = readFileSync(resolve(__dirname, "globals.css"), "utf8");

describe("theme CSS", () => {
  it("uses dark field and surface colors in the dark theme", () => {
    const darkTheme = css.match(/html\[data-theme="dark"\]\s*\{([\s\S]*?)\}/)?.[1] ?? "";

    expect(darkTheme).toContain("--color-surface: #1a1a1c");
    expect(darkTheme).toContain("--color-field: #141416");
  });

  it("keeps white theme fields light", () => {
    const whiteTheme = css.match(/html\[data-theme="white"\]\s*\{([\s\S]*?)\}/)?.[1] ?? "";

    expect(whiteTheme).toContain("--color-surface: #ffffff");
    expect(whiteTheme).toContain("--color-field: #ffffff");
  });

  it("maps common utility classes to theme variables", () => {
    expect(css).toContain("background-color: var(--color-field)");
    expect(css).toContain("background-color: var(--color-surface)");
    expect(css).toContain("color: var(--color-muted)");
  });

  it("uses theme-aware selected card colors", () => {
    expect(css).toContain("--color-selected-bg: rgba(0, 117, 222, 0.14)");
    expect(css).toContain(".selected-card");
    expect(css).toContain("background-color: var(--color-selected-bg)");
  });
});

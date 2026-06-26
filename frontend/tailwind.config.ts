import type { Config } from "tailwindcss";

const config: Config = {
  content: ["./src/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        ink: "var(--color-ink)",
        muted: "var(--color-muted)",
        subtle: "var(--color-subtle)",
        line: "var(--color-line)",
        panel: "var(--color-panel)",
        surface: "var(--color-surface)",
        field: "var(--color-field)",
        action: "var(--color-action)",
        "action-hover": "var(--color-action-hover)",
        accent: "var(--color-accent)",
      },
      fontFamily: {
        sans: ["Geist", "system-ui", "-apple-system", "'Segoe UI'", "Roboto", "sans-serif"],
        mono: ["'Geist Mono'", "ui-monospace", "SFMono-Regular", "Menlo", "Monaco", "monospace"],
      },
      boxShadow: {
        "border": "var(--shadow-border)",
        "card": "var(--shadow-card)",
        "elevated": "var(--shadow-elevated)",
      },
    }
  },
  plugins: []
};

export default config;

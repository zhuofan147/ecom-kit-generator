import type { Config } from "tailwindcss";

const config: Config = {
  content: ["./src/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        ink: "var(--color-ink)",
        line: "var(--color-line)",
        panel: "var(--color-panel)",
        action: "var(--color-action)",
        accent: "var(--color-accent)"
      }
    }
  },
  plugins: []
};

export default config;

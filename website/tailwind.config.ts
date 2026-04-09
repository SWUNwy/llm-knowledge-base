import type { Config } from "tailwindcss";

const config: Config = {
  content: [
    "./app/**/*.{js,ts,jsx,tsx,mdx}",
    "./components/**/*.{js,ts,jsx,tsx,mdx}",
  ],
  theme: {
    extend: {
      colors: {
        brand: {
          blue: "#3b82f6",
          "blue-light": "#60a5fa",
          purple: "#7c3aed",
          "purple-light": "#a78bfa",
          green: "#10b981",
          "green-light": "#34d399",
        },
        surface: {
          dark: "#0f172a",
          "dark-secondary": "#1e293b",
          light: "#f8fafc",
          white: "#ffffff",
        },
        text: {
          primary: "#0f172a",
          secondary: "#64748b",
          "on-dark": "#f8fafc",
          "on-dark-muted": "#94a3b8",
        },
      },
      fontFamily: {
        sans: ["Inter", "system-ui", "-apple-system", "sans-serif"],
      },
      borderRadius: {
        card: "16px",
        button: "10px",
        tag: "20px",
      },
    },
  },
  plugins: [],
};

export default config;

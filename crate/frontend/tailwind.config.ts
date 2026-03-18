import type { Config } from "tailwindcss";

const config: Config = {
  content: ["./src/**/*.{js,ts,jsx,tsx,mdx}"],
  theme: {
    extend: {
      colors: {
        crate: {
          bg: "#0a0a0a",
          surface: "#141414",
          border: "#262626",
          text: "#e5e5e5",
          muted: "#737373",
          accent: "#f59e0b",
          blue: "#3b82f6",
          green: "#22c55e",
        },
      },
    },
  },
  plugins: [],
};
export default config;

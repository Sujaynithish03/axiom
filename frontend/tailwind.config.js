/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{js,ts,jsx,tsx}"],
  theme: {
    extend: {
      colors: {
        // Deep-navy trading terminal palette
        bg: "#070A14",
        surface: "#0E1424",
        surface2: "#151C33",
        border: "#1F2942",
        text: "#E8ECF5",
        muted: "#8B93A7",
        // The single accent — electric mint, our signal-green
        mint: "#00E5A0",
        mintDim: "#00A876",
        // Semantic
        danger: "#FF6B6B",
        warn: "#FFB454",
        info: "#5EA0FF",
        // Agent identity tints
        marketing: "#F0997B",
        sales: "#5DCAA5",
        finance: "#EF9F27",
        strategy: "#AFA9EC",
        ceo: "#00E5A0",
        learning: "#ED93B1",
      },
      fontFamily: {
        sans: ["Inter", "system-ui", "sans-serif"],
        mono: ["JetBrains Mono", "ui-monospace", "monospace"],
      },
    },
  },
  plugins: [],
};

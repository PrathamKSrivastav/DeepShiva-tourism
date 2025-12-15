/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{js,ts,jsx,tsx}"],
  darkMode: "class",
  theme: {
    extend: {
      colors: {
        // keep previous tokens if needed
        saffron: "#FF9933",
        "deep-blue": "#0F4C75",
        "mountain-green": "#2E7D32",
        "lotus-pink": "#F48FB1",
        "temple-gold": "#FFD700",

        // New polished dark theme tokens
        "dark-bg": "#061524", // almost-black navy
        "dark-surface": "#0C1522", // main panel surface
        "dark-elev": "#0F2130", // elevated/inner panels
        "dark-border": "#1F2D3A", // subtle border in dark
        "dark-muted": "#94A3B8", // muted text
        "dark-subtle": "#0B2533",

        // Accent gradient family
        "accent-indigo": "#6366F1", // indigo
        "accent-fuchsia": "#D946EF", // fuchsia
        "accent-rose": "#FB7185", // rose/red tint
      },
      fontFamily: {
        sans: ["Inter", "system-ui", "sans-serif"],
        heading: ["Poppins", "sans-serif"],
      },
    },
  },
  plugins: [],
};

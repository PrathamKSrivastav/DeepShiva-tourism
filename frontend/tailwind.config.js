/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        'saffron': '#FF9933',
        'deep-blue': '#0F4C75',
        'mountain-green': '#2E7D32',
        'lotus-pink': '#F48FB1',
        'temple-gold': '#FFD700',
      },
      fontFamily: {
        'sans': ['Inter', 'system-ui', 'sans-serif'],
        'heading': ['Poppins', 'sans-serif'],
      },
    },
  },
  plugins: [],
}

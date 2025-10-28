/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,jsx,ts,tsx}"
  ],
  theme: {
    extend: {
      colors: {
        uplift: {
          blue: "#0048E8",
          gold: "#FACC15",
          dark: "#000814",
          navy: "#001133"
        }
      }
    },
  },
  plugins: [],
}

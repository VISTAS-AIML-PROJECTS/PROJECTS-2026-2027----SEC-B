/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        brand: {
          dark: '#0b0f19',
          card: '#111827',
          border: '#1f2937',
          accent: '#3b82f6',
          green: '#10b981',
          red: '#ef4444',
          yellow: '#f59e0b',
        }
      }
    },
  },
  plugins: [],
}

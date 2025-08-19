
/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    "./employees/templates/**/*.html",
    "./assets/**/*.{js,css}",
  ],
  darkMode: 'class', // Enable dark mode with class strategy
  theme: {
    extend: {
      // Your theme extensions...
    },
  },
  plugins: [],
}
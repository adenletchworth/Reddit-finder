/** @type {import('tailwindcss').Config} */
module.exports = {
  mode: "jit",
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        primary: {
          light: '#cfe8ff', // Light Blue
          DEFAULT: '#007bff', // Blue
          dark: '#0056b3', // Dark Blue
        },
        secondary: {
          light: '#f1f1f1', // Light Gray
          DEFAULT: '#6c757d', // Gray
          dark: '#343a40', // Dark Gray
        },
        accent: {
          light: '#ffccd5', // Light Coral
          DEFAULT: '#ff6b6b', // Coral
          dark: '#c62e2e', // Dark Coral
        },
        white: '#ffffff', // Pure White
      },
    },
  },
  plugins: [],
}

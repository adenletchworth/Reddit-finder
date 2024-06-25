/** @type {import('tailwindcss').Config} */
module.exports = {
  mode: "jit",
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      boxShadow: {
        'custom': '0 10px 25px rgba(0, 0, 0, 0.5)', 
      },
      backgroundImage: {
        'svg-bg-1': "url('/src/assets/background1.svg')",
        'svg-bg-2': "url('/src/assets/background2.svg')",
        // 'svg-bg-3': "url('/src/assets/background3.svg')",
        // 'svg-bg-4': "url('/src/assets/background4.svg')",
        // 'svg-bg-5': "url('/src/assets/background5.svg')",
        // 'svg-bg-6': "url('/src/assets/background6.svg')",
        // 'svg-bg-7': "url('/src/assets/background7.svg')",
        // 'svg-bg-8': "url('/src/assets/background8.svg')",
        // 'svg-bg-9': "url('/src/assets/background9.svg')",
        // 'svg-bg-10': "url('/src/assets/background10.svg')",
      },
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
      fontFamily: {
        sans: ['Roboto', 'Arial', 'sans-serif'],
        serif: ['Merriweather', 'serif'],
      },
      keyframes: {
        backgroundFade: {
          '0%': { backgroundImage: "url('/src/assets/background1.svg')" },
          '10%': { backgroundImage: "url('/src/assets/background2.svg')" },
          // '20%': { backgroundImage: "url('/src/assets/background3.svg')" },
          // '30%': { backgroundImage: "url('/src/assets/background4.svg')" },
          // '40%': { backgroundImage: "url('/src/assets/background5.svg')" },
          // '50%': { backgroundImage: "url('/src/assets/background6.svg')" },
          // '60%': { backgroundImage: "url('/src/assets/background7.svg')" },
          // '70%': { backgroundImage: "url('/src/assets/background8.svg')" },
          // '80%': { backgroundImage: "url('/src/assets/background9.svg')" },
          // '90%': { backgroundImage: "url('/src/assets/background10.svg')" },
          // '100%': { backgroundImage: "url('/src/assets/background1.svg')" },
        },
      },
      animation: {
        backgroundFade: 'backgroundFade 30s infinite', // Adjust the duration as needed
      },
    },
  },
  plugins: [],
}

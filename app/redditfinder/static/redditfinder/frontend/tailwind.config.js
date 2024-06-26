// tailwind.config.js
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
        'prominent': '0 15px 30px rgba(0, 0, 0, 0.7)',  
      },
      backgroundImage: {
        'svg-bg-1': "url('/src/assets/background1.svg')",
      },
      colors: {
        primary: {
          light: '#cfe8ff',
          DEFAULT: '#007bff',
          dark: '#0056b3',
        },
        secondary: {
          light: '#f1f1f1',
          DEFAULT: '#6c757d',
          dark: '#343a40',
        },
        accent: {
          light: '#ffccd5',
          DEFAULT: '#ff6b6b',
          dark: '#c62e2e',
        },
        white: '#ffffff',
      },
      fontFamily: {
        sans: ['Roboto', 'Arial', 'sans-serif'],
        serif: ['Merriweather', 'serif'],
      },
      keyframes: {
        backgroundFade: {
          '0%': { backgroundImage: "url('/src/assets/background1.svg')" },
        },
      },
      animation: {
        backgroundFade: 'backgroundFade 30s infinite',
      },
    },
  },
  plugins: [],
}

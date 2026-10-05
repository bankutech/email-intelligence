/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{vue,js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        background: '#0a0a0c', // Deep solid military-grade dark
        surface: '#111216',
        surfaceElevated: '#1a1b21',
        border: '#272932',
        primary: '#3b82f6',
        success: '#10b981',
        warning: '#f59e0b',
        danger: '#ef4444',
        textMain: '#f8fafc',
        textMuted: '#94a3b8',
        cream: '#F1E9DA',
        ink: '#15120E',
        vermilion: '#FF4B1F',
        airmail: '#2B4BFF',
      },
      fontFamily: {
        sans: ['Inter', 'system-ui', 'sans-serif'],
        mono: ['"IBM Plex Mono"', 'JetBrains Mono', 'monospace'],
        serif: ['"Instrument Serif"', 'serif'],
        dispatchSans: ['"Instrument Sans"', 'sans-serif'],
        hand: ['"Caveat"', 'cursive'],
      }
    },
  },
  plugins: [],
}

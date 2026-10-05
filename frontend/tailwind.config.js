/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{vue,js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        cream: '#F1E9DA',
        ink: '#15120E',
        vermilion: '#FF4B1F',
        airmail: '#2B4BFF',
        success: '#16a34a',
        danger: '#dc2626',
      },
      fontFamily: {
        serif: ['"Instrument Serif"', 'serif'],
        dispatchSans: ['"Instrument Sans"', 'sans-serif'],
        mono: ['"IBM Plex Mono"', 'monospace'],
        hand: ['"Caveat"', 'cursive'],
      },
    },
  },
  plugins: [],
}

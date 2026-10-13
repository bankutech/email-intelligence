/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{vue,js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        nyalablue: '#0C49A2',
        nyalaslate: '#32373c',
        nyalawhite: '#ffffff',
        nyalbg: '#f8fafc',
        success: '#16a34a',
        danger: '#dc2626',
      },
      fontFamily: {
        sans: ['"Heebo"', 'sans-serif'],
        display: ['"Syne"', 'sans-serif'],
      },
      animation: {
        'slide-up': 'slideUp 0.8s ease-out forwards',
      },
      keyframes: {
        slideUp: {
          '0%': { transform: 'translateY(40px)', opacity: '0' },
          '100%': { transform: 'translateY(0)', opacity: '1' },
        },
      }
    },
  },
  plugins: [],
}

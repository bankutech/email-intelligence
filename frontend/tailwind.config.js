/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{vue,js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        canvas: {
          DEFAULT: '#fbfbfc',
          subtle: '#f7f8fa',
          muted: '#f1f3f5',
        },
        surface: {
          DEFAULT: '#ffffff',
          elevated: '#ffffff',
          sunken: '#f8fafc',
        },
        border: {
          subtle: '#ebeef2',
          DEFAULT: '#e2e6eb',
          strong: '#cbd3dc',
        },
        ink: {
          DEFAULT: '#111827',
          secondary: '#4b5563',
          muted: '#8590a2',
          faint: '#b3b9c5',
        },
        brand: {
          DEFAULT: '#4338ca',
          hover: '#3730a3',
          subtle: '#eef2ff',
          ring: 'rgba(67, 56, 202, 0.15)',
        },
        status: {
          success: '#059669',
          successBg: '#ecfdf5',
          successBorder: '#a7f3d0',
          warning: '#d97706',
          warningBg: '#fffbeb',
          warningBorder: '#fde68a',
          danger: '#e11d48',
          dangerBg: '#fff1f2',
          dangerBorder: '#fecdd3',
        }
      },
      fontFamily: {
        sans: ['"Instrument Sans"', '-apple-system', 'BlinkMacSystemFont', 'Inter', 'system-ui', 'sans-serif'],
        serif: ['"Instrument Serif"', 'Georgia', 'serif'],
        mono: ['"IBM Plex Mono"', 'ui-monospace', 'monospace'],
      },
      boxShadow: {
        'subtle': '0 1px 2px 0 rgba(0, 0, 0, 0.03), 0 1px 3px 0 rgba(0, 0, 0, 0.02)',
        'panel': '0 4px 6px -1px rgba(0, 0, 0, 0.04), 0 2px 4px -2px rgba(0, 0, 0, 0.03)',
        'float': '0 12px 24px -4px rgba(0, 0, 0, 0.06), 0 4px 8px -2px rgba(0, 0, 0, 0.03)',
      }
    },
  },
  plugins: [],
}

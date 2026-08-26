/** @type {import('tailwindcss').Config} */
export default {
  darkMode: 'class',
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        canvas: {
          light: '#FAF8F5',
          DEFAULT: '#FAF8F5',
          dark: '#0F1115',
        },
        surface: {
          light: '#FFFFFF',
          DEFAULT: '#FFFFFF',
          dark: '#181A20',
          subtle: {
            light: '#F5F2EB',
            DEFAULT: '#F5F2EB',
            dark: '#21252E',
          },
          sunken: {
            light: '#EDE8DE',
            DEFAULT: '#EDE8DE',
            dark: '#14161C',
          }
        },
        brand: {
          50: '#FBF7F4',
          100: '#F4ECE4',
          200: '#E8D6C7',
          300: '#D5B79F',
          400: '#BD9172',
          500: '#8C5E3C',
          600: '#7A4B2C',
          700: '#6B4226', // Core primary brand
          800: '#55331C',
          900: '#3D2312',
          DEFAULT: '#6B4226',
        },
        status: {
          critical: {
            text: '#DC2626',
            bg: '#FEF2F2',
            border: '#FECACA',
            darkText: '#F87171',
            darkBg: '#2D1212',
            darkBorder: '#7F1D1D',
          },
          warning: {
            text: '#D97706',
            bg: '#FFFBEB',
            border: '#FDE68A',
            darkText: '#FBBF24',
            darkBg: '#2D2008',
            darkBorder: '#78350F',
          },
          healthy: {
            text: '#16A34A',
            bg: '#F0FDF4',
            border: '#BBF7D0',
            darkText: '#4ADE80',
            darkBg: '#0D2818',
            darkBorder: '#14532D',
          },
          info: {
            text: '#2563EB',
            bg: '#EFF6FF',
            border: '#BFDBFE',
            darkText: '#60A5FA',
            darkBg: '#111D36',
            darkBorder: '#1E3A8A',
          },
        },
      },
      fontFamily: {
        sans: ['Inter', 'ui-sans-serif', 'system-ui', '-apple-system', 'BlinkMacSystemFont', '"Segoe UI"', 'Roboto', '"Helvetica Neue"', 'Arial', 'sans-serif'],
        mono: ['"JetBrains Mono"', 'ui-monospace', 'SFMono-Regular', 'Menlo', 'Monaco', 'Consolas', 'monospace'],
      },
      boxShadow: {
        'card': '0 1px 3px 0 rgba(0, 0, 0, 0.04), 0 1px 2px -1px rgba(0, 0, 0, 0.03)',
        'card-hover': '0 4px 12px 0 rgba(0, 0, 0, 0.08), 0 2px 4px -2px rgba(0, 0, 0, 0.04)',
        'panel': '0 1px 4px 0 rgba(0, 0, 0, 0.05)',
        'popover': '0 12px 30px -4px rgba(0, 0, 0, 0.12), 0 4px 10px -2px rgba(0, 0, 0, 0.06)',
        'elevated': '0 8px 24px -6px rgba(0, 0, 0, 0.1)',
        'btn': '0 1px 2px 0 rgba(0, 0, 0, 0.08)',
        'btn-hover': '0 3px 8px 0 rgba(0, 0, 0, 0.12)',
      },
      borderRadius: {
        'card': '12px',
        'panel': '16px',
        'btn': '10px',
      },
    },
  },
  plugins: [],
}

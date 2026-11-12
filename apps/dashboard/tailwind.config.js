/** @type {import('tailwindcss').Config} */
export default {
  darkMode: 'class',
  content: [
    './index.html',
    './src/**/*.{js,ts,jsx,tsx}',
    '../../packages/design-system/src/**/*.{js,ts,jsx,tsx}',
  ],
  theme: {
    extend: {
      colors: {
        brand: {
          navy: '#0B1026',
          space: '#0F1736',
          card: '#131C40',
          elevated: '#1A2552',
          cyan: '#00E5FF',
          violet: '#8B5CF6',
          silver: '#E2E6F0',
        },
      },
      fontFamily: {
        sans: ['"Inter"', 'system-ui', '-apple-system', 'sans-serif'],
        display: ['"Space Grotesk"', '"Inter"', 'system-ui', 'sans-serif'],
        mono: ['"JetBrains Mono"', 'Consolas', 'monospace'],
      },
      keyframes: {
        wave: {
          '0%, 100%': { transform: 'scaleY(0.35)' },
          '50%': { transform: 'scaleY(1)' },
        },
        glow: {
          '0%, 100%': { boxShadow: '0 0 14px rgba(0, 229, 255, 0.25)' },
          '50%': { boxShadow: '0 0 28px rgba(0, 229, 255, 0.55)' },
        },
      },
      animation: {
        wave: 'wave 1.2s ease-in-out infinite',
        glow: 'glow 2.4s ease-in-out infinite',
        'pulse-slow': 'pulse 3s cubic-bezier(0.4, 0, 0.6, 1) infinite',
      },
    },
  },
  plugins: [],
};

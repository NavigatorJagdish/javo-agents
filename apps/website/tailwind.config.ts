import type { Config } from 'tailwindcss';

const config: Config = {
  darkMode: 'class',
  content: [
    './src/pages/**/*.{js,ts,jsx,tsx,mdx}',
    './src/components/**/*.{js,ts,jsx,tsx,mdx}',
    './src/app/**/*.{js,ts,jsx,tsx,mdx}',
  ],
  theme: {
    extend: {
      colors: {
        navy: {
          DEFAULT: '#0B1026',
          50: '#1A2347',
          100: '#151D3D',
          200: '#111836',
          300: '#0E142E',
          400: '#0B1026',
          500: '#080C1D',
        },
        cyan: {
          DEFAULT: '#00E5FF',
          400: '#33ECFF',
          500: '#00E5FF',
          600: '#00B8D4',
          700: '#008BA3',
        },
        violet: {
          DEFAULT: '#8B5CF6',
          400: '#A78BFA',
          500: '#8B5CF6',
          600: '#7C3AED',
        },
        silver: {
          DEFAULT: '#E2E6F0',
          muted: '#94A3B8',
        },
      },
      fontFamily: {
        sans: ['Inter', 'Segoe UI', 'system-ui', '-apple-system', 'sans-serif'],
        display: ['Space Grotesk', 'Segoe UI', 'system-ui', 'sans-serif'],
        mono: ['JetBrains Mono', 'Cascadia Code', 'ui-monospace', 'SFMono-Regular', 'monospace'],
      },
      boxShadow: {
        glow: '0 0 30px -5px rgba(0, 229, 255, 0.25)',
        'glow-violet': '0 0 30px -5px rgba(139, 92, 246, 0.3)',
        card: '0 8px 32px rgba(5, 8, 22, 0.45)',
      },
      animation: {
        'pulse-slow': 'pulse 4s cubic-bezier(0.4, 0, 0.6, 1) infinite',
        'spin-slow': 'spin 24s linear infinite',
        float: 'float 6s ease-in-out infinite',
        wave: 'wave 1.4s ease-in-out infinite',
      },
      keyframes: {
        float: {
          '0%, 100%': { transform: 'translateY(0px)' },
          '50%': { transform: 'translateY(-8px)' },
        },
        wave: {
          '0%, 100%': { transform: 'scaleY(0.35)' },
          '50%': { transform: 'scaleY(1)' },
        },
      },
    },
  },
  plugins: [],
};

export default config;

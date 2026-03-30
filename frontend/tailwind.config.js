/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{js,ts,jsx,tsx}'],
  theme: {
    extend: {
      colors: {
        bg: {
          base: '#060608',
          surface: '#0e0f14',
          card: '#13141a',
          elevated: '#1a1b24',
        },
        brand: {
          DEFAULT: '#6366f1',
          glow: 'rgba(99,102,241,0.25)',
          dim: '#4f46e5',
        },
        green: {
          DEFAULT: '#10b981',
          glow: 'rgba(16,185,129,0.2)',
        },
        red: {
          DEFAULT: '#f43f5e',
          glow: 'rgba(244,63,94,0.2)',
        },
        amber: {
          DEFAULT: '#f59e0b',
        },
        text: {
          primary: '#f1f5f9',
          secondary: '#94a3b8',
          muted: '#475569',
        },
        border: 'rgba(255,255,255,0.07)',
      },
      fontFamily: {
        sans: ['Inter', 'system-ui', 'sans-serif'],
        mono: ['JetBrains Mono', 'monospace'],
      },
      animation: {
        'float': 'float 6s ease-in-out infinite',
        'pulse-slow': 'pulse 4s ease-in-out infinite',
        'gradient': 'gradient 8s ease infinite',
      },
      keyframes: {
        float: {
          '0%, 100%': { transform: 'translateY(0)' },
          '50%': { transform: 'translateY(-10px)' },
        },
        gradient: {
          '0%, 100%': { backgroundPosition: '0% 50%' },
          '50%': { backgroundPosition: '100% 50%' },
        },
      },
      backgroundSize: {
        '300%': '300%',
      },
    },
  },
  plugins: [],
}

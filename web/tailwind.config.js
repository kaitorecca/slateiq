/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{ts,tsx}'],
  theme: {
    extend: {
      colors: {
        void: '#08090B',
        cell: '#0E1013',
        panel: '#14171B',
        raise: '#1B1F25',
        line: '#252A31',
        ink: '#E9E7E2',
        dim: '#9AA1AB',
        faint: '#828A94',
        slate: { DEFAULT: '#F0B429', soft: '#8A6512' },
        circled: '#5FBF7F',
        ng: '#E0574F',
        hold: '#5B9FE3',
      },
      fontFamily: {
        sans: ['Inter var', 'Inter', 'system-ui', '-apple-system', 'Segoe UI', 'sans-serif'],
        mono: ['ui-monospace', 'SFMono-Regular', 'JetBrains Mono', 'Menlo', 'monospace'],
      },
      boxShadow: {
        lift: '0 1px 0 0 rgba(255,255,255,.04) inset, 0 12px 32px -12px rgba(0,0,0,.9)',
        glow: '0 0 0 1px rgba(240,180,41,.35), 0 0 28px -8px rgba(240,180,41,.45)',
      },
      keyframes: {
        rise: { '0%': { opacity: '0', transform: 'translateY(6px)' }, '100%': { opacity: '1', transform: 'none' } },
        blip: { '0%,100%': { opacity: '1' }, '50%': { opacity: '.25' } },
        sweep: { '0%': { transform: 'translateX(-100%)' }, '100%': { transform: 'translateX(100%)' } },
      },
      animation: {
        rise: 'rise .28s cubic-bezier(.2,.7,.3,1) both',
        blip: 'blip 1.6s ease-in-out infinite',
        sweep: 'sweep 1.6s linear infinite',
      },
    },
  },
  plugins: [],
}

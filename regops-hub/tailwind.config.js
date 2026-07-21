/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{ts,tsx}'],
  theme: {
    extend: {
      colors: {
        sidebar: {
          DEFAULT: '#12161c',
          hover: '#1c222b',
          active: '#232a35',
          border: '#232a35',
        },
        surface: {
          DEFAULT: '#ffffff',
          subtle: '#f6f7f9',
          muted: '#eef0f3',
        },
        ink: {
          DEFAULT: '#141821',
          muted: '#5b6472',
          faint: '#8892a0',
        },
        accent: {
          DEFAULT: '#2f6fed',
          hover: '#2560d4',
          subtle: '#e8f0fe',
        },
        severity: {
          p1: '#d92d20',
          p2: '#e0641f',
          p3: '#dc9c1a',
          p4: '#6b7280',
        },
        status: {
          good: '#0f9d58',
          warn: '#dc9c1a',
          info: '#2f6fed',
          bad: '#d92d20',
          neutral: '#8892a0',
        },
      },
      fontFamily: {
        sans: [
          'Inter',
          'ui-sans-serif',
          'system-ui',
          '-apple-system',
          'Segoe UI',
          'Roboto',
          'Helvetica Neue',
          'Arial',
          'sans-serif',
        ],
        mono: ['"JetBrains Mono"', 'ui-monospace', 'SFMono-Regular', 'Menlo', 'monospace'],
      },
      boxShadow: {
        panel: '-8px 0 24px -8px rgba(15, 23, 42, 0.15)',
        card: '0 1px 2px 0 rgba(15, 23, 42, 0.06), 0 1px 1px 0 rgba(15, 23, 42, 0.04)',
      },
    },
  },
  plugins: [],
};

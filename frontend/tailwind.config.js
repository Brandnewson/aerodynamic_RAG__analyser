/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,jsx}",
  ],
  theme: {
    extend: {
      colors: {
        cockpit: {
          bg: '#0a0e14',
          panel: '#111827',
          border: '#1f2937',
          highlight: '#374151',
          primary: '#ff9500',     // Amber HUD
          secondary: '#00d9ff',   // Cyan displays
          danger: '#ff4757',
          success: '#2ecc71',
          text: {
            primary: '#e5e7eb',
            secondary: '#9ca3af',
            muted: '#6b7280',
          }
        }
      },
      fontFamily: {
        display: ['Rajdhani', 'sans-serif'],
        body: ['Inter', 'system-ui', 'sans-serif'],
        mono: ['JetBrains Mono', 'monospace'],
      },
      animation: {
        'slide-in': 'slideIn 0.3s ease-out',
        'fade-in': 'fadeIn 0.4s ease-out',
        'pulse-slow': 'pulse 3s cubic-bezier(0.4, 0, 0.6, 1) infinite',
        'scan': 'scan 2s linear infinite',
      },
      keyframes: {
        slideIn: {
          '0%': { transform: 'translateX(-100%)', opacity: '0' },
          '100%': { transform: 'translateX(0)', opacity: '1' },
        },
        fadeIn: {
          '0%': { opacity: '0' },
          '100%': { opacity: '1' },
        },
        scan: {
          '0%': { transform: 'translateY(-100%)' },
          '100%': { transform: 'translateY(100%)' },
        }
      },
      backgroundImage: {
        'grid-pattern': "linear-gradient(to right, rgba(255, 149, 0, 0.05) 1px, transparent 1px), linear-gradient(to bottom, rgba(255, 149, 0, 0.05) 1px, transparent 1px)",
        'radial-cockpit': 'radial-gradient(circle at center, rgba(255, 149, 0, 0.03) 0%, transparent 70%)',
      },
      backgroundSize: {
        'grid': '40px 40px',
      }
    },
  },
  plugins: [],
}

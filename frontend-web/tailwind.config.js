/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{js,jsx}'],
  theme: {
    extend: {
      colors: {
        // Paleta VertexMascota (oscuro y tecnológico)
        vx: {
          bg: '#0A0E1A',        // fondo principal
          surface: '#0F1626',   // superficies/cards
          blue: '#3B82F6',      // azul principal
          blueLight: '#60A5FA', // azul claro
          muted: '#4A6B9A',     // texto secundario
          border: '#1E3A6B',    // bordes
          success: '#10B981',   // éxito
          danger: '#EF4444',
          warning: '#F59E0B',
        },
      },
      fontFamily: {
        sans: ['Inter', 'system-ui', 'sans-serif'],
      },
      boxShadow: {
        glow: '0 0 20px rgba(59,130,246,0.25)',
      },
    },
  },
  plugins: [],
};

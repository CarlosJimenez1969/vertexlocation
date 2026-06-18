// Configuración visual de cada estado de ánimo
export const MOOD_CONFIG = {
  feliz: { label: 'Feliz', emoji: '😄', color: '#10B981', desc: 'Actividad por encima del promedio.' },
  tranquilo: { label: 'Tranquilo', emoji: '😌', color: '#3B82F6', desc: 'En reposo, sin movimientos bruscos.' },
  ansioso: { label: 'Ansioso', emoji: '😰', color: '#F59E0B', desc: 'Movimiento errático y alta movilidad.' },
  asustado: { label: 'Asustado', emoji: '😱', color: '#EF4444', desc: 'Velocidad alta y fuera de la geocerca.' },
  posiblemente_enfermo: { label: 'Posiblemente enfermo', emoji: '🤒', color: '#A855F7', desc: 'Actividad muy baja por días.' },
  sin_datos: { label: 'Sin datos', emoji: '❓', color: '#4A6B9A', desc: 'Aún no hay suficientes lecturas.' },
};

export const moodOf = (estado) => MOOD_CONFIG[estado] || MOOD_CONFIG.sin_datos;

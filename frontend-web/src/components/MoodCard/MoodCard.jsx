import { moodOf } from './moodConfig';

/**
 * Tarjeta de estado de ánimo de la mascota.
 * @param {{mood: object, pet: object, onRecalculate: function}} props
 */
export default function MoodCard({ mood, pet, onRecalculate }) {
  const cfg = moodOf(mood?.estado);
  const conf = mood?.confianza != null ? Math.round(mood.confianza * 100) : 0;
  const hasFoto = Boolean(pet?.foto_url);

  return (
    <div className="vx-card p-5">
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-sm font-semibold text-vx-muted uppercase tracking-wider">
          Estado de ánimo
        </h3>
        {onRecalculate && (
          <button
            onClick={onRecalculate}
            className="text-xs text-vx-blueLight hover:text-vx-blue"
            title="Recalcular ahora"
          >
            ↻ Actualizar
          </button>
        )}
      </div>

      <div className="flex items-center gap-4">
        <div className="relative w-16 h-16 shrink-0">
          <div
            className="w-16 h-16 rounded-2xl overflow-hidden flex items-center justify-center text-3xl transition-all"
            style={{
              backgroundColor: `${cfg.color}22`,
              border: `2px solid ${cfg.color}`,
              boxShadow: `0 0 16px ${cfg.color}66`,
            }}
          >
            {hasFoto ? (
              <img src={pet.foto_url} alt={pet?.nombre} className="w-full h-full object-cover" />
            ) : (
              cfg.emoji
            )}
          </div>
          {/* Insignia con el emoji del estado (solo si hay foto) */}
          {hasFoto && (
            <span
              className="absolute -bottom-1.5 -right-1.5 w-7 h-7 rounded-full flex items-center justify-center text-base border-2 border-vx-surface"
              style={{ backgroundColor: cfg.color }}
              title={cfg.label}
            >
              {cfg.emoji}
            </span>
          )}
        </div>
        <div className="flex-1">
          <p className="text-xl font-bold" style={{ color: cfg.color }}>
            {cfg.label}
          </p>
          <p className="text-xs text-vx-muted mt-0.5">{cfg.desc}</p>
        </div>
      </div>

      {/* Barra de confianza */}
      {mood && (
        <div className="mt-4">
          <div className="flex justify-between text-xs text-vx-muted mb-1">
            <span>Confianza</span>
            <span>{conf}%</span>
          </div>
          <div className="h-2 rounded-full bg-vx-bg overflow-hidden">
            <div
              className="h-full rounded-full transition-all"
              style={{ width: `${conf}%`, backgroundColor: cfg.color }}
            />
          </div>
        </div>
      )}

      {/* Métricas */}
      {mood && (
        <div className="grid grid-cols-3 gap-2 mt-4 text-center">
          <Metric label="Actividad" value={`${Math.round(mood.actividad_pct ?? 0)}%`} />
          <Metric label="Reposo" value={`${Math.round(mood.reposo_pct ?? 0)}%`} />
          <Metric label="Vel. máx" value={`${Math.round(mood.velocidad_max ?? 0)} km/h`} />
        </div>
      )}
    </div>
  );
}

function Metric({ label, value }) {
  return (
    <div className="bg-vx-bg rounded-xl py-2 border border-vx-border">
      <p className="text-sm font-bold text-white">{value}</p>
      <p className="text-[10px] text-vx-muted uppercase">{label}</p>
    </div>
  );
}

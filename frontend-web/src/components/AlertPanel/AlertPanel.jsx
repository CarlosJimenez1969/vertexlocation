const ICONS = {
  salida_geocerca: '🚨',
  entrada_geocerca: '✅',
  bateria_baja: '🔋',
  animo_enfermo: '🤒',
  animo_asustado: '😱',
  animo_ansioso: '😰',
  velocidad_alta: '💨',
  dispositivo_offline: '📡',
};

function timeAgo(iso) {
  const diff = (Date.now() - new Date(iso).getTime()) / 1000;
  if (diff < 60) return 'hace instantes';
  if (diff < 3600) return `hace ${Math.floor(diff / 60)} min`;
  if (diff < 86400) return `hace ${Math.floor(diff / 3600)} h`;
  return `hace ${Math.floor(diff / 86400)} d`;
}

/**
 * Panel de alertas recientes.
 */
export default function AlertPanel({ alerts = [], onMarkRead }) {
  return (
    <div className="vx-card p-5 flex flex-col h-full">
      <div className="flex items-center justify-between mb-3">
        <h3 className="text-sm font-semibold text-vx-muted uppercase tracking-wider">Alertas</h3>
        {alerts.filter((a) => !a.leida).length > 0 && (
          <span className="text-xs bg-vx-danger/20 text-vx-danger px-2 py-0.5 rounded-full">
            {alerts.filter((a) => !a.leida).length} nuevas
          </span>
        )}
      </div>

      <div className="flex-1 overflow-y-auto space-y-2 pr-1">
        {alerts.length === 0 && (
          <p className="text-sm text-vx-muted text-center py-8">Sin alertas recientes 🎉</p>
        )}
        {alerts.map((a) => (
          <div
            key={a.id}
            className={`p-3 rounded-xl border transition-colors ${
              a.leida ? 'border-vx-border bg-vx-bg/40' : 'border-vx-blue/40 bg-vx-blue/10'
            }`}
          >
            <div className="flex items-start gap-3">
              <span className="text-lg">{ICONS[a.tipo] || '🔔'}</span>
              <div className="flex-1 min-w-0">
                <p className="text-sm font-semibold text-white truncate">{a.titulo}</p>
                {a.mensaje && <p className="text-xs text-vx-muted mt-0.5">{a.mensaje}</p>}
                <div className="flex items-center gap-2 mt-1">
                  <span className="text-[10px] text-vx-muted">{timeAgo(a.creado_en)}</span>
                  {a.enviada_whatsapp && (
                    <span className="text-[10px] text-vx-success">· WhatsApp ✓</span>
                  )}
                </div>
              </div>
              {!a.leida && (
                <button
                  onClick={() => onMarkRead(a.id)}
                  className="text-[10px] text-vx-blueLight hover:text-vx-blue shrink-0"
                >
                  marcar
                </button>
              )}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}

import {
  ResponsiveContainer, AreaChart, Area, XAxis, YAxis, Tooltip, CartesianGrid,
} from 'recharts';

/**
 * Gráfica de actividad semanal (pasos / distancia) con Recharts.
 * @param {{data: Array}} props
 */
export default function ActivityChart({ data = [] }) {
  const chartData = data.map((d) => ({
    dia: d.fecha ? new Date(d.fecha).toLocaleDateString('es-EC', { weekday: 'short' }) : '',
    pasos: d.pasos,
    distancia: Number(d.distancia_km),
  }));

  return (
    <div className="vx-card p-5">
      <h3 className="text-sm font-semibold text-vx-muted uppercase tracking-wider mb-4">
        Actividad semanal
      </h3>
      <div className="h-48">
        <ResponsiveContainer width="100%" height="100%">
          <AreaChart data={chartData}>
            <defs>
              <linearGradient id="gPasos" x1="0" y1="0" x2="0" y2="1">
                <stop offset="0%" stopColor="#3B82F6" stopOpacity={0.5} />
                <stop offset="100%" stopColor="#3B82F6" stopOpacity={0} />
              </linearGradient>
            </defs>
            <CartesianGrid strokeDasharray="3 3" stroke="#1E3A6B" />
            <XAxis dataKey="dia" stroke="#4A6B9A" fontSize={11} />
            <YAxis stroke="#4A6B9A" fontSize={11} />
            <Tooltip
              contentStyle={{
                background: '#0F1626',
                border: '1px solid #1E3A6B',
                borderRadius: 12,
                color: '#fff',
              }}
            />
            <Area
              type="monotone"
              dataKey="pasos"
              stroke="#3B82F6"
              strokeWidth={2}
              fill="url(#gPasos)"
              name="Pasos"
            />
          </AreaChart>
        </ResponsiveContainer>
      </div>

      {/* Resumen numérico */}
      <div className="grid grid-cols-4 gap-2 mt-4 text-center">
        <Stat label="Pasos" value={sum(data, 'pasos')} />
        <Stat label="Distancia" value={`${sum(data, 'distancia_km').toFixed(1)} km`} />
        <Stat label="Calorías" value={Math.round(sum(data, 'calorias'))} />
        <Stat label="Activo" value={`${Math.round(sum(data, 'minutos_activo') / 60)} h`} />
      </div>
    </div>
  );
}

const sum = (arr, k) => arr.reduce((a, b) => a + Number(b[k] || 0), 0);

function Stat({ label, value }) {
  return (
    <div className="bg-vx-bg rounded-xl py-2 border border-vx-border">
      <p className="text-sm font-bold text-white">{value}</p>
      <p className="text-[10px] text-vx-muted uppercase">{label}</p>
    </div>
  );
}

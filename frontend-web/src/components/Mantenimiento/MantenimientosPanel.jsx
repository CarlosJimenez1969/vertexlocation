import { useEffect, useState } from 'react';
import { maintenanceApi, vehiclesApi } from '../../api/client';

const BADGE = {
  vencido:   { txt: 'Vencido',   cls: 'bg-vx-danger/20 text-vx-danger',  icon: '🔴' },
  proximo:   { txt: 'Próximo',   cls: 'bg-vx-warning/20 text-vx-warning', icon: '🟡' },
  vigente:   { txt: 'Vigente',   cls: 'bg-vx-success/20 text-vx-success', icon: '🟢' },
  realizado: { txt: 'Hecho',     cls: 'bg-vx-muted/20 text-vx-muted',     icon: '✅' },
};
const TIPOS = ['Cambio de aceite', 'Rotación de llantas', 'Revisión de frenos',
  'Cambio de filtros', 'Batería', 'Alineación y balanceo', 'Revisión general'];
const VACIO = { tipo: '', fecha_proxima: '', km_proximo: '', intervalo_dias: '', intervalo_km: '', notas: '' };

export default function MantenimientosPanel({ vehiculo, onVehUpdate }) {
  const [items, setItems] = useState([]);
  const [form, setForm] = useState(VACIO);
  const [mostrarForm, setMostrarForm] = useState(false);
  const [km, setKm] = useState(vehiculo.km_actual ?? '');
  const [msg, setMsg] = useState('');

  const cargar = () => maintenanceApi.list(vehiculo.id).then((r) => setItems(r.data)).catch(() => {});
  useEffect(() => { cargar(); setKm(vehiculo.km_actual ?? ''); /* eslint-disable-next-line */ }, [vehiculo.id]);

  const ch = (e) => setForm({ ...form, [e.target.name]: e.target.value });

  const guardarKm = async () => {
    const n = parseInt(km, 10);
    if (Number.isNaN(n)) return;
    try {
      const r = await vehiclesApi.update(vehiculo.id, { km_actual: n });
      onVehUpdate?.(r.data);
      cargar();
    } catch { /* noop */ }
  };

  const crear = async (e) => {
    e.preventDefault(); setMsg('');
    if (!form.fecha_proxima && !form.km_proximo) { setMsg('Indica una fecha o un kilometraje.'); return; }
    const p = { vehiculo_id: vehiculo.id, tipo: form.tipo, notas: form.notas || null };
    if (form.fecha_proxima) p.fecha_proxima = form.fecha_proxima;
    if (form.km_proximo) p.km_proximo = parseInt(form.km_proximo, 10);
    if (form.intervalo_dias) p.intervalo_dias = parseInt(form.intervalo_dias, 10);
    if (form.intervalo_km) p.intervalo_km = parseInt(form.intervalo_km, 10);
    try {
      await maintenanceApi.create(p);
      setForm(VACIO); setMostrarForm(false); cargar();
    } catch (err) { setMsg(err.response?.data?.detail || 'No se pudo crear.'); }
  };

  const hecho = async (id) => { await maintenanceApi.done(id); cargar(); };
  const borrar = async (id) => { if (window.confirm('¿Eliminar este mantenimiento?')) { await maintenanceApi.remove(id); cargar(); } };

  return (
    <div className="h-full overflow-y-auto space-y-3 pr-1">
      {/* Odómetro */}
      <div className="vx-card p-3 flex items-center justify-between gap-2">
        <div>
          <p className="text-xs text-vx-muted">Odómetro actual</p>
          <div className="flex items-center gap-2">
            <input type="number" min="0" value={km} onChange={(e) => setKm(e.target.value)}
              className="w-28 bg-vx-bg border border-vx-border rounded px-2 py-1 text-white" placeholder="—" />
            <span className="text-sm text-vx-muted">km</span>
          </div>
        </div>
        <button onClick={guardarKm} className="vx-btn text-sm py-1.5">Guardar km</button>
      </div>

      {/* Botón agregar */}
      {!mostrarForm && (
        <button onClick={() => setMostrarForm(true)} className="vx-btn w-full text-sm py-2">+ Agregar mantenimiento</button>
      )}

      {/* Formulario */}
      {mostrarForm && (
        <form onSubmit={crear} className="vx-card p-3 space-y-2">
          <input name="tipo" list="tipos-mant" required value={form.tipo} onChange={ch}
            placeholder="Tipo (ej. Cambio de aceite)" className="vx-input text-sm" />
          <datalist id="tipos-mant">{TIPOS.map((t) => <option key={t} value={t} />)}</datalist>
          <div className="grid grid-cols-2 gap-2">
            <div>
              <label className="text-[11px] text-vx-muted">Vence (fecha)</label>
              <input type="date" name="fecha_proxima" value={form.fecha_proxima} onChange={ch} className="vx-input text-sm" />
            </div>
            <div>
              <label className="text-[11px] text-vx-muted">Vence (km)</label>
              <input type="number" min="0" name="km_proximo" value={form.km_proximo} onChange={ch} placeholder="ej. 50000" className="vx-input text-sm" />
            </div>
          </div>
          <div className="grid grid-cols-2 gap-2">
            <div>
              <label className="text-[11px] text-vx-muted">Repetir cada (días)</label>
              <input type="number" min="1" name="intervalo_dias" value={form.intervalo_dias} onChange={ch} placeholder="opcional" className="vx-input text-sm" />
            </div>
            <div>
              <label className="text-[11px] text-vx-muted">Repetir cada (km)</label>
              <input type="number" min="1" name="intervalo_km" value={form.intervalo_km} onChange={ch} placeholder="opcional" className="vx-input text-sm" />
            </div>
          </div>
          <input name="notas" value={form.notas} onChange={ch} placeholder="Notas (opcional)" className="vx-input text-sm" />
          {msg && <p className="text-xs text-vx-danger">{msg}</p>}
          <div className="flex gap-2">
            <button className="vx-btn flex-1 text-sm py-1.5">Guardar</button>
            <button type="button" onClick={() => { setMostrarForm(false); setForm(VACIO); setMsg(''); }} className="text-sm text-vx-muted px-3">Cancelar</button>
          </div>
        </form>
      )}

      {/* Lista */}
      {items.length === 0 && <p className="text-center text-vx-muted text-sm py-4">Sin mantenimientos registrados.</p>}
      {items.map((m) => {
        const b = BADGE[m.estado] || BADGE.vigente;
        return (
          <div key={m.id} className="vx-card p-3">
            <div className="flex items-start justify-between gap-2">
              <div className="min-w-0">
                <p className="font-semibold truncate">{m.tipo}</p>
                <p className="text-xs text-vx-muted">
                  {m.fecha_proxima ? `📅 ${new Date(m.fecha_proxima + 'T00:00:00').toLocaleDateString('es-EC')}` : ''}
                  {m.fecha_proxima && m.km_proximo != null ? ' · ' : ''}
                  {m.km_proximo != null ? `🚗 ${m.km_proximo.toLocaleString()} km` : ''}
                </p>
                <p className="text-[11px] text-vx-muted">
                  {m.estado !== 'realizado' && m.dias_restantes != null && `${m.dias_restantes >= 0 ? `faltan ${m.dias_restantes} días` : `vencido hace ${-m.dias_restantes} días`}`}
                  {m.estado !== 'realizado' && m.km_restantes != null && ` · ${m.km_restantes > 0 ? `faltan ${m.km_restantes.toLocaleString()} km` : `pasado por ${(-m.km_restantes).toLocaleString()} km`}`}
                  {(m.intervalo_dias || m.intervalo_km) ? ' · 🔁 recurrente' : ''}
                </p>
                {m.notas && <p className="text-[11px] text-vx-muted italic">{m.notas}</p>}
              </div>
              <span className={`shrink-0 text-[10px] px-2 py-0.5 rounded-full ${b.cls}`}>{b.icon} {b.txt}</span>
            </div>
            <div className="flex gap-3 mt-2">
              {m.estado !== 'realizado' && (
                <button onClick={() => hecho(m.id)} className="text-xs text-vx-success hover:underline">✓ Marcar realizado</button>
              )}
              <button onClick={() => borrar(m.id)} className="text-xs text-vx-danger hover:underline">Eliminar</button>
            </div>
          </div>
        );
      })}
    </div>
  );
}

import { useEffect, useState } from 'react';
import { devicesApi, petsApi, vehiclesApi } from '../../api/client';

const OPERADORES = ['CNT', 'Claro', 'Movistar'];
const VACIO = { imei: '', nombre: '', sim_operador: '' };

export default function DispositivosPanel() {
  const [devices, setDevices] = useState([]);
  const [pets, setPets] = useState([]);
  const [vehiculos, setVehiculos] = useState([]);
  const [form, setForm] = useState(VACIO);
  const [editId, setEditId] = useState(null); // null = registrar; id = editar
  const [error, setError] = useState('');
  const [okMsg, setOkMsg] = useState('');
  const [saving, setSaving] = useState(false);

  const cargar = () => {
    devicesApi.list().then((r) => setDevices(r.data)).catch(() => {});
    petsApi.list().then((r) => setPets(r.data)).catch(() => {});
    vehiclesApi.list().then((r) => setVehiculos(r.data)).catch(() => {});
  };
  useEffect(() => { cargar(); }, []);

  const onChange = (e) => setForm({ ...form, [e.target.name]: e.target.value });

  const cancelar = () => { setEditId(null); setForm(VACIO); setError(''); setOkMsg(''); };

  const editar = (d) => {
    setEditId(d.id);
    setForm({ imei: d.imei, nombre: d.nombre || '', sim_operador: d.sim_operador || '' });
    setError(''); setOkMsg('');
    window.scrollTo({ top: 0, behavior: 'smooth' }); // llevar al formulario
  };

  const guardar = async (e) => {
    e.preventDefault();
    setError(''); setOkMsg(''); setSaving(true);
    try {
      const payload = { ...form };
      Object.keys(payload).forEach((k) => { if (payload[k] === '') delete payload[k]; });
      if (editId) {
        await devicesApi.update(editId, payload);
        setOkMsg('Dispositivo actualizado.');
      } else {
        await devicesApi.register(payload);
        setOkMsg('Dispositivo registrado.');
      }
      setForm(VACIO);
      setEditId(null);
      cargar();
    } catch (err) {
      setError(err.response?.data?.detail || 'No se pudo guardar el dispositivo.');
    } finally {
      setSaving(false);
    }
  };

  const asignar = async (deviceId, value) => {
    try {
      if (!value) await devicesApi.unassign(deviceId);
      else {
        const [tipo, targetId] = value.split(':');
        await devicesApi.assign(deviceId, tipo, targetId);
      }
      cargar();
    } catch (err) {
      setError(err.response?.data?.detail || 'No se pudo asignar.');
    }
  };

  const eliminar = async (deviceId) => {
    if (!window.confirm('¿Eliminar este dispositivo? Se quitará también de Traccar.')) return;
    try {
      await devicesApi.remove(deviceId);
      if (editId === deviceId) cancelar();
      cargar();
    } catch { /* noop */ }
  };

  return (
    <div className="h-full overflow-y-auto p-1">
      <h2 className="text-xl font-bold mb-1">Dispositivos</h2>
      <p className="text-xs text-vx-muted mb-4">
        Registra tus rastreadores GPS y asígnalos a una mascota o vehículo.
      </p>

      <div className="grid grid-cols-12 gap-4">
        {/* Formulario (registrar O editar — el mismo) */}
        <form
          onSubmit={guardar}
          className={`col-span-12 lg:col-span-4 vx-card p-5 space-y-3 h-fit ${editId ? 'border-vx-blue shadow-glow' : ''}`}
        >
          <h3 className="text-sm font-semibold text-vx-muted uppercase tracking-wider">
            {editId ? '✏️ Editar dispositivo' : 'Registrar dispositivo'}
          </h3>
          <input className="vx-input" name="imei" placeholder="IMEI / ID del rastreador" required
            value={form.imei} onChange={onChange} />
          <input className="vx-input" name="nombre" placeholder="Nombre (opcional)"
            value={form.nombre} onChange={onChange} />
          <select className="vx-input" name="sim_operador" value={form.sim_operador} onChange={onChange}>
            <option value="">Operador SIM (opcional)</option>
            {OPERADORES.map((o) => <option key={o} value={o}>{o}</option>)}
          </select>
          {okMsg && <p className="text-sm text-vx-success">{okMsg}</p>}
          {error && <p className="text-sm text-vx-danger">{error}</p>}
          <div className="flex gap-2">
            <button className="vx-btn flex-1" disabled={saving}>
              {saving ? 'Guardando…' : editId ? 'Guardar cambios' : 'Registrar'}
            </button>
            {editId && (
              <button type="button" onClick={cancelar} className="text-sm text-vx-muted px-3">
                Cancelar
              </button>
            )}
          </div>
          <p className="text-[10px] text-vx-muted leading-relaxed">
            ⚠️ El ID debe coincidir <b>exacto</b> con el que transmite el rastreador (ojo con ceros iniciales).
            Al editar el ID, se sincroniza también en Traccar.
          </p>
        </form>

        {/* Lista */}
        <div className="col-span-12 lg:col-span-8 space-y-3">
          {devices.length === 0 && (
            <div className="vx-card p-8 text-center text-vx-muted">
              Aún no tienes dispositivos. Registra el primero con el formulario.
            </div>
          )}
          {devices.map((d) => (
            <div
              key={d.id}
              className={`vx-card p-4 flex flex-col sm:flex-row sm:items-center gap-3 ${editId === d.id ? 'ring-1 ring-vx-blue' : ''}`}
            >
              <div className="flex items-center gap-3 flex-1 min-w-0">
                <span className={`inline-block w-2.5 h-2.5 rounded-full shrink-0 ${d.online ? 'bg-vx-success' : 'bg-vx-muted'}`} />
                <div className="min-w-0">
                  <p className="font-bold truncate">🛰️ {d.nombre || d.imei}</p>
                  <p className="text-xs text-vx-muted truncate">
                    ID: {d.imei}{d.sim_operador ? ` · ${d.sim_operador}` : ''}
                    {d.bateria != null ? ` · 🔋 ${d.bateria}%` : ''} · {d.online ? 'En línea' : 'Desconectado'}
                  </p>
                  <p className="text-xs mt-0.5">
                    {d.asignado ? (
                      <span className="text-vx-blueLight">
                        {d.asignado.tipo === 'mascota' ? '🐶' : '🚗'} Asignado a: <b>{d.asignado.nombre}</b>
                      </span>
                    ) : (
                      <span className="text-vx-muted">Sin asignar</span>
                    )}
                  </p>
                </div>
              </div>
              <div className="flex items-center gap-2 shrink-0">
                <select
                  className="vx-input !w-auto text-xs py-1.5"
                  value={d.asignado ? `${d.asignado.tipo}:${d.asignado.id}` : ''}
                  onChange={(e) => asignar(d.id, e.target.value)}
                >
                  <option value="">— Sin asignar —</option>
                  {pets.length > 0 && (
                    <optgroup label="Mascotas">
                      {pets.map((p) => <option key={p.id} value={`mascota:${p.id}`}>🐶 {p.nombre}</option>)}
                    </optgroup>
                  )}
                  {vehiculos.length > 0 && (
                    <optgroup label="Vehículos">
                      {vehiculos.map((v) => <option key={v.id} value={`vehiculo:${v.id}`}>🚗 {v.alias}</option>)}
                    </optgroup>
                  )}
                </select>
                <button onClick={() => editar(d)} className="text-xs text-vx-blueLight hover:text-vx-blue">
                  Editar
                </button>
                <button onClick={() => eliminar(d.id)} className="text-xs text-vx-danger hover:underline">
                  Eliminar
                </button>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}

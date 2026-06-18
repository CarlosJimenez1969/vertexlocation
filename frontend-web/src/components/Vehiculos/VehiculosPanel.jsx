import { useEffect, useRef, useState } from 'react';
import { vehiclesApi } from '../../api/client';
import VehiculoTracker from './VehiculoTracker';
import { useAuth } from '../../context/AuthContext';

const TIPOS = [
  { v: 'auto', l: 'Auto' },
  { v: 'camioneta', l: 'Camioneta' },
  { v: 'moto', l: 'Moto' },
  { v: 'otro', l: 'Otro' },
];
const COMBUSTIBLES = ['gasolina', 'diesel', 'electrico', 'hibrido'];
const EMOJI = { auto: '🚗', camioneta: '🛻', moto: '🏍️', otro: '🚙' };

const VACIO = {
  alias: '', placa: '', marca: '', modelo: '', anio: '', color: '',
  tipo: 'auto', tipo_combustible: '', limite_velocidad: '',
  tiene_inmovilizador: false,
};

export default function VehiculosPanel({ onChanged, lastMessage }) {
  const { isAdmin } = useAuth();
  const readOnly = !isAdmin; // el cliente solo ve y rastrea sus vehículos
  const [vehiculos, setVehiculos] = useState([]);
  const [form, setForm] = useState(VACIO);
  const [error, setError] = useState('');
  const [okMsg, setOkMsg] = useState('');
  const [saving, setSaving] = useState(false);
  const [bust, setBust] = useState({});
  const [tracking, setTracking] = useState(null); // vehículo en vista de mapa

  const cargar = () => vehiclesApi.list().then((r) => setVehiculos(r.data));
  useEffect(() => { cargar(); }, []);

  // Vista de rastreo en vivo de un vehículo
  if (tracking) {
    return (
      <VehiculoTracker
        vehiculo={tracking}
        lastMessage={lastMessage}
        onBack={() => setTracking(null)}
      />
    );
  }

  const onChange = (e) =>
    setForm({ ...form, [e.target.name]: e.target.type === 'checkbox' ? e.target.checked : e.target.value });

  const crear = async (e) => {
    e.preventDefault();
    setError(''); setOkMsg(''); setSaving(true);
    try {
      const payload = { ...form };
      Object.keys(payload).forEach((k) => { if (payload[k] === '') delete payload[k]; });
      if (payload.anio) payload.anio = parseInt(payload.anio, 10);
      if (payload.limite_velocidad) payload.limite_velocidad = parseInt(payload.limite_velocidad, 10);
      await vehiclesApi.create(payload);
      setOkMsg(`Vehículo "${form.alias}" registrado.`);
      setForm(VACIO);
      cargar();
      onChanged?.();
    } catch (err) {
      setError(err.response?.data?.detail || 'No se pudo registrar el vehículo.');
    } finally {
      setSaving(false);
    }
  };

  return (
    <div className="h-full overflow-y-auto p-1">
      <h2 className="text-xl font-bold mb-1">Mis vehículos</h2>
      <p className="text-xs text-vx-muted mb-4">
        {readOnly
          ? 'Tus vehículos. Pulsa "Rastrear" para verlos en el mapa y usar el anti-robo.'
          : 'Registra tus autos o motos y su rastreador GPS para localizarlos en caso de robo.'}
      </p>

      <div className="grid grid-cols-12 gap-4">
        {/* Formulario (solo admin) */}
        {!readOnly && (
        <form onSubmit={crear} className="col-span-12 lg:col-span-4 vx-card p-5 space-y-3 h-fit">
          <h3 className="text-sm font-semibold text-vx-muted uppercase tracking-wider">Nuevo vehículo</h3>
          <input className="vx-input" name="alias" placeholder="Alias (ej. Mi Corolla)" required
            value={form.alias} onChange={onChange} />
          <div className="grid grid-cols-2 gap-2">
            <input className="vx-input" name="placa" placeholder="Placa" value={form.placa} onChange={onChange} />
            <select className="vx-input" name="tipo" value={form.tipo} onChange={onChange}>
              {TIPOS.map((t) => <option key={t.v} value={t.v}>{t.l}</option>)}
            </select>
          </div>
          <div className="grid grid-cols-2 gap-2">
            <input className="vx-input" name="marca" placeholder="Marca" value={form.marca} onChange={onChange} />
            <input className="vx-input" name="modelo" placeholder="Modelo" value={form.modelo} onChange={onChange} />
          </div>
          <div className="grid grid-cols-2 gap-2">
            <input className="vx-input" name="anio" type="number" placeholder="Año" value={form.anio} onChange={onChange} />
            <input className="vx-input" name="color" placeholder="Color" value={form.color} onChange={onChange} />
          </div>
          <div className="grid grid-cols-2 gap-2">
            <select className="vx-input" name="tipo_combustible" value={form.tipo_combustible} onChange={onChange}>
              <option value="">Combustible</option>
              {COMBUSTIBLES.map((c) => <option key={c} value={c}>{c[0].toUpperCase() + c.slice(1)}</option>)}
            </select>
            <input className="vx-input" name="limite_velocidad" type="number" min="1"
              placeholder="Límite km/h" value={form.limite_velocidad} onChange={onChange} />
          </div>
          <label className="flex items-center gap-2 text-xs text-vx-muted cursor-pointer">
            <input type="checkbox" name="tiene_inmovilizador" checked={form.tiene_inmovilizador} onChange={onChange} />
            Tiene inmovilizador (corte de motor)
          </label>
          {okMsg && <p className="text-sm text-vx-success">{okMsg}</p>}
          {error && <p className="text-sm text-vx-danger">{error}</p>}
          <button className="vx-btn w-full" disabled={saving}>
            {saving ? 'Guardando…' : 'Registrar vehículo'}
          </button>
        </form>
        )}

        {/* Listado */}
        <div className={`col-span-12 ${readOnly ? '' : 'lg:col-span-8'} grid sm:grid-cols-2 gap-4 content-start`}>
          {vehiculos.length === 0 && (
            <div className="col-span-full vx-card p-8 text-center text-vx-muted">
              {readOnly ? 'No tienes vehículos registrados todavía.' : 'Aún no tienes vehículos. Registra el primero con el formulario.'}
            </div>
          )}
          {vehiculos.map((v) => (
            <VehicleCard key={v.id} v={v} bust={bust[v.id]} readOnly={readOnly}
              onTrack={() => setTracking(v)}
              onChanged={(id) => { setBust((b) => ({ ...b, [id]: Date.now() })); cargar(); onChanged?.(); }} />
          ))}
        </div>
      </div>
    </div>
  );
}

function VehicleCard({ v, bust, onChanged, onTrack, readOnly }) {
  const fileRef = useRef(null);
  const [subiendo, setSubiendo] = useState(false);
  const [err, setErr] = useState('');
  const src = v.foto_url ? `${v.foto_url}${bust ? `?x=${bust}` : ''}` : null;

  const subir = async (e) => {
    const file = e.target.files?.[0];
    if (!file) return;
    setErr(''); setSubiendo(true);
    try {
      await vehiclesApi.uploadPhoto(v.id, file);
      onChanged?.(v.id);
    } catch (ex) {
      setErr(ex.response?.data?.detail || 'No se pudo subir la imagen.');
    } finally {
      setSubiendo(false); e.target.value = '';
    }
  };

  return (
    <div className="vx-card p-4 flex gap-4 items-center">
      <div className="w-20 h-20 rounded-2xl overflow-hidden border border-vx-border bg-vx-bg flex items-center justify-center shrink-0">
        {src ? <img src={src} alt={v.alias} className="w-full h-full object-cover" />
             : <span className="text-3xl">{EMOJI[v.tipo] || '🚗'}</span>}
      </div>
      <div className="flex-1 min-w-0">
        <p className="font-bold truncate">{v.alias}</p>
        <p className="text-xs text-vx-muted truncate">
          {[v.marca, v.modelo, v.anio].filter(Boolean).join(' ') || v.tipo}
          {v.placa ? ` · ${v.placa}` : ''}
        </p>
        <p className="text-[10px] text-vx-muted mt-0.5">
          {v.dispositivo_id ? '🛰️ Con rastreador' : '— Sin rastreador'}
        </p>
        <input ref={fileRef} type="file" accept="image/png,image/jpeg,image/webp" className="hidden" onChange={subir} />
        <div className="mt-1 flex items-center gap-3">
          <button onClick={onTrack} className="text-xs font-semibold text-vx-blueLight hover:text-vx-blue">
            📍 Rastrear
          </button>
          {!readOnly && (
            <button onClick={() => fileRef.current?.click()} disabled={subiendo}
              className="text-xs text-vx-muted hover:text-white">
              {subiendo ? 'Subiendo…' : v.foto_url ? '↻ Foto' : '📷 Foto'}
            </button>
          )}
        </div>
        {err && <p className="text-xs text-vx-danger mt-1">{err}</p>}
      </div>
    </div>
  );
}

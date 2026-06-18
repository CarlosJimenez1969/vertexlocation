import { useEffect, useMemo, useState } from 'react';
import { adminApi } from '../../api/client';
import { useAuth } from '../../context/AuthContext';

const TABS = [
  { id: 'usuarios', label: '👤 Usuarios' },
  { id: 'mascotas', label: '🐶 Mascotas' },
  { id: 'vehiculos', label: '🚗 Vehículos' },
  { id: 'dispositivos', label: '🛰️ Dispositivos' },
];

export default function AdminPanel() {
  const { user, logout } = useAuth();
  const [tab, setTab] = useState('usuarios');
  const [users, setUsers] = useState([]);
  const [pets, setPets] = useState([]);
  const [vehicles, setVehicles] = useState([]);
  const [devices, setDevices] = useState([]);

  const clientes = useMemo(() => users.filter((u) => u.rol === 'cliente'), [users]);

  const cargar = () => {
    adminApi.users.list().then((r) => setUsers(r.data)).catch(() => {});
    adminApi.pets.list().then((r) => setPets(r.data)).catch(() => {});
    adminApi.vehicles.list().then((r) => setVehicles(r.data)).catch(() => {});
    adminApi.devices.list().then((r) => setDevices(r.data)).catch(() => {});
  };
  useEffect(() => { cargar(); }, []);

  return (
    <div className="h-full flex flex-col bg-vx-bg">
      <div className="flex items-center justify-between px-6 py-3 border-b border-vx-border">
        <div className="flex items-center gap-3">
          <div className="w-9 h-9 rounded-lg bg-vx-blue flex items-center justify-center text-lg">📍</div>
          <div>
            <h1 className="font-extrabold leading-tight">Vertex<span className="text-vx-blue">Location</span> · Admin</h1>
            <p className="text-[10px] text-vx-muted">{user?.email}</p>
          </div>
        </div>
        <button onClick={logout} className="text-xs text-vx-danger hover:underline">Cerrar sesión</button>
      </div>

      <div className="flex gap-1 px-6 pt-3 border-b border-vx-border">
        {TABS.map((t) => (
          <button key={t.id} onClick={() => setTab(t.id)}
            className={`px-4 py-2 text-sm rounded-t-lg transition-colors ${tab === t.id ? 'bg-vx-surface text-white border-b-2 border-vx-blue' : 'text-vx-muted hover:text-white'}`}>
            {t.label}
          </button>
        ))}
      </div>

      <div className="flex-1 overflow-y-auto p-6">
        {tab === 'usuarios' && <UsuariosTab users={users} onChanged={cargar} />}
        {tab === 'mascotas' && <MascotasTab pets={pets} clientes={clientes} onChanged={cargar} />}
        {tab === 'vehiculos' && <VehiculosTab vehicles={vehicles} clientes={clientes} onChanged={cargar} />}
        {tab === 'dispositivos' && (
          <DispositivosTab devices={devices} pets={pets} vehicles={vehicles} clientes={clientes} onChanged={cargar} />
        )}
      </div>
    </div>
  );
}

/* ---------- helpers de UI ---------- */
function Campo(props) {
  return <input {...props} className={`vx-input ${props.className || ''}`} />;
}
function Mensaje({ error, ok }) {
  return (
    <>
      {ok && <p className="text-sm text-vx-success">{ok}</p>}
      {error && <p className="text-sm text-vx-danger">{error}</p>}
    </>
  );
}
/* Botón de guardado con barra de avance mientras la petición está en curso */
function BtnGuardar({ loading, children, className = '' }) {
  return (
    <div className={`flex-1 ${className}`}>
      <button type="submit" disabled={loading} className="vx-btn w-full disabled:opacity-70 disabled:cursor-wait">
        {loading ? 'Guardando…' : children}
      </button>
      {loading && <div className="vx-progress mt-1.5"><span /></div>}
    </div>
  );
}

/* ==================== USUARIOS ==================== */
function UsuariosTab({ users, onChanged }) {
  const VACIO = { nombre: '', email: '', telefono: '', ciudad: '', activo: true };
  const [form, setForm] = useState(VACIO);
  const [editId, setEditId] = useState(null);
  const [saving, setSaving] = useState(false);
  const [msg, setMsg] = useState({ error: '', ok: '' });
  const ch = (e) => setForm({ ...form, [e.target.name]: e.target.type === 'checkbox' ? e.target.checked : e.target.value });
  const cancelar = () => { setEditId(null); setForm(VACIO); setMsg({ error: '', ok: '' }); };

  const editar = (u) => {
    setEditId(u.id);
    setForm({ nombre: u.nombre, email: u.email, telefono: u.telefono || '', ciudad: u.ciudad || '', activo: u.activo });
    window.scrollTo({ top: 0, behavior: 'smooth' });
  };

  const guardar = async (e) => {
    e.preventDefault(); setMsg({ error: '', ok: '' }); setSaving(true);
    try {
      if (editId) {
        await adminApi.users.update(editId, { nombre: form.nombre, telefono: form.telefono, ciudad: form.ciudad, activo: form.activo });
        setMsg({ ok: 'Datos actualizados.', error: '' });
      } else {
        const p = { nombre: form.nombre, email: form.email, telefono: form.telefono, ciudad: form.ciudad };
        Object.keys(p).forEach((k) => p[k] === '' && delete p[k]);
        await adminApi.users.create(p);
        setMsg({ ok: 'Cliente creado. Se le envió un correo para crear su contraseña.', error: '' });
      }
      setForm(VACIO); setEditId(null); onChanged();
    } catch (err) { setMsg({ error: err.response?.data?.detail || 'No se pudo guardar.', ok: '' }); }
    finally { setSaving(false); }
  };

  return (
    <div className="grid grid-cols-12 gap-4">
      <form onSubmit={guardar} className={`col-span-12 lg:col-span-4 vx-card p-5 space-y-3 h-fit ${editId ? 'border-vx-blue shadow-glow' : ''}`}>
        <h3 className="text-sm font-semibold text-vx-muted uppercase tracking-wider">{editId ? '✏️ Editar usuario' : 'Nuevo cliente'}</h3>
        <Campo name="nombre" placeholder="Nombre completo" required value={form.nombre} onChange={ch} />
        <Campo type="email" name="email" placeholder="correo@ejemplo.com" required value={form.email} onChange={ch} disabled={!!editId} />
        <Campo name="telefono" placeholder="WhatsApp +593… (opcional)" value={form.telefono} onChange={ch} />
        <Campo name="ciudad" placeholder="Ciudad" value={form.ciudad} onChange={ch} />
        {editId && (
          <label className="flex items-center gap-2 text-xs text-vx-muted cursor-pointer">
            <input type="checkbox" name="activo" checked={form.activo} onChange={ch} /> Cuenta activa
          </label>
        )}
        <Mensaje {...msg} />
        <div className="flex gap-2 items-start">
          <BtnGuardar loading={saving}>{editId ? 'Guardar cambios' : 'Crear cliente'}</BtnGuardar>
          {editId && <button type="button" onClick={cancelar} disabled={saving} className="text-sm text-vx-muted px-3 py-2">Cancelar</button>}
        </div>
        {!editId && <p className="text-[10px] text-vx-muted">📧 Al crear, se le envía un correo para que <b>cree su propia contraseña</b>. Tú no la defines.</p>}
        {editId && <p className="text-[10px] text-vx-muted">El correo no se puede cambiar (es su usuario de acceso).</p>}
      </form>

      <div className="col-span-12 lg:col-span-8 space-y-2">
        {users.map((u) => (
          <div key={u.id} className={`vx-card p-3 flex items-center justify-between ${editId === u.id ? 'ring-1 ring-vx-blue' : ''}`}>
            <div className="min-w-0">
              <p className="font-bold truncate">{u.nombre} {u.rol === 'admin' && <span className="text-[10px] text-vx-warning">· ADMIN</span>}</p>
              <p className="text-xs text-vx-muted truncate">{u.email}{u.telefono ? ` · ${u.telefono}` : ''}{u.ciudad ? ` · ${u.ciudad}` : ''}</p>
            </div>
            <div className="flex items-center gap-3 shrink-0">
              <span className={`text-[10px] px-2 py-0.5 rounded-full ${u.activo ? 'bg-vx-success/20 text-vx-success' : 'bg-vx-muted/20 text-vx-muted'}`}>
                {u.activo ? 'activo' : 'inactivo'}
              </span>
              {u.rol !== 'admin' && (
                <button onClick={() => editar(u)} className="text-xs text-vx-blueLight hover:text-vx-blue">Editar</button>
              )}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}

/* ==================== MASCOTAS ==================== */
function MascotasTab({ pets, clientes, onChanged }) {
  const ESPECIES = ['perro', 'gato', 'otro'];
  const SEXOS = ['macho', 'hembra', 'desconocido'];
  const VACIO = { usuario_id: '', nombre: '', especie: 'perro', raza: '', sexo: 'desconocido', peso_kg: '' };
  const [form, setForm] = useState(VACIO);
  const [editId, setEditId] = useState(null);
  const [saving, setSaving] = useState(false);
  const [msg, setMsg] = useState({ error: '', ok: '' });
  const ch = (e) => setForm({ ...form, [e.target.name]: e.target.value });
  const cancelar = () => { setEditId(null); setForm(VACIO); setMsg({ error: '', ok: '' }); };

  const editar = (p) => {
    setEditId(p.id);
    setForm({ usuario_id: p.usuario_id, nombre: p.nombre, especie: p.especie, raza: p.raza || '', sexo: p.sexo, peso_kg: p.peso_kg || '' });
    window.scrollTo({ top: 0, behavior: 'smooth' });
  };

  const guardar = async (e) => {
    e.preventDefault(); setMsg({ error: '', ok: '' });
    if (!editId && !form.usuario_id) { setMsg({ error: 'Selecciona el cliente dueño.', ok: '' }); return; }
    setSaving(true);
    try {
      const p = { nombre: form.nombre, especie: form.especie, raza: form.raza, sexo: form.sexo };
      if (form.peso_kg !== '') p.peso_kg = parseFloat(form.peso_kg);
      Object.keys(p).forEach((k) => p[k] === '' && delete p[k]);
      if (editId) await adminApi.pets.update(editId, p);
      else await adminApi.pets.create(form.usuario_id, p);
      setMsg({ ok: editId ? 'Mascota actualizada.' : 'Mascota creada.', error: '' });
      setForm(VACIO); setEditId(null); onChanged();
    } catch (err) { setMsg({ error: err.response?.data?.detail || 'Error al guardar.', ok: '' }); }
    finally { setSaving(false); }
  };

  const eliminar = async (id) => { if (window.confirm('¿Eliminar esta mascota?')) { await adminApi.pets.remove(id); if (editId === id) cancelar(); onChanged(); } };

  return (
    <div className="grid grid-cols-12 gap-4">
      <form onSubmit={guardar} className={`col-span-12 lg:col-span-4 vx-card p-5 space-y-3 h-fit ${editId ? 'border-vx-blue shadow-glow' : ''}`}>
        <h3 className="text-sm font-semibold text-vx-muted uppercase tracking-wider">{editId ? '✏️ Editar mascota' : 'Nueva mascota'}</h3>
        {!editId && (
          <select name="usuario_id" className="vx-input" value={form.usuario_id} onChange={ch} required>
            <option value="">— Cliente dueño —</option>
            {clientes.map((c) => <option key={c.id} value={c.id}>{c.nombre} ({c.email})</option>)}
          </select>
        )}
        <Campo name="nombre" placeholder="Nombre" required value={form.nombre} onChange={ch} />
        <div className="grid grid-cols-2 gap-2">
          <select name="especie" className="vx-input" value={form.especie} onChange={ch} disabled={!!editId}>
            {ESPECIES.map((e) => <option key={e} value={e}>{e[0].toUpperCase() + e.slice(1)}</option>)}
          </select>
          <select name="sexo" className="vx-input" value={form.sexo} onChange={ch}>
            {SEXOS.map((s) => <option key={s} value={s}>{s[0].toUpperCase() + s.slice(1)}</option>)}
          </select>
        </div>
        <div className="grid grid-cols-2 gap-2">
          <Campo name="raza" placeholder="Raza" value={form.raza} onChange={ch} />
          <Campo name="peso_kg" type="number" step="0.1" placeholder="Peso kg" value={form.peso_kg} onChange={ch} />
        </div>
        <Mensaje {...msg} />
        <div className="flex gap-2 items-start">
          <BtnGuardar loading={saving}>{editId ? 'Guardar cambios' : 'Crear mascota'}</BtnGuardar>
          {editId && <button type="button" onClick={cancelar} disabled={saving} className="text-sm text-vx-muted px-3 py-2">Cancelar</button>}
        </div>
      </form>

      <div className="col-span-12 lg:col-span-8 space-y-2">
        {pets.length === 0 && <div className="vx-card p-6 text-center text-vx-muted">Sin mascotas.</div>}
        {pets.map((p) => (
          <div key={p.id} className={`vx-card p-3 flex items-center justify-between ${editId === p.id ? 'ring-1 ring-vx-blue' : ''}`}>
            <div className="min-w-0">
              <p className="font-bold truncate">🐶 {p.nombre} <span className="text-xs text-vx-muted">· {p.especie}{p.raza ? ` · ${p.raza}` : ''}</span></p>
              <p className="text-xs text-vx-muted truncate">Dueño: <b className="text-vx-blueLight">{p.dueno?.nombre || '—'}</b>{p.dispositivo_id ? ' · 🛰️ con dispositivo' : ' · sin dispositivo'}</p>
            </div>
            <div className="flex gap-2 shrink-0">
              <button onClick={() => editar(p)} className="text-xs text-vx-blueLight hover:text-vx-blue">Editar</button>
              <button onClick={() => eliminar(p.id)} className="text-xs text-vx-danger hover:underline">Eliminar</button>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}

/* ==================== VEHICULOS ==================== */
function VehiculosTab({ vehicles, clientes, onChanged }) {
  const TIPOS = ['auto', 'camioneta', 'moto', 'otro'];
  const VACIO = { usuario_id: '', alias: '', placa: '', marca: '', modelo: '', anio: '', color: '', tipo: 'auto', tiene_inmovilizador: false };
  const [form, setForm] = useState(VACIO);
  const [editId, setEditId] = useState(null);
  const [saving, setSaving] = useState(false);
  const [msg, setMsg] = useState({ error: '', ok: '' });
  const ch = (e) => setForm({ ...form, [e.target.name]: e.target.type === 'checkbox' ? e.target.checked : e.target.value });
  const cancelar = () => { setEditId(null); setForm(VACIO); setMsg({ error: '', ok: '' }); };

  const editar = (v) => {
    setEditId(v.id);
    setForm({ usuario_id: v.usuario_id, alias: v.alias, placa: v.placa || '', marca: v.marca || '', modelo: v.modelo || '', anio: v.anio || '', color: v.color || '', tipo: v.tipo, tiene_inmovilizador: v.tiene_inmovilizador });
    window.scrollTo({ top: 0, behavior: 'smooth' });
  };

  const guardar = async (e) => {
    e.preventDefault(); setMsg({ error: '', ok: '' });
    if (!editId && !form.usuario_id) { setMsg({ error: 'Selecciona el cliente dueño.', ok: '' }); return; }
    setSaving(true);
    try {
      const p = { alias: form.alias, placa: form.placa, marca: form.marca, modelo: form.modelo, color: form.color, tipo: form.tipo, tiene_inmovilizador: form.tiene_inmovilizador };
      if (form.anio !== '') p.anio = parseInt(form.anio, 10);
      Object.keys(p).forEach((k) => p[k] === '' && delete p[k]);
      if (editId) await adminApi.vehicles.update(editId, p);
      else await adminApi.vehicles.create(form.usuario_id, p);
      setMsg({ ok: editId ? 'Vehículo actualizado.' : 'Vehículo creado.', error: '' });
      setForm(VACIO); setEditId(null); onChanged();
    } catch (err) { setMsg({ error: err.response?.data?.detail || 'Error al guardar.', ok: '' }); }
    finally { setSaving(false); }
  };

  const eliminar = async (id) => { if (window.confirm('¿Eliminar este vehículo?')) { await adminApi.vehicles.remove(id); if (editId === id) cancelar(); onChanged(); } };

  return (
    <div className="grid grid-cols-12 gap-4">
      <form onSubmit={guardar} className={`col-span-12 lg:col-span-4 vx-card p-5 space-y-3 h-fit ${editId ? 'border-vx-blue shadow-glow' : ''}`}>
        <h3 className="text-sm font-semibold text-vx-muted uppercase tracking-wider">{editId ? '✏️ Editar vehículo' : 'Nuevo vehículo'}</h3>
        {!editId && (
          <select name="usuario_id" className="vx-input" value={form.usuario_id} onChange={ch} required>
            <option value="">— Cliente dueño —</option>
            {clientes.map((c) => <option key={c.id} value={c.id}>{c.nombre} ({c.email})</option>)}
          </select>
        )}
        <Campo name="alias" placeholder="Alias (ej. Mi Corolla)" required value={form.alias} onChange={ch} />
        <div className="grid grid-cols-2 gap-2">
          <Campo name="placa" placeholder="Placa" value={form.placa} onChange={ch} />
          <select name="tipo" className="vx-input" value={form.tipo} onChange={ch}>
            {TIPOS.map((t) => <option key={t} value={t}>{t[0].toUpperCase() + t.slice(1)}</option>)}
          </select>
        </div>
        <div className="grid grid-cols-2 gap-2">
          <Campo name="marca" placeholder="Marca" value={form.marca} onChange={ch} />
          <Campo name="modelo" placeholder="Modelo" value={form.modelo} onChange={ch} />
        </div>
        <div className="grid grid-cols-2 gap-2">
          <Campo name="anio" type="number" placeholder="Año" value={form.anio} onChange={ch} />
          <Campo name="color" placeholder="Color" value={form.color} onChange={ch} />
        </div>
        <label className="flex items-center gap-2 text-xs text-vx-muted cursor-pointer">
          <input type="checkbox" name="tiene_inmovilizador" checked={form.tiene_inmovilizador} onChange={ch} />
          Tiene inmovilizador (corte de motor)
        </label>
        <Mensaje {...msg} />
        <div className="flex gap-2 items-start">
          <BtnGuardar loading={saving}>{editId ? 'Guardar cambios' : 'Crear vehículo'}</BtnGuardar>
          {editId && <button type="button" onClick={cancelar} disabled={saving} className="text-sm text-vx-muted px-3 py-2">Cancelar</button>}
        </div>
      </form>

      <div className="col-span-12 lg:col-span-8 space-y-2">
        {vehicles.length === 0 && <div className="vx-card p-6 text-center text-vx-muted">Sin vehículos.</div>}
        {vehicles.map((v) => (
          <div key={v.id} className={`vx-card p-3 flex items-center justify-between ${editId === v.id ? 'ring-1 ring-vx-blue' : ''}`}>
            <div className="min-w-0">
              <p className="font-bold truncate">🚗 {v.alias} <span className="text-xs text-vx-muted">· {[v.marca, v.modelo, v.anio].filter(Boolean).join(' ')}{v.placa ? ` · ${v.placa}` : ''}</span></p>
              <p className="text-xs text-vx-muted truncate">Dueño: <b className="text-vx-blueLight">{v.dueno?.nombre || '—'}</b>{v.dispositivo_id ? ' · 🛰️ con dispositivo' : ' · sin dispositivo'}{v.tiene_inmovilizador ? ' · 🛑 inmovilizador' : ''}</p>
            </div>
            <div className="flex gap-2 shrink-0">
              <button onClick={() => editar(v)} className="text-xs text-vx-blueLight hover:text-vx-blue">Editar</button>
              <button onClick={() => eliminar(v.id)} className="text-xs text-vx-danger hover:underline">Eliminar</button>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}

/* ==================== DISPOSITIVOS ==================== */
function DispositivosTab({ devices, pets, vehicles, clientes, onChanged }) {
  const OPERADORES = ['CNT', 'Claro', 'Movistar'];
  const VACIO = { imei: '', nombre: '', sim_operador: '' };
  const [form, setForm] = useState(VACIO);
  const [editId, setEditId] = useState(null);
  const [saving, setSaving] = useState(false);
  const [asignandoId, setAsignandoId] = useState(null);
  const [msg, setMsg] = useState({ error: '', ok: '' });
  const ch = (e) => setForm({ ...form, [e.target.name]: e.target.value });
  const cancelar = () => { setEditId(null); setForm(VACIO); setMsg({ error: '', ok: '' }); };

  const editar = (d) => {
    setEditId(d.id);
    setForm({ imei: d.imei, nombre: d.nombre || '', sim_operador: d.sim_operador || '' });
    window.scrollTo({ top: 0, behavior: 'smooth' });
  };

  const guardar = async (e) => {
    e.preventDefault(); setMsg({ error: '', ok: '' }); setSaving(true);
    try {
      const p = { imei: form.imei, nombre: form.nombre, sim_operador: form.sim_operador };
      Object.keys(p).forEach((k) => p[k] === '' && delete p[k]);
      if (editId) await adminApi.devices.update(editId, p);
      else await adminApi.devices.create(p);
      setMsg({ ok: editId ? 'Dispositivo actualizado.' : 'Dispositivo registrado. Asígnalo a una mascota o vehículo.', error: '' });
      setForm(VACIO); setEditId(null); onChanged();
    } catch (err) { setMsg({ error: err.response?.data?.detail || 'Error al guardar.', ok: '' }); }
    finally { setSaving(false); }
  };

  const asignar = async (d, value) => {
    setMsg({ error: '', ok: '' }); setAsignandoId(d.id);
    try {
      if (!value) await adminApi.devices.unassign(d.id);
      else { const [tipo, id] = value.split(':'); await adminApi.devices.assign(d.id, tipo, id); }
      onChanged();
    } catch (err) { setMsg({ error: err.response?.data?.detail || 'No se pudo asignar.', ok: '' }); }
    finally { setAsignandoId(null); }
  };

  const eliminar = async (id) => { if (window.confirm('¿Eliminar este dispositivo? Se borra también de Traccar.')) { await adminApi.devices.remove(id); if (editId === id) cancelar(); onChanged(); } };

  return (
    <div className="grid grid-cols-12 gap-4">
      <form onSubmit={guardar} className={`col-span-12 lg:col-span-4 vx-card p-5 space-y-3 h-fit ${editId ? 'border-vx-blue shadow-glow' : ''}`}>
        <h3 className="text-sm font-semibold text-vx-muted uppercase tracking-wider">{editId ? '✏️ Editar dispositivo' : 'Registrar dispositivo'}</h3>
        <Campo name="imei" placeholder="IMEI / ID del rastreador" required value={form.imei} onChange={ch} />
        <Campo name="nombre" placeholder="Nombre (opcional)" value={form.nombre} onChange={ch} />
        <select name="sim_operador" className="vx-input" value={form.sim_operador} onChange={ch}>
          <option value="">Operador SIM (opcional)</option>
          {OPERADORES.map((o) => <option key={o} value={o}>{o}</option>)}
        </select>
        <Mensaje {...msg} />
        <div className="flex gap-2 items-start">
          <BtnGuardar loading={saving}>{editId ? 'Guardar cambios' : 'Registrar'}</BtnGuardar>
          {editId && <button type="button" onClick={cancelar} disabled={saving} className="text-sm text-vx-muted px-3 py-2">Cancelar</button>}
        </div>
        <p className="text-[10px] text-vx-muted">⚠️ El ID debe coincidir exacto con el que transmite el rastreador (ojo con ceros iniciales).</p>
        <p className="text-[10px] text-vx-muted">👤 No se elige cliente: el dispositivo <b>hereda el dueño</b> de la mascota o vehículo al que lo asignes.</p>
      </form>

      <div className="col-span-12 lg:col-span-8 space-y-2">
        {devices.length === 0 && <div className="vx-card p-6 text-center text-vx-muted">Sin dispositivos.</div>}
        {devices.map((d) => {
          // Dueños que tienen al menos una mascota o vehículo (para agrupar el desplegable).
          const dueños = clientes.filter((c) =>
            pets.some((p) => p.usuario_id === c.id) || vehicles.some((v) => v.usuario_id === c.id)
          );
          return (
            <div key={d.id} className={`vx-card p-3 flex flex-col sm:flex-row sm:items-center gap-2 ${editId === d.id ? 'ring-1 ring-vx-blue' : ''}`}>
              <div className="flex items-center gap-2 flex-1 min-w-0">
                <span className={`inline-block w-2.5 h-2.5 rounded-full shrink-0 ${d.online ? 'bg-vx-success' : 'bg-vx-muted'}`} />
                <div className="min-w-0">
                  <p className="font-bold truncate">🛰️ {d.nombre || d.imei}</p>
                  <p className="text-xs text-vx-muted truncate">ID: {d.imei} · Dueño: <b className="text-vx-blueLight">{d.dueno?.nombre || '—'}</b>{d.bateria != null ? ` · 🔋 ${d.bateria}%` : ''}</p>
                  <p className="text-xs">{d.asignado ? <span className="text-vx-blueLight">{d.asignado.tipo === 'mascota' ? '🐶' : '🚗'} {d.asignado.nombre}</span> : <span className="text-vx-muted">Sin asignar</span>}</p>
                </div>
              </div>
              <div className="flex items-center gap-2 shrink-0">
                <div className="flex flex-col">
                  <select className="vx-input !w-auto text-xs py-1.5" disabled={asignandoId === d.id}
                    value={d.asignado ? `${d.asignado.tipo}:${d.asignado.id}` : ''} onChange={(e) => asignar(d, e.target.value)}>
                    <option value="">{asignandoId === d.id ? 'Asignando…' : '— Asignar a —'}</option>
                    {dueños.map((c) => {
                      const cp = pets.filter((p) => p.usuario_id === c.id);
                      const cv = vehicles.filter((v) => v.usuario_id === c.id);
                      return (
                        <optgroup key={c.id} label={c.nombre}>
                          {cp.map((p) => <option key={p.id} value={`mascota:${p.id}`}>🐶 {p.nombre}</option>)}
                          {cv.map((v) => <option key={v.id} value={`vehiculo:${v.id}`}>🚗 {v.alias}</option>)}
                        </optgroup>
                      );
                    })}
                  </select>
                  {asignandoId === d.id && <div className="vx-progress mt-1"><span /></div>}
                </div>
                <button onClick={() => editar(d)} className="text-xs text-vx-blueLight hover:text-vx-blue">Editar</button>
                <button onClick={() => eliminar(d.id)} className="text-xs text-vx-danger hover:underline">Eliminar</button>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}

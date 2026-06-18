import { useRef, useState } from 'react';
import { petsApi } from '../../api/client';
import { useAuth } from '../../context/AuthContext';

const ESPECIES = ['perro', 'gato', 'otro'];
const SEXOS = [
  { v: 'macho', l: 'Macho' },
  { v: 'hembra', l: 'Hembra' },
  { v: 'desconocido', l: 'Desconocido' },
];

const VACIO = { nombre: '', especie: 'perro', raza: '', sexo: 'desconocido', peso_kg: '' };

/**
 * Sección "Mis mascotas": crear mascota y gestionar su foto.
 * @param {{pets: array, onChanged: function}} props
 */
export default function MascotasPanel({ pets = [], onChanged }) {
  const { isAdmin } = useAuth();
  const readOnly = !isAdmin; // el cliente solo ve sus mascotas
  const [form, setForm] = useState(VACIO);
  const [error, setError] = useState('');
  const [okMsg, setOkMsg] = useState('');
  const [saving, setSaving] = useState(false);
  // Cache-buster por mascota para refrescar la <img> tras subir foto.
  const [bust, setBust] = useState({});

  const onChange = (e) => setForm({ ...form, [e.target.name]: e.target.value });

  const crear = async (e) => {
    e.preventDefault();
    setError('');
    setOkMsg('');
    setSaving(true);
    try {
      const payload = { ...form };
      if (payload.peso_kg === '') delete payload.peso_kg;
      else payload.peso_kg = parseFloat(payload.peso_kg);
      if (payload.raza === '') delete payload.raza;
      await petsApi.create(payload);
      setOkMsg(`Mascota "${form.nombre}" creada.`);
      setForm(VACIO);
      onChanged?.();
    } catch (err) {
      setError(err.response?.data?.detail || 'No se pudo crear la mascota.');
    } finally {
      setSaving(false);
    }
  };

  return (
    <div className="h-full overflow-y-auto p-1">
      <h2 className="text-xl font-bold mb-1">Mis mascotas</h2>
      <p className="text-xs text-vx-muted mb-4">
        {readOnly
          ? 'Tus mascotas registradas. Para cambios, contacta a tu proveedor.'
          : 'Crea tus mascotas y súbeles una foto. El estado de ánimo usará esa imagen.'}
      </p>

      <div className="grid grid-cols-12 gap-4">
        {/* Formulario de creación (solo admin) */}
        {!readOnly && (
        <form onSubmit={crear} className="col-span-12 lg:col-span-4 vx-card p-5 space-y-3 h-fit">
          <h3 className="text-sm font-semibold text-vx-muted uppercase tracking-wider">
            Nueva mascota
          </h3>
          <input
            className="vx-input" name="nombre" placeholder="Nombre" required
            value={form.nombre} onChange={onChange}
          />
          <div className="grid grid-cols-2 gap-2">
            <select className="vx-input" name="especie" value={form.especie} onChange={onChange}>
              {ESPECIES.map((e) => <option key={e} value={e}>{e[0].toUpperCase() + e.slice(1)}</option>)}
            </select>
            <select className="vx-input" name="sexo" value={form.sexo} onChange={onChange}>
              {SEXOS.map((s) => <option key={s.v} value={s.v}>{s.l}</option>)}
            </select>
          </div>
          <input
            className="vx-input" name="raza" placeholder="Raza (opcional)"
            value={form.raza} onChange={onChange}
          />
          <input
            className="vx-input" name="peso_kg" type="number" step="0.1" min="0"
            placeholder="Peso kg (opcional)" value={form.peso_kg} onChange={onChange}
          />
          {okMsg && <p className="text-sm text-vx-success">{okMsg}</p>}
          {error && <p className="text-sm text-vx-danger">{error}</p>}
          <button className="vx-btn w-full" disabled={saving}>
            {saving ? 'Guardando…' : 'Crear mascota'}
          </button>
        </form>
        )}

        {/* Listado de mascotas con su foto */}
        <div className={`col-span-12 ${readOnly ? '' : 'lg:col-span-8'} grid sm:grid-cols-2 gap-4 content-start`}>
          {pets.length === 0 && (
            <div className="col-span-full vx-card p-8 text-center text-vx-muted">
              {readOnly ? 'No tienes mascotas registradas todavía.' : 'Aún no tienes mascotas. Crea la primera con el formulario.'}
            </div>
          )}
          {pets.map((p) => (
            <PetCard
              key={p.id}
              pet={p}
              readOnly={readOnly}
              bust={bust[p.id]}
              onUploaded={(petId) => {
                setBust((b) => ({ ...b, [petId]: Date.now() }));
                onChanged?.();
              }}
            />
          ))}
        </div>
      </div>
    </div>
  );
}

function PetCard({ pet, bust, onUploaded, readOnly }) {
  const fileRef = useRef(null);
  const [subiendo, setSubiendo] = useState(false);
  const [err, setErr] = useState('');

  const src = pet.foto_url ? `${pet.foto_url}${bust ? `?v=${bust}` : ''}` : null;

  const elegir = () => fileRef.current?.click();

  const subir = async (e) => {
    const file = e.target.files?.[0];
    if (!file) return;
    setErr('');
    setSubiendo(true);
    try {
      await petsApi.uploadPhoto(pet.id, file);
      onUploaded?.(pet.id);
    } catch (ex) {
      setErr(ex.response?.data?.detail || 'No se pudo subir la imagen.');
    } finally {
      setSubiendo(false);
      e.target.value = '';
    }
  };

  return (
    <div className="vx-card p-4 flex gap-4 items-center">
      <div className="w-20 h-20 rounded-2xl overflow-hidden border border-vx-border bg-vx-bg flex items-center justify-center shrink-0">
        {src ? (
          <img src={src} alt={pet.nombre} className="w-full h-full object-cover" />
        ) : (
          <span className="text-3xl">{pet.especie === 'gato' ? '🐱' : '🐶'}</span>
        )}
      </div>
      <div className="flex-1 min-w-0">
        <p className="font-bold truncate">{pet.nombre}</p>
        <p className="text-xs text-vx-muted truncate">
          {pet.especie}{pet.raza ? ` · ${pet.raza}` : ''}
        </p>
        {!readOnly && (
          <>
            <input
              ref={fileRef} type="file" accept="image/png,image/jpeg,image/webp"
              className="hidden" onChange={subir}
            />
            <button
              onClick={elegir} disabled={subiendo}
              className="mt-2 text-xs text-vx-blueLight hover:text-vx-blue"
            >
              {subiendo ? 'Subiendo…' : pet.foto_url ? '↻ Cambiar foto' : '📷 Subir foto'}
            </button>
            {err && <p className="text-xs text-vx-danger mt-1">{err}</p>}
          </>
        )}
      </div>
    </div>
  );
}

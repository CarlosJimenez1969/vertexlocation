import { useAuth } from '../../context/AuthContext';

const NAV = [
  { id: 'mapa', label: 'Mapa en vivo', icon: '🗺️' },
  { id: 'mascotas', label: 'Mis mascotas', icon: '🐕' },
  { id: 'vehiculos', label: 'Mis vehículos', icon: '🚗' },
  { id: 'geocercas', label: 'Geocercas', icon: '📍' },
  { id: 'actividad', label: 'Actividad', icon: '📊' },
  { id: 'alertas', label: 'Alertas', icon: '🔔' },
];

/**
 * Barra lateral del dashboard.
 */
export default function Sidebar({ active, onSelect, pets, selectedPet, onSelectPet, connected }) {
  const { user, logout } = useAuth();

  return (
    <aside className="w-64 shrink-0 h-full bg-vx-surface border-r border-vx-border flex flex-col">
      {/* Logo */}
      <div className="px-5 py-5 border-b border-vx-border">
        <div className="flex items-center gap-2">
          <div className="w-9 h-9 rounded-lg bg-vx-blue flex items-center justify-center text-lg">📍</div>
          <div>
            <h1 className="font-extrabold leading-tight">
              Vertex<span className="text-vx-blue">Location</span>
            </h1>
            <span className="text-[10px] text-vx-muted flex items-center gap-1">
              <span
                className={`inline-block w-2 h-2 rounded-full ${connected ? 'bg-vx-success' : 'bg-vx-muted'}`}
              />
              {connected ? 'En línea' : 'Reconectando…'}
            </span>
          </div>
        </div>
      </div>

      {/* Selector de mascota */}
      <div className="px-4 py-3 border-b border-vx-border">
        <label className="text-[10px] uppercase text-vx-muted">Mascota activa</label>
        <select
          className="vx-input mt-1"
          value={selectedPet?.id || ''}
          onChange={(e) => onSelectPet(pets.find((p) => p.id === e.target.value))}
        >
          {pets.length === 0 && <option>— Sin mascotas —</option>}
          {pets.map((p) => (
            <option key={p.id} value={p.id}>
              {p.nombre} {p.raza ? `· ${p.raza}` : ''}
            </option>
          ))}
        </select>
      </div>

      {/* Navegación */}
      <nav className="flex-1 px-3 py-3 space-y-1">
        {NAV.map((item) => (
          <button
            key={item.id}
            onClick={() => onSelect(item.id)}
            className={`w-full flex items-center gap-3 px-3 py-2.5 rounded-xl text-sm transition-colors ${
              active === item.id
                ? 'bg-vx-blue/15 text-vx-blueLight border border-vx-border'
                : 'text-vx-muted hover:bg-vx-bg hover:text-white'
            }`}
          >
            <span>{item.icon}</span>
            {item.label}
          </button>
        ))}
      </nav>

      {/* Usuario */}
      <div className="px-4 py-4 border-t border-vx-border">
        <p className="text-sm font-semibold truncate">{user?.nombre}</p>
        <p className="text-xs text-vx-muted truncate">{user?.email}</p>
        <button onClick={logout} className="mt-2 text-xs text-vx-danger hover:underline">
          Cerrar sesión
        </button>
      </div>
    </aside>
  );
}

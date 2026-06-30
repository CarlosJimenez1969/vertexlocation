import { useEffect, useState } from 'react';
import { useParams } from 'react-router-dom';
import PetMap from '../components/Map/PetMap';
import { shareApi } from '../api/client';

/**
 * Página PÚBLICA (sin login) para ver la ubicación en vivo de un activo
 * compartido por enlace. Refresca la posición automáticamente.
 */
export default function SharedLocation() {
  const { token } = useParams();
  const [data, setData] = useState(null);
  const [estado, setEstado] = useState('cargando'); // cargando | ok | invalido | expirado | error

  useEffect(() => {
    let vivo = true;
    const cargar = () => {
      shareApi.getPublic(token)
        .then((r) => { if (vivo) { setData(r.data); setEstado('ok'); } })
        .catch((e) => {
          if (!vivo) return;
          const s = e.response?.status;
          setEstado(s === 410 ? 'expirado' : s === 404 ? 'invalido' : 'error');
        });
    };
    cargar();
    const t = setInterval(cargar, 12000); // refresca cada 12s
    return () => { vivo = false; clearInterval(t); };
  }, [token]);

  const Marco = ({ children }) => (
    <div className="h-screen flex flex-col bg-vx-bg text-white">
      <header className="flex items-center justify-between px-5 py-3 border-b border-vx-border">
        <div className="flex items-center gap-2">
          <div className="w-8 h-8 rounded-lg bg-vx-blue flex items-center justify-center">📍</div>
          <span className="font-extrabold">Vertex<span className="text-vx-blue">Location</span></span>
        </div>
        <span className="text-[11px] text-vx-muted">Ubicación compartida</span>
      </header>
      {children}
    </div>
  );

  if (estado !== 'ok') {
    const msg = {
      cargando: 'Cargando ubicación…',
      invalido: 'Este enlace no es válido.',
      expirado: 'Este enlace de ubicación ya expiró.',
      error: 'No se pudo cargar la ubicación.',
    }[estado];
    return (
      <Marco>
        <div className="flex-1 flex items-center justify-center text-vx-muted text-center px-6">
          <div>
            <div className="text-3xl mb-3">{estado === 'cargando' ? '⏳' : '🔒'}</div>
            <p>{msg}</p>
          </div>
        </div>
      </Marco>
    );
  }

  const pos = data.posicion;
  const position = pos ? [pos.latitud, pos.longitud] : null;
  const velocidad = pos?.velocidad != null ? Math.round(pos.velocidad) : null;
  const fecha = pos?.fija_en ? new Date(pos.fija_en).toLocaleString('es-EC') : null;
  const expira = data.expira_en ? new Date(data.expira_en).toLocaleString('es-EC') : null;

  return (
    <Marco>
      <div className="px-5 py-2 flex items-center justify-between text-sm border-b border-vx-border">
        <span className="font-bold">{data.emoji} {data.nombre}</span>
        {velocidad != null && <span className="text-vx-muted">{velocidad} km/h</span>}
      </div>

      <div className="flex-1 min-h-0 relative">
        {position ? (
          <PetMap position={position} route={[]} petName={data.nombre} markerEmoji={data.emoji} />
        ) : (
          <div className="h-full flex items-center justify-center text-vx-muted text-center px-6">
            📡 Esperando señal del rastreador…
          </div>
        )}
      </div>

      <footer className="px-5 py-2 text-[11px] text-vx-muted flex flex-col sm:flex-row sm:items-center sm:justify-between gap-1 border-t border-vx-border">
        <span>{fecha ? `Últ. actualización: ${fecha}` : 'Sin posición todavía'}</span>
        <span>{expira ? `El enlace expira: ${expira}` : ''}</span>
      </footer>
    </Marco>
  );
}

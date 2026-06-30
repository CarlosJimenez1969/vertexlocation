import { useState } from 'react';
import { shareApi } from '../../api/client';

/**
 * Botón + panel para generar un enlace público temporal con la ubicación en vivo.
 * tipo: 'mascota' | 'vehiculo'  ·  targetId: id del activo
 */
export default function CompartirUbicacion({ tipo, targetId, disabled }) {
  const [abierto, setAbierto] = useState(false);
  const [horas, setHoras] = useState(24);
  const [link, setLink] = useState('');
  const [busy, setBusy] = useState(false);
  const [copiado, setCopiado] = useState(false);
  const [error, setError] = useState('');

  const generar = async () => {
    setBusy(true); setError('');
    try {
      const { data } = await shareApi.create(tipo, targetId, Number(horas));
      setLink(`${window.location.origin}/ver/${data.token}`);
    } catch (e) {
      setError(e.response?.data?.detail || 'No se pudo generar el enlace.');
    } finally { setBusy(false); }
  };

  const copiar = async () => {
    try { await navigator.clipboard.writeText(link); } catch { /* noop */ }
    setCopiado(true); setTimeout(() => setCopiado(false), 1500);
  };

  const cerrar = () => { setAbierto(false); setLink(''); setError(''); };

  return (
    <div className="relative">
      <button
        onClick={() => (abierto ? cerrar() : setAbierto(true))}
        disabled={disabled}
        className="text-sm font-semibold rounded-xl px-4 py-2 border border-vx-blue/40 bg-vx-blue/15 text-vx-blueLight hover:bg-vx-blue/25 disabled:opacity-50"
        title={disabled ? 'Asigna un rastreador primero' : ''}
      >
        🔗 Compartir ubicación
      </button>

      {abierto && (
        <div className="absolute right-0 mt-2 z-[1000] w-72 vx-card p-3 space-y-2 shadow-glow text-left">
          {!link ? (
            <>
              <p className="text-xs text-vx-muted">Genera un enlace público para ver la ubicación en vivo (sin necesidad de cuenta).</p>
              <label className="text-xs text-vx-muted">Válido por:</label>
              <select className="vx-input text-sm" value={horas} onChange={(e) => setHoras(e.target.value)}>
                <option value={1}>1 hora</option>
                <option value={8}>8 horas</option>
                <option value={24}>24 horas</option>
                <option value={168}>7 días</option>
              </select>
              {error && <p className="text-xs text-vx-danger">{error}</p>}
              <div className="flex gap-2">
                <button onClick={generar} disabled={busy} className="vx-btn flex-1 text-sm py-1.5">
                  {busy ? 'Generando…' : 'Generar enlace'}
                </button>
                <button onClick={cerrar} className="text-xs text-vx-muted px-2">Cerrar</button>
              </div>
            </>
          ) : (
            <>
              <p className="text-xs text-vx-success">✅ Enlace listo. Compártelo:</p>
              <input readOnly value={link} onFocus={(e) => e.target.select()}
                className="vx-input text-xs" />
              <div className="flex gap-2">
                <button onClick={copiar} className="vx-btn flex-1 text-sm py-1.5">
                  {copiado ? '✅ Copiado' : '📋 Copiar'}
                </button>
                <a href={link} target="_blank" rel="noreferrer"
                   className="text-sm text-vx-blueLight px-3 py-1.5 hover:text-vx-blue">Abrir</a>
              </div>
              <button onClick={() => setLink('')} className="text-[11px] text-vx-muted">Generar otro</button>
            </>
          )}
        </div>
      )}
    </div>
  );
}

import { useEffect, useState } from 'react';
import PetMap from '../Map/PetMap';
import { vehiclesApi, geofencesApi } from '../../api/client';
import { useAuth } from '../../context/AuthContext';
import CompartirUbicacion from '../Compartir/CompartirUbicacion';

const EMOJI = { auto: '🚗', camioneta: '🛻', moto: '🏍️', otro: '🚙' };

/**
 * Rastreo en vivo de un vehículo: mapa con posición, ruta del día, tiempo real
 * y modo estacionado/armado (anti-robo).
 */
export default function VehiculoTracker({ vehiculo, lastMessage, onBack }) {
  const { isAdmin } = useAuth();
  const limitEditable = isAdmin; // el límite de velocidad lo fija el admin
  const [veh, setVeh] = useState(vehiculo);
  const [position, setPosition] = useState(null);
  const [route, setRoute] = useState([]);
  const [info, setInfo] = useState(null);
  const [aviso, setAviso] = useState('');
  const [alerta, setAlerta] = useState(null);
  const [armBusy, setArmBusy] = useState(false);
  const [limiteInput, setLimiteInput] = useState(vehiculo.limite_velocidad || '');
  const [geocercas, setGeocercas] = useState([]);
  const [geoBusy, setGeoBusy] = useState(false);
  const [inmoConfirm, setInmoConfirm] = useState(false);
  const [inmoPwd, setInmoPwd] = useState('');
  const [inmoBusy, setInmoBusy] = useState(false);
  const [inmoMsg, setInmoMsg] = useState('');

  // Carga inicial: última posición + ruta del día
  useEffect(() => {
    setAviso(''); setPosition(null); setRoute([]); setInfo(null); setAlerta(null); setGeocercas([]);
    setInmoConfirm(false); setInmoPwd(''); setInmoMsg('');
    setVeh(vehiculo);
    setLimiteInput(vehiculo.limite_velocidad || '');
    cargarGeocercas();
    if (!vehiculo.dispositivo_id) {
      setAviso('Este vehículo aún no tiene un rastreador asignado.');
      return;
    }
    vehiclesApi.latest(vehiculo.id)
      .then((r) => {
        if (r.data) { setPosition([r.data.latitud, r.data.longitud]); setInfo(r.data); }
        else setAviso('Sin posiciones todavía. Esperando señal del rastreador…');
      })
      .catch((e) => setAviso(e.response?.data?.detail || 'No se pudo obtener la posición.'));
    vehiclesApi.history(vehiculo.id, 1)
      .then((r) => setRoute(r.data.map((p) => [p.latitud, p.longitud])))
      .catch(() => {});
  }, [vehiculo.id]);

  const cargarGeocercas = () =>
    geofencesApi.list()
      .then((r) => setGeocercas(r.data.filter((g) => g.vehiculo_id === vehiculo.id)))
      .catch(() => {});

  const crearZona = async () => {
    if (!position) return;
    setGeoBusy(true); setAviso('');
    try {
      await geofencesApi.create({
        nombre: `Zona de ${veh.alias}`, tipo: 'circular',
        centro_lat: position[0], centro_lng: position[1], radio_m: 300,
        vehiculo_id: veh.id, alerta_salida: true,
      });
      cargarGeocercas();
    } catch (e) {
      setAviso(e.response?.data?.detail || 'No se pudo crear la zona segura.');
    } finally { setGeoBusy(false); }
  };

  const quitarZonas = async () => {
    setGeoBusy(true);
    try {
      await Promise.all(geocercas.map((g) => geofencesApi.remove(g.id)));
      cargarGeocercas();
    } catch { /* noop */ } finally { setGeoBusy(false); }
  };

  const accionarMotor = async () => {
    setInmoBusy(true); setInmoMsg('');
    try {
      const r = veh.motor_cortado
        ? await vehiclesApi.engineRestore(veh.id, inmoPwd)
        : await vehiclesApi.engineCut(veh.id, inmoPwd);
      setVeh(r.data);
      setInmoConfirm(false); setInmoPwd('');
      setInmoMsg(r.data.motor_cortado ? '🛑 Comando de corte enviado.' : '🔁 Comando de restablecimiento enviado.');
    } catch (e) {
      setInmoMsg(e.response?.data?.detail || 'No se pudo ejecutar la acción.');
    } finally { setInmoBusy(false); }
  };

  // Tiempo real: posiciones y alertas de ESTE vehículo
  useEffect(() => {
    if (!lastMessage) return;
    if (lastMessage.type === 'position' && lastMessage.vehiculo_id === vehiculo.id) {
      setPosition([lastMessage.latitud, lastMessage.longitud]);
      setInfo(lastMessage);
      setRoute((prev) => [...prev.slice(-500), [lastMessage.latitud, lastMessage.longitud]]);
      setAviso('');
    }
    if (lastMessage.type === 'alert' && lastMessage.vehiculo_id === vehiculo.id) {
      setAlerta(lastMessage);
    }
  }, [lastMessage]);

  const toggleArmado = async () => {
    setArmBusy(true);
    setAviso('');
    try {
      const r = veh.armado ? await vehiclesApi.disarm(veh.id) : await vehiclesApi.arm(veh.id);
      setVeh(r.data);
      if (!r.data.armado) setAlerta(null);
    } catch (e) {
      setAviso(e.response?.data?.detail || 'No se pudo cambiar el estado.');
    } finally {
      setArmBusy(false);
    }
  };

  const guardarLimite = async () => {
    const n = parseInt(limiteInput, 10);
    try {
      const r = await vehiclesApi.update(veh.id, { limite_velocidad: Number.isNaN(n) ? 0 : n });
      setVeh(r.data);
      setLimiteInput(r.data.limite_velocidad || '');
    } catch { /* noop */ }
  };

  const velocidad = Math.round(info?.velocidad ?? 0);
  const excede = veh.limite_velocidad && velocidad > veh.limite_velocidad;
  const fechaFix = info?.fija_en ? new Date(info.fija_en).toLocaleString('es-EC') : null;

  return (
    <div className="h-full flex flex-col">
      {/* Banner de alerta de robo */}
      {alerta && (
        <div className="mb-3 rounded-xl border border-vx-danger bg-vx-danger/15 px-4 py-3 flex items-start justify-between gap-3">
          <div>
            <p className="font-bold text-vx-danger">{alerta.titulo}</p>
            <p className="text-xs text-vx-muted">{alerta.mensaje}</p>
          </div>
          <button onClick={() => setAlerta(null)} className="text-vx-muted hover:text-white text-sm">✕</button>
        </div>
      )}

      <div className="flex items-start justify-between mb-3 gap-3">
        <div>
          <button onClick={onBack} className="text-xs text-vx-blueLight hover:text-vx-blue">
            ← Volver a vehículos
          </button>
          <h2 className="text-xl font-bold flex items-center gap-2">
            {EMOJI[veh.tipo] || '🚗'} {veh.alias}
            {veh.armado && (
              <span className="text-xs px-2 py-0.5 rounded-full bg-vx-success/20 text-vx-success border border-vx-success/40">
                🅿️ Armado
              </span>
            )}
          </h2>
          <p className="text-xs text-vx-muted">
            {position
              ? `📍 ${position[0].toFixed(5)}, ${position[1].toFixed(5)}`
              : (aviso || 'Esperando señal del rastreador…')}
          </p>
        </div>
        <div className="flex flex-col items-end gap-2 shrink-0">
          <CompartirUbicacion tipo="vehiculo" targetId={veh.id} disabled={!veh.dispositivo_id} />
          <button
            onClick={toggleArmado}
            disabled={armBusy || !veh.dispositivo_id}
            className={`text-sm font-semibold rounded-xl px-4 py-2 transition-colors ${
              veh.armado
                ? 'bg-vx-danger/20 text-vx-danger hover:bg-vx-danger/30 border border-vx-danger/40'
                : 'bg-vx-success/20 text-vx-success hover:bg-vx-success/30 border border-vx-success/40'
            } disabled:opacity-50`}
            title={!veh.dispositivo_id ? 'Asigna un rastreador primero' : ''}
          >
            {armBusy ? '…' : veh.armado ? '🔓 Desarmar' : '🛡️ Armar (estacionado)'}
          </button>

          {/* Inmovilizador (corte de motor) */}
          {veh.tiene_inmovilizador && (
            <div className="flex flex-col items-end gap-1">
              {!inmoConfirm ? (
                <button
                  onClick={() => { setInmoConfirm(true); setInmoMsg(''); }}
                  className={`text-sm font-semibold rounded-xl px-4 py-2 border ${
                    veh.motor_cortado
                      ? 'bg-vx-warning/20 text-vx-warning border-vx-warning/40 hover:bg-vx-warning/30'
                      : 'bg-vx-danger/20 text-vx-danger border-vx-danger/40 hover:bg-vx-danger/30'
                  }`}
                >
                  {veh.motor_cortado ? '🔁 Restablecer motor' : '🛑 Cortar motor'}
                </button>
              ) : (
                <div className="vx-card p-3 w-64 space-y-2 text-left">
                  <p className="text-xs text-vx-muted">
                    {veh.motor_cortado
                      ? 'Confirma para restablecer el motor.'
                      : '⚠️ Vas a cortar el motor. Confirma con tu contraseña:'}
                  </p>
                  <input
                    type="password" autoComplete="off" value={inmoPwd}
                    onChange={(e) => setInmoPwd(e.target.value)}
                    onKeyDown={(e) => e.key === 'Enter' && inmoPwd && accionarMotor()}
                    placeholder="Contraseña" className="vx-input"
                  />
                  <div className="flex gap-2">
                    <button onClick={accionarMotor} disabled={inmoBusy || !inmoPwd} className="vx-btn flex-1 text-xs py-1.5">
                      {inmoBusy ? '…' : 'Confirmar'}
                    </button>
                    <button
                      onClick={() => { setInmoConfirm(false); setInmoPwd(''); setInmoMsg(''); }}
                      className="text-xs text-vx-muted px-2"
                    >
                      Cancelar
                    </button>
                  </div>
                </div>
              )}
              {veh.motor_cortado && <span className="text-[10px] text-vx-warning font-semibold">🛑 Motor cortado</span>}
              {inmoMsg && <span className="text-[10px] text-vx-muted max-w-64 text-right">{inmoMsg}</span>}
            </div>
          )}

          <div className="vx-card px-4 py-2 text-xs text-vx-muted text-right">
            <p>Velocidad: <b className={excede ? 'text-vx-danger' : 'text-white'}>{velocidad} km/h</b>
              {excede && <span className="text-vx-danger"> ⚡</span>}
            </p>
            <p className="mt-1 flex items-center justify-end gap-1">
              Límite:
              <input
                type="number" min="0" value={limiteInput}
                onChange={(e) => setLimiteInput(e.target.value)}
                onBlur={limitEditable ? guardarLimite : undefined}
                onKeyDown={(e) => e.key === 'Enter' && e.target.blur()}
                placeholder="—" disabled={!limitEditable}
                className="w-14 bg-vx-bg border border-vx-border rounded px-1 text-right text-white disabled:opacity-60"
              /> km/h
            </p>
            {info?.bateria != null && <p>Batería: <b className="text-white">{info.bateria}%</b></p>}
            {fechaFix && <p className="mt-1">Últ. reporte: {fechaFix}</p>}
          </div>
        </div>
      </div>

      {/* Zona segura (geocerca anti-robo) */}
      <div className="flex items-center justify-between mb-2 text-xs">
        <span className="text-vx-muted">
          {geocercas.length > 0
            ? `🛟 Zona segura activa (radio ${geocercas[0].radio_m} m) — te avisamos si el vehículo sale`
            : 'Sin zona segura definida'}
        </span>
        {geocercas.length > 0 ? (
          <button onClick={quitarZonas} disabled={geoBusy} className="text-vx-danger hover:underline">
            🗑️ Quitar zona
          </button>
        ) : (
          <button
            onClick={crearZona} disabled={geoBusy || !position}
            className="text-vx-blueLight hover:text-vx-blue font-semibold disabled:opacity-50"
            title={!position ? 'Se necesita una posición del vehículo' : ''}
          >
            🛟 Crear zona segura aquí (300 m)
          </button>
        )}
      </div>

      <div className="flex-1 min-h-0">
        <PetMap
          position={position}
          route={route}
          geofences={geocercas}
          petName={veh.alias}
          markerEmoji={EMOJI[veh.tipo] || '🚗'}
        />
      </div>
    </div>
  );
}

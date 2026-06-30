import { useEffect, useState, useCallback } from 'react';
import Sidebar from '../components/Sidebar/Sidebar';
import PetMap from '../components/Map/PetMap';
import MoodCard from '../components/MoodCard/MoodCard';
import AlertPanel from '../components/AlertPanel/AlertPanel';
import ActivityChart from '../components/ActivityChart';
import MascotasPanel from '../components/Mascotas/MascotasPanel';
import VehiculosPanel from '../components/Vehiculos/VehiculosPanel';
import DispositivosPanel from '../components/Dispositivos/DispositivosPanel';
import CompartirUbicacion from '../components/Compartir/CompartirUbicacion';
import { useRealtime } from '../hooks/useRealtime';
import {
  petsApi, positionsApi, geofencesApi, moodApi, alertsApi,
} from '../api/client';

export default function Dashboard() {
  const { lastMessage, connected } = useRealtime();
  const [section, setSection] = useState('mapa');
  const [pets, setPets] = useState([]);
  const [selectedPet, setSelectedPet] = useState(null);
  const [position, setPosition] = useState(null);
  const [route, setRoute] = useState([]);
  const [geofences, setGeofences] = useState([]);
  const [mood, setMood] = useState(null);
  const [activity, setActivity] = useState([]);
  const [alerts, setAlerts] = useState([]);

  // Carga las mascotas y preserva la selección actual (refrescando su objeto,
  // p.ej. tras subir una foto). Si no había selección, toma la primera.
  const loadPets = useCallback(() => {
    return petsApi.list().then((r) => {
      setPets(r.data);
      setSelectedPet((prev) =>
        prev ? r.data.find((p) => p.id === prev.id) || r.data[0] || null : r.data[0] || null
      );
    });
  }, []);

  // Cargar datos al inicio
  useEffect(() => {
    loadPets();
    geofencesApi.list().then((r) => setGeofences(r.data));
    refreshAlerts();
  }, []);

  // Cargar datos al cambiar de mascota
  useEffect(() => {
    if (!selectedPet) return;
    positionsApi.latest(selectedPet.id).then((r) => {
      if (r.data) setPosition([r.data.latitud, r.data.longitud]);
    });
    positionsApi.history(selectedPet.id, 1).then((r) =>
      setRoute(r.data.map((p) => [p.latitud, p.longitud]))
    );
    moodApi.current(selectedPet.id).then((r) => setMood(r.data));
    moodApi.activity(selectedPet.id, 7).then((r) => setActivity(r.data));
  }, [selectedPet?.id]);

  // Mensajes en tiempo real (posiciones / eventos)
  useEffect(() => {
    if (!lastMessage) return;
    if (lastMessage.type === 'position' && selectedPet &&
        lastMessage.mascota_id === selectedPet.id) {
      setPosition([lastMessage.latitud, lastMessage.longitud]);
      setRoute((prev) => [...prev.slice(-500), [lastMessage.latitud, lastMessage.longitud]]);
    }
    if (lastMessage.type === 'event') {
      refreshAlerts();
    }
  }, [lastMessage]);

  const refreshAlerts = useCallback(() => {
    alertsApi.list().then((r) => setAlerts(r.data));
  }, []);

  const recalcMood = () => {
    if (!selectedPet) return;
    moodApi.recalculate(selectedPet.id).then((r) => setMood(r.data));
  };

  const markRead = (id) => {
    alertsApi.markRead(id).then(refreshAlerts);
  };

  return (
    <div className="h-full flex bg-vx-bg">
      <Sidebar
        active={section}
        onSelect={setSection}
        pets={pets}
        selectedPet={selectedPet}
        onSelectPet={setSelectedPet}
        connected={connected}
      />

      {/* Sección "Mis mascotas" (crear y gestionar fotos) */}
      {section === 'mascotas' ? (
        <main className="flex-1 p-4 overflow-hidden">
          <MascotasPanel pets={pets} onChanged={loadPets} />
        </main>
      ) : section === 'vehiculos' ? (
        <main className="flex-1 p-4 overflow-hidden">
          <VehiculosPanel lastMessage={lastMessage} />
        </main>
      ) : section === 'dispositivos' ? (
        <main className="flex-1 p-4 overflow-hidden">
          <DispositivosPanel />
        </main>
      ) : (
      <main className="flex-1 grid grid-cols-12 gap-4 p-4 overflow-hidden">
        {/* Mapa central */}
        <section className="col-span-12 lg:col-span-8 flex flex-col min-h-0">
          <div className="flex items-center justify-between mb-3">
            <div>
              <h2 className="text-xl font-bold">
                {selectedPet ? selectedPet.nombre : 'Sin mascota'}
              </h2>
              <p className="text-xs text-vx-muted">
                {position
                  ? `📍 ${position[0].toFixed(5)}, ${position[1].toFixed(5)}`
                  : 'Esperando señal del collar C059…'}
              </p>
            </div>
            {selectedPet && (
              <CompartirUbicacion tipo="mascota" targetId={selectedPet.id} disabled={!selectedPet.dispositivo_id} />
            )}
          </div>
          <div className="flex-1 min-h-0">
            <PetMap
              position={position}
              route={route}
              geofences={geofences}
              petName={selectedPet?.nombre}
            />
          </div>
        </section>

        {/* Panel derecho */}
        <aside className="col-span-12 lg:col-span-4 flex flex-col gap-4 overflow-y-auto">
          <MoodCard mood={mood} pet={selectedPet} onRecalculate={recalcMood} />
          <ActivityChart data={activity} />
          <div className="flex-1 min-h-[220px]">
            <AlertPanel alerts={alerts} onMarkRead={markRead} />
          </div>
        </aside>
      </main>
      )}
    </div>
  );
}

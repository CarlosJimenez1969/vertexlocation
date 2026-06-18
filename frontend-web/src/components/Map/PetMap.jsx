import { useEffect, useMemo } from 'react';
import {
  MapContainer, TileLayer, Marker, Popup, Circle, Polygon, Polyline, useMap,
} from 'react-leaflet';
import L from 'leaflet';

// Icono personalizado del activo rastreado (emoji configurable)
const makeIcon = (emoji) =>
  L.divIcon({
    className: '',
    html: `<div style="
      width:34px;height:34px;border-radius:50%;
      background:#3B82F6;border:3px solid #60A5FA;
      display:flex;align-items:center;justify-content:center;
      box-shadow:0 0 14px rgba(59,130,246,.8);font-size:18px;">${emoji}</div>`,
    iconSize: [34, 34],
    iconAnchor: [17, 17],
  });

// Centra el mapa cuando cambia la posición
function Recenter({ position }) {
  const map = useMap();
  useEffect(() => {
    if (position) map.setView(position, map.getZoom(), { animate: true });
  }, [position?.[0], position?.[1]]);
  return null;
}

/**
 * Mapa principal con la posición en vivo, ruta histórica y geocercas.
 */
export default function PetMap({ position, route = [], geofences = [], petName, markerEmoji = '🐶' }) {
  // Centro por defecto: Quito, Ecuador
  const center = position || [-0.1807, -78.4678];
  const icon = useMemo(() => makeIcon(markerEmoji), [markerEmoji]);

  return (
    <MapContainer center={center} zoom={16} className="h-full w-full rounded-2xl" zoomControl={false}>
      <TileLayer
        attribution='&copy; OpenStreetMap &copy; CARTO'
        url="https://{s}.basemaps.cartocdn.com/rastertiles/voyager/{z}/{x}/{y}{r}.png"
      />

      {/* Ruta histórica */}
      {route.length > 1 && (
        <Polyline positions={route} pathOptions={{ color: '#60A5FA', weight: 3, opacity: 0.7 }} />
      )}

      {/* Geocercas */}
      {geofences.map((g) =>
        g.tipo === 'circular' && g.centro_lat != null ? (
          <Circle
            key={g.id}
            center={[g.centro_lat, g.centro_lng]}
            radius={g.radio_m}
            pathOptions={{ color: g.color || '#3B82F6', fillOpacity: 0.08 }}
          />
        ) : g.poligono ? (
          <Polygon
            key={g.id}
            positions={g.poligono.map((p) => [p.lat, p.lng])}
            pathOptions={{ color: g.color || '#3B82F6', fillOpacity: 0.08 }}
          />
        ) : null
      )}

      {/* Posición actual */}
      {position && (
        <Marker position={position} icon={icon}>
          <Popup>{petName || 'Activo'}</Popup>
        </Marker>
      )}

      <Recenter position={position} />
    </MapContainer>
  );
}

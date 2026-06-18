import React, { useEffect, useRef, useState } from 'react';
import { View, Text, StyleSheet, ActivityIndicator } from 'react-native';
import MapView, { Marker, PROVIDER_GOOGLE } from 'react-native-maps';
import { petsApi, positionsApi } from '../api/client';
import { colors, MOOD } from '../theme';
import { moodApi } from '../api/client';

const QUITO = { latitude: -0.1807, longitude: -78.4678, latitudeDelta: 0.02, longitudeDelta: 0.02 };

export default function MapScreen() {
  const [pet, setPet] = useState(null);
  const [pos, setPos] = useState(null);
  const [mood, setMood] = useState(null);
  const [loading, setLoading] = useState(true);
  const mapRef = useRef(null);
  const pollRef = useRef(null);

  useEffect(() => {
    petsApi.list().then((r) => {
      if (r.data.length) setPet(r.data[0]);
      setLoading(false);
    });
  }, []);

  useEffect(() => {
    if (!pet) return;
    const fetchPos = () => {
      positionsApi.latest(pet.id).then((r) => {
        if (r.data) {
          const p = { latitude: r.data.latitud, longitude: r.data.longitud };
          setPos(p);
          mapRef.current?.animateToRegion({ ...p, latitudeDelta: 0.01, longitudeDelta: 0.01 }, 600);
        }
      }).catch(() => {});
    };
    moodApi.current(pet.id).then((r) => setMood(r.data)).catch(() => {});
    fetchPos();
    // Refresco periódico de la posición (5 s)
    pollRef.current = setInterval(fetchPos, 5000);
    return () => clearInterval(pollRef.current);
  }, [pet?.id]);

  if (loading) {
    return (
      <View style={styles.center}>
        <ActivityIndicator color={colors.blue} size="large" />
      </View>
    );
  }

  const moodCfg = MOOD[mood?.estado] || MOOD.sin_datos;

  return (
    <View style={styles.container}>
      <MapView
        ref={mapRef}
        style={StyleSheet.absoluteFill}
        provider={PROVIDER_GOOGLE}
        initialRegion={pos ? { ...pos, latitudeDelta: 0.01, longitudeDelta: 0.01 } : QUITO}
        customMapStyle={DARK_MAP}
      >
        {pos && (
          <Marker coordinate={pos} title={pet?.nombre}>
            <View style={styles.marker}>
              <Text style={{ fontSize: 18 }}>🐶</Text>
            </View>
          </Marker>
        )}
      </MapView>

      {/* Tarjeta flotante de estado */}
      <View style={styles.card}>
        <View style={{ flexDirection: 'row', alignItems: 'center', gap: 10 }}>
          <Text style={{ fontSize: 28 }}>{moodCfg.emoji}</Text>
          <View style={{ flex: 1 }}>
            <Text style={styles.petName}>{pet?.nombre || 'Sin mascota'}</Text>
            <Text style={[styles.moodLabel, { color: moodCfg.color }]}>{moodCfg.label}</Text>
          </View>
          <View style={styles.dot(pos ? colors.success : colors.muted)} />
        </View>
        <Text style={styles.coords}>
          {pos
            ? `📍 ${pos.latitude.toFixed(5)}, ${pos.longitude.toFixed(5)}`
            : 'Esperando señal del collar C059…'}
        </Text>
      </View>
    </View>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: colors.bg },
  center: { flex: 1, backgroundColor: colors.bg, justifyContent: 'center', alignItems: 'center' },
  marker: {
    width: 40, height: 40, borderRadius: 20, backgroundColor: colors.blue,
    borderWidth: 3, borderColor: colors.blueLight, alignItems: 'center', justifyContent: 'center',
  },
  card: {
    position: 'absolute', left: 16, right: 16, bottom: 24,
    backgroundColor: colors.surface, borderColor: colors.border, borderWidth: 1,
    borderRadius: 18, padding: 16,
  },
  petName: { color: colors.text, fontWeight: '700', fontSize: 16 },
  moodLabel: { fontWeight: '600', fontSize: 13, marginTop: 2 },
  coords: { color: colors.muted, fontSize: 12, marginTop: 10 },
  dot: (c) => ({ width: 12, height: 12, borderRadius: 6, backgroundColor: c }),
});

// Estilo de mapa oscuro (Google Maps)
const DARK_MAP = [
  { elementType: 'geometry', stylers: [{ color: '#0A0E1A' }] },
  { elementType: 'labels.text.fill', stylers: [{ color: '#4A6B9A' }] },
  { elementType: 'labels.text.stroke', stylers: [{ color: '#0A0E1A' }] },
  { featureType: 'road', elementType: 'geometry', stylers: [{ color: '#1E3A6B' }] },
  { featureType: 'water', elementType: 'geometry', stylers: [{ color: '#0F1626' }] },
  { featureType: 'poi', stylers: [{ visibility: 'off' }] },
];

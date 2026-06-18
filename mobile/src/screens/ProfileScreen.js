import React, { useEffect, useState } from 'react';
import {
  View, Text, StyleSheet, ScrollView, TouchableOpacity, ActivityIndicator, Image,
} from 'react-native';
import { petsApi, moodApi } from '../api/client';
import { useAuth } from '../context/AuthContext';
import { colors, MOOD } from '../theme';

export default function ProfileScreen() {
  const { user, logout } = useAuth();
  const [pet, setPet] = useState(null);
  const [mood, setMood] = useState(null);
  const [activity, setActivity] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    petsApi.list().then((r) => {
      const p = r.data[0];
      setPet(p);
      if (p) {
        moodApi.current(p.id).then((m) => setMood(m.data)).catch(() => {});
        moodApi.activity(p.id, 7).then((a) => setActivity(a.data)).catch(() => {});
      }
      setLoading(false);
    });
  }, []);

  if (loading) {
    return (
      <View style={styles.center}>
        <ActivityIndicator color={colors.blue} size="large" />
      </View>
    );
  }

  const moodCfg = MOOD[mood?.estado] || MOOD.sin_datos;
  const totalPasos = activity.reduce((a, b) => a + (b.pasos || 0), 0);
  const totalKm = activity.reduce((a, b) => a + Number(b.distancia_km || 0), 0);
  const totalCal = activity.reduce((a, b) => a + Number(b.calorias || 0), 0);

  return (
    <ScrollView style={styles.container} contentContainerStyle={{ padding: 16 }}>
      {/* Cabecera de la mascota */}
      <View style={styles.header}>
        {pet?.foto_url ? (
          <Image source={{ uri: pet.foto_url }} style={styles.avatar} />
        ) : (
          <View style={styles.avatar}>
            <Text style={{ fontSize: 40 }}>🐶</Text>
          </View>
        )}
        <Text style={styles.name}>{pet?.nombre || 'Sin mascota'}</Text>
        <Text style={styles.breed}>
          {pet?.raza || 'Raza desconocida'} {pet?.edad_meses ? `· ${pet.edad_meses} meses` : ''}
        </Text>
      </View>

      {/* Estado de ánimo */}
      <View style={styles.card}>
        <Text style={styles.cardTitle}>ESTADO DE ÁNIMO</Text>
        <View style={{ flexDirection: 'row', alignItems: 'center', gap: 14 }}>
          <View style={[styles.moodIcon, { backgroundColor: `${moodCfg.color}22`, borderColor: moodCfg.color }]}>
            <Text style={{ fontSize: 30 }}>{moodCfg.emoji}</Text>
          </View>
          <View style={{ flex: 1 }}>
            <Text style={[styles.moodLabel, { color: moodCfg.color }]}>{moodCfg.label}</Text>
            {mood && (
              <Text style={styles.moodSub}>
                Confianza {Math.round((mood.confianza || 0) * 100)}% · Actividad{' '}
                {Math.round(mood.actividad_pct || 0)}%
              </Text>
            )}
          </View>
        </View>
      </View>

      {/* Actividad semanal */}
      <View style={styles.card}>
        <Text style={styles.cardTitle}>ACTIVIDAD (7 DÍAS)</Text>
        <View style={styles.statsRow}>
          <Stat label="Pasos" value={totalPasos} />
          <Stat label="Distancia" value={`${totalKm.toFixed(1)} km`} />
          <Stat label="Calorías" value={Math.round(totalCal)} />
        </View>
      </View>

      {/* Datos del dueño */}
      <View style={styles.card}>
        <Text style={styles.cardTitle}>CUENTA</Text>
        <Text style={styles.row}>{user?.nombre}</Text>
        <Text style={styles.rowMuted}>{user?.email}</Text>
        {user?.telefono ? <Text style={styles.rowMuted}>WhatsApp: {user.telefono}</Text> : null}
      </View>

      <TouchableOpacity style={styles.logout} onPress={logout}>
        <Text style={{ color: colors.danger, fontWeight: '700' }}>Cerrar sesión</Text>
      </TouchableOpacity>
    </ScrollView>
  );
}

function Stat({ label, value }) {
  return (
    <View style={styles.stat}>
      <Text style={styles.statValue}>{value}</Text>
      <Text style={styles.statLabel}>{label}</Text>
    </View>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: colors.bg },
  center: { flex: 1, backgroundColor: colors.bg, justifyContent: 'center', alignItems: 'center' },
  header: { alignItems: 'center', marginBottom: 18 },
  avatar: {
    width: 96, height: 96, borderRadius: 48, backgroundColor: colors.surface,
    borderWidth: 2, borderColor: colors.blue, alignItems: 'center', justifyContent: 'center',
  },
  name: { color: colors.text, fontSize: 22, fontWeight: '800', marginTop: 10 },
  breed: { color: colors.muted, fontSize: 13 },
  card: {
    backgroundColor: colors.surface, borderColor: colors.border, borderWidth: 1,
    borderRadius: 16, padding: 16, marginBottom: 14,
  },
  cardTitle: { color: colors.muted, fontSize: 11, fontWeight: '700', letterSpacing: 1, marginBottom: 12 },
  moodIcon: {
    width: 56, height: 56, borderRadius: 16, borderWidth: 1,
    alignItems: 'center', justifyContent: 'center',
  },
  moodLabel: { fontSize: 18, fontWeight: '700' },
  moodSub: { color: colors.muted, fontSize: 12, marginTop: 2 },
  statsRow: { flexDirection: 'row', justifyContent: 'space-between' },
  stat: { flex: 1, alignItems: 'center' },
  statValue: { color: colors.text, fontSize: 18, fontWeight: '800' },
  statLabel: { color: colors.muted, fontSize: 11, marginTop: 2 },
  row: { color: colors.text, fontSize: 15, fontWeight: '600' },
  rowMuted: { color: colors.muted, fontSize: 13, marginTop: 4 },
  logout: {
    borderColor: colors.danger, borderWidth: 1, borderRadius: 14,
    paddingVertical: 13, alignItems: 'center', marginTop: 4, marginBottom: 30,
  },
});

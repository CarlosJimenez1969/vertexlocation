import React, { useState } from 'react';
import {
  View, Text, TextInput, TouchableOpacity, StyleSheet, KeyboardAvoidingView,
  Platform, Alert, ActivityIndicator,
} from 'react-native';
import { useAuth } from '../context/AuthContext';
import { colors } from '../theme';

export default function LoginScreen() {
  const { login, register } = useAuth();
  const [modo, setModo] = useState('login');
  const [form, setForm] = useState({ nombre: '', email: '', password: '', telefono: '' });
  const [loading, setLoading] = useState(false);

  const set = (k, v) => setForm({ ...form, [k]: v });

  const submit = async () => {
    setLoading(true);
    try {
      if (modo === 'login') await login(form.email, form.password);
      else await register(form);
    } catch (e) {
      Alert.alert('Error', e.response?.data?.detail || 'No se pudo completar la acción.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <KeyboardAvoidingView
      style={styles.container}
      behavior={Platform.OS === 'ios' ? 'padding' : undefined}
    >
      <View style={styles.logoRow}>
        <View style={styles.logoBox}>
          <Text style={{ fontSize: 26 }}>📍</Text>
        </View>
        <View>
          <Text style={styles.brand}>
            Vertex<Text style={{ color: colors.blue }}>Location</Text>
          </Text>
          <Text style={styles.subtitle}>Rastreo GPS · Ecuador</Text>
        </View>
      </View>

      <Text style={styles.title}>{modo === 'login' ? 'Inicia sesión' : 'Crea tu cuenta'}</Text>

      {modo === 'registro' && (
        <TextInput
          style={styles.input}
          placeholder="Nombre completo"
          placeholderTextColor={colors.muted}
          value={form.nombre}
          onChangeText={(v) => set('nombre', v)}
        />
      )}
      <TextInput
        style={styles.input}
        placeholder="correo@ejemplo.com"
        placeholderTextColor={colors.muted}
        autoCapitalize="none"
        keyboardType="email-address"
        value={form.email}
        onChangeText={(v) => set('email', v)}
      />
      <TextInput
        style={styles.input}
        placeholder="Contraseña"
        placeholderTextColor={colors.muted}
        secureTextEntry
        value={form.password}
        onChangeText={(v) => set('password', v)}
      />
      {modo === 'registro' && (
        <TextInput
          style={styles.input}
          placeholder="WhatsApp (+593...)"
          placeholderTextColor={colors.muted}
          value={form.telefono}
          onChangeText={(v) => set('telefono', v)}
        />
      )}

      <TouchableOpacity style={styles.btn} onPress={submit} disabled={loading}>
        {loading ? (
          <ActivityIndicator color="#fff" />
        ) : (
          <Text style={styles.btnText}>{modo === 'login' ? 'Entrar' : 'Registrarme'}</Text>
        )}
      </TouchableOpacity>

      <TouchableOpacity onPress={() => setModo(modo === 'login' ? 'registro' : 'login')}>
        <Text style={styles.switch}>
          {modo === 'login' ? '¿No tienes cuenta? Regístrate' : '¿Ya tienes cuenta? Inicia sesión'}
        </Text>
      </TouchableOpacity>
    </KeyboardAvoidingView>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: colors.bg, justifyContent: 'center', padding: 24 },
  logoRow: { flexDirection: 'row', alignItems: 'center', gap: 12, marginBottom: 28 },
  logoBox: {
    width: 52, height: 52, borderRadius: 14, backgroundColor: colors.blue,
    alignItems: 'center', justifyContent: 'center',
  },
  brand: { color: colors.text, fontSize: 24, fontWeight: '800' },
  subtitle: { color: colors.muted, fontSize: 12 },
  title: { color: colors.text, fontSize: 18, fontWeight: '700', marginBottom: 16 },
  input: {
    backgroundColor: colors.surface, borderColor: colors.border, borderWidth: 1,
    borderRadius: 14, paddingHorizontal: 14, paddingVertical: 12, color: colors.text, marginBottom: 12,
  },
  btn: {
    backgroundColor: colors.blue, borderRadius: 14, paddingVertical: 14,
    alignItems: 'center', marginTop: 6,
  },
  btnText: { color: '#fff', fontWeight: '700', fontSize: 16 },
  switch: { color: colors.blueLight, textAlign: 'center', marginTop: 18 },
});

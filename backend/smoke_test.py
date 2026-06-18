"""Smoke test end-to-end contra el backend en marcha (puerto 8001)."""
import requests

BASE = "http://127.0.0.1:8001"
ok = lambda b: "OK" if b else "FALLO"

# Email único por corrida (sin random: usamos un sufijo fijo de prueba)
email = "test_smoke@vertexmascota.com"

print("=" * 60)
# 1) Registro (o login si ya existe)
r = requests.post(f"{BASE}/api/auth/register", json={
    "nombre": "Usuario Prueba", "email": email,
    "password": "ClaveSegura123", "telefono": "+593999999999", "ciudad": "Quito",
})
if r.status_code == 400:  # ya registrado de una corrida previa
    r = requests.post(f"{BASE}/api/auth/login-json",
                      json={"email": email, "password": "ClaveSegura123"})
    print(f"[1] Login (usuario ya existía): {r.status_code} -> {ok(r.ok)}")
else:
    print(f"[1] Registro: {r.status_code} (201 esperado) -> {ok(r.status_code == 201)}")

token = r.json()["access_token"]
headers = {"Authorization": f"Bearer {token}"}
print(f"    JWT recibido: {token[:30]}...")

# 2) /auth/me con el token
r = requests.get(f"{BASE}/api/auth/me", headers=headers)
print(f"[2] /auth/me: {r.status_code} -> {ok(r.ok)} | email={r.json().get('email')}")

# 3) Token inválido -> 401 (valida el fix de deps.py)
r = requests.get(f"{BASE}/api/auth/me", headers={"Authorization": "Bearer no-es-un-jwt"})
print(f"[3] /auth/me con token basura: {r.status_code} (401 esperado) -> {ok(r.status_code == 401)}")

# 4) Límite de plan: usuario sin suscripción => Básico (max 1 mascota)
#    Limpio mascotas previas para que la prueba sea determinista.
mascotas = requests.get(f"{BASE}/api/pets", headers=headers).json()
for m in mascotas:
    requests.delete(f"{BASE}/api/pets/{m['id']}", headers=headers)

r1 = requests.post(f"{BASE}/api/pets", headers=headers, json={"nombre": "Firulais", "especie": "perro"})
print(f"[4a] Crear 1ª mascota: {r1.status_code} (201 esperado) -> {ok(r1.status_code == 201)}")

r2 = requests.post(f"{BASE}/api/pets", headers=headers, json={"nombre": "Rex", "especie": "perro"})
print(f"[4b] Crear 2ª mascota (límite Básico): {r2.status_code} (403 esperado) -> {ok(r2.status_code == 403)}")
print(f"     Mensaje: {r2.json().get('detail')}")

# 5) Límite de geocercas (Básico = 1)
gfs = requests.get(f"{BASE}/api/geofences", headers=headers).json()
for g in gfs:
    requests.delete(f"{BASE}/api/geofences/{g['id']}", headers=headers)
g1 = requests.post(f"{BASE}/api/geofences", headers=headers, json={
    "nombre": "Casa", "tipo": "circular", "centro_lat": -0.18, "centro_lng": -78.46, "radio_m": 120})
print(f"[5a] Crear 1ª geocerca: {g1.status_code} (201 esperado) -> {ok(g1.status_code == 201)}")
g2 = requests.post(f"{BASE}/api/geofences", headers=headers, json={
    "nombre": "Parque", "tipo": "circular", "centro_lat": -0.19, "centro_lng": -78.47, "radio_m": 100})
print(f"[5b] Crear 2ª geocerca (límite Básico): {g2.status_code} (403 esperado) -> {ok(g2.status_code == 403)}")

print("=" * 60)
print("Smoke test completado.")

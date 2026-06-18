import { useState } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';
import { authApi } from '../api/client';

export default function ResetPassword() {
  const [params] = useSearchParams();
  const token = params.get('token') || '';
  const navigate = useNavigate();

  const [pwd, setPwd] = useState('');
  const [pwd2, setPwd2] = useState('');
  const [error, setError] = useState('');
  const [okMsg, setOkMsg] = useState('');
  const [loading, setLoading] = useState(false);

  const submit = async (e) => {
    e.preventDefault();
    setError('');
    if (pwd.length < 6) return setError('La contraseña debe tener al menos 6 caracteres.');
    if (pwd !== pwd2) return setError('Las contraseñas no coinciden.');
    setLoading(true);
    try {
      await authApi.resetPassword(token, pwd);
      setOkMsg('¡Contraseña actualizada! Te llevamos a iniciar sesión…');
      setTimeout(() => navigate('/login'), 1800);
    } catch (err) {
      setError(err.response?.data?.detail || 'No se pudo restablecer la contraseña.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="h-full flex items-center justify-center bg-vx-bg px-4">
      <div className="w-full max-w-md vx-card p-8 shadow-glow">
        <div className="flex items-center gap-3 mb-6">
          <div className="w-11 h-11 rounded-xl bg-vx-blue flex items-center justify-center text-xl font-extrabold">
            📍
          </div>
          <h1 className="text-2xl font-extrabold tracking-tight">
            Vertex<span className="text-vx-blue">Location</span>
          </h1>
        </div>

        <h2 className="text-lg font-semibold mb-1">Nueva contraseña</h2>
        <p className="text-xs text-vx-muted mb-4">Crea una contraseña nueva para tu cuenta.</p>

        {!token ? (
          <p className="text-sm text-vx-danger">
            Enlace inválido: falta el token. Solicita un nuevo enlace desde “¿Olvidaste tu contraseña?”.
          </p>
        ) : (
          <form onSubmit={submit} className="space-y-3">
            <input
              className="vx-input"
              type="password"
              autoComplete="new-password"
              placeholder="Nueva contraseña"
              value={pwd}
              onChange={(e) => setPwd(e.target.value)}
              required
            />
            <input
              className="vx-input"
              type="password"
              autoComplete="new-password"
              placeholder="Repite la contraseña"
              value={pwd2}
              onChange={(e) => setPwd2(e.target.value)}
              required
            />

            {okMsg && <p className="text-sm text-vx-success">{okMsg}</p>}
            {error && <p className="text-sm text-vx-danger">{error}</p>}

            <button className="vx-btn w-full" disabled={loading || Boolean(okMsg)}>
              {loading ? 'Guardando…' : 'Cambiar contraseña'}
            </button>
          </form>
        )}

        <p className="text-sm text-vx-muted mt-4 text-center">
          <button
            type="button"
            className="text-vx-blueLight font-semibold"
            onClick={() => navigate('/login')}
          >
            ← Volver a iniciar sesión
          </button>
        </p>
      </div>
    </div>
  );
}

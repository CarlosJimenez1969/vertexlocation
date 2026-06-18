import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { authApi } from '../api/client';

export default function Login() {
  const { login, register } = useAuth();
  const navigate = useNavigate();
  const [modo, setModo] = useState('login'); // login | registro | forgot
  const [form, setForm] = useState({ nombre: '', email: '', password: '', telefono: '' });
  const [error, setError] = useState('');
  const [okMsg, setOkMsg] = useState('');
  const [loading, setLoading] = useState(false);

  const onChange = (e) => setForm({ ...form, [e.target.name]: e.target.value });

  const irA = (nuevoModo) => {
    setError('');
    setOkMsg('');
    setModo(nuevoModo);
  };

  const submit = async (e) => {
    e.preventDefault();
    setError('');
    setOkMsg('');
    setLoading(true);
    try {
      if (modo === 'login') {
        await login(form.email, form.password);
        navigate('/');
      } else if (modo === 'registro') {
        await register(form);
        // Tras registrarse NO se entra al sistema: se pasa a iniciar sesión.
        setModo('login');
        setOkMsg('¡Cuenta creada con éxito! Inicia sesión para continuar.');
        setForm((f) => ({ ...f, password: '', nombre: '', telefono: '' }));
      } else {
        // forgot: pedir enlace de restablecimiento por correo.
        await authApi.forgotPassword(form.email);
        setOkMsg('Si el correo está registrado, te enviamos un enlace para restablecer tu contraseña.');
      }
    } catch (err) {
      setError(err.response?.data?.detail || 'Ocurrió un error. Inténtalo de nuevo.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="h-full flex items-center justify-center bg-vx-bg px-4">
      <div className="w-full max-w-md vx-card p-8 shadow-glow">
        {/* Logo */}
        <div className="flex items-center gap-3 mb-6">
          <div className="w-11 h-11 rounded-xl bg-vx-blue flex items-center justify-center text-xl font-extrabold">
            📍
          </div>
          <div>
            <h1 className="text-2xl font-extrabold tracking-tight">
              Vertex<span className="text-vx-blue">Location</span>
            </h1>
            <p className="text-xs text-vx-muted">Rastreo GPS inteligente · Ecuador</p>
          </div>
        </div>

        <h2 className="text-lg font-semibold mb-1">
          {modo === 'login'
            ? 'Inicia sesión'
            : modo === 'registro'
            ? 'Crea tu cuenta'
            : 'Recupera tu contraseña'}
        </h2>
        {modo === 'forgot' && (
          <p className="text-xs text-vx-muted mb-4">
            Ingresa tu correo y te enviaremos un enlace para crear una nueva contraseña.
          </p>
        )}
        {modo !== 'forgot' && <div className="mb-4" />}

        <form onSubmit={submit} className="space-y-3">
          {modo === 'registro' && (
            <input
              className="vx-input"
              name="nombre"
              autoComplete="name"
              placeholder="Nombre completo"
              value={form.nombre}
              onChange={onChange}
              required
            />
          )}
          <input
            className="vx-input"
            type="email"
            name="email"
            autoComplete="email"
            placeholder="correo@ejemplo.com"
            value={form.email}
            onChange={onChange}
            required
          />
          {modo !== 'forgot' && (
            <input
              className="vx-input"
              type="password"
              name="password"
              autoComplete={modo === 'registro' ? 'new-password' : 'current-password'}
              placeholder="Contraseña"
              value={form.password}
              onChange={onChange}
              required
            />
          )}
          {modo === 'login' && (
            <div className="text-right -mt-1">
              <button
                type="button"
                className="text-xs text-vx-blueLight hover:text-vx-blue"
                onClick={() => irA('forgot')}
              >
                ¿Olvidaste tu contraseña?
              </button>
            </div>
          )}
          {modo === 'registro' && (
            <input
              className="vx-input"
              type="tel"
              name="telefono"
              autoComplete="tel"
              inputMode="tel"
              placeholder="WhatsApp (+593...)"
              value={form.telefono}
              onChange={onChange}
            />
          )}

          {okMsg && <p className="text-sm text-vx-success">{okMsg}</p>}
          {error && <p className="text-sm text-vx-danger">{error}</p>}

          <button className="vx-btn w-full" disabled={loading}>
            {loading
              ? 'Procesando…'
              : modo === 'login'
              ? 'Entrar'
              : modo === 'registro'
              ? 'Registrarme'
              : 'Enviar enlace'}
          </button>
        </form>

        <p className="text-sm text-vx-muted mt-4 text-center">
          {modo === 'forgot' ? (
            <button
              type="button"
              className="text-vx-blueLight font-semibold"
              onClick={() => irA('login')}
            >
              ← Volver a iniciar sesión
            </button>
          ) : (
            <>
              {modo === 'login' ? '¿No tienes cuenta?' : '¿Ya tienes cuenta?'}{' '}
              <button
                type="button"
                className="text-vx-blueLight font-semibold"
                onClick={() => irA(modo === 'login' ? 'registro' : 'login')}
              >
                {modo === 'login' ? 'Regístrate' : 'Inicia sesión'}
              </button>
            </>
          )}
        </p>
      </div>
    </div>
  );
}

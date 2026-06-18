import { Navigate, Route, Routes } from 'react-router-dom';
import { useAuth } from './context/AuthContext';
import Login from './pages/Login';
import ResetPassword from './pages/ResetPassword';
import Dashboard from './pages/Dashboard';
import AdminPanel from './components/Admin/AdminPanel';

function Protected({ children }) {
  const { user, loading } = useAuth();
  if (loading) {
    return (
      <div className="h-full flex items-center justify-center text-vx-muted">
        Cargando…
      </div>
    );
  }
  return user ? children : <Navigate to="/login" replace />;
}

// Según el rol: admin -> panel de administración; cliente -> dashboard (solo lectura).
function Home() {
  const { isAdmin } = useAuth();
  return isAdmin ? <AdminPanel /> : <Dashboard />;
}

export default function App() {
  return (
    <Routes>
      <Route path="/login" element={<Login />} />
      <Route path="/reset-password" element={<ResetPassword />} />
      <Route
        path="/"
        element={
          <Protected>
            <Home />
          </Protected>
        }
      />
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  );
}

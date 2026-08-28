import { Navigate, Outlet } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';

export function ProtectedRoute() {
  const { me, loading } = useAuth();

  if (loading) {
    return <div>Loading…</div>;
  }

  if (!me) {
    return <Navigate to="/login" replace />;
  }

  return <Outlet />;
}

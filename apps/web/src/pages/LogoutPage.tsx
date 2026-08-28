import { useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';

export function LogoutPage() {
  const navigate = useNavigate();
  const { logout } = useAuth();

  useEffect(() => {
    logout().then(() => navigate('/login', { replace: true }));
  }, [logout, navigate]);

  return <div>Signing out…</div>;
}

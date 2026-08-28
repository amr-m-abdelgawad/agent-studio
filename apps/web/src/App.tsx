import { Navigate, Route, Routes } from 'react-router-dom';
import { ProtectedRoute } from './components/ProtectedRoute';
import { WorkspacePanel } from './components/WorkspacePanel';
import { useAuth } from './context/AuthContext';
import { AgentsPage } from './pages/AgentsPage';
import { InvitePage } from './pages/InvitePage';
import { LoginPage } from './pages/LoginPage';
import { LogoutPage } from './pages/LogoutPage';
import { OrgInvitePage } from './pages/OrgInvitePage';
import { RunsPage } from './pages/RunsPage';
import { ShellLayout } from './pages/ShellLayout';

function HomePage() {
  return (
    <>
      <AgentsPage />
      <WorkspacePanel />
    </>
  );
}

function RootRedirect() {
  const { me, loading } = useAuth();
  if (loading) return <div>Loading…</div>;
  if (!me) return <Navigate to="/login" replace />;
  return <Navigate to="/" replace />;
}

export default function App() {
  return (
    <Routes>
      <Route path="/login" element={<LoginPage />} />
      <Route path="/invite/:token" element={<InvitePage />} />
      <Route path="/logout" element={<LogoutPage />} />
      <Route element={<ProtectedRoute />}>
        <Route element={<ShellLayout />}>
          <Route index element={<HomePage />} />
          <Route path="runs" element={<RunsPage />} />
          <Route path="invite" element={<OrgInvitePage />} />
        </Route>
      </Route>
      <Route path="*" element={<RootRedirect />} />
    </Routes>
  );
}

import { NavLink, Outlet } from 'react-router-dom';
import { WorkspaceSwitcher } from '../components/WorkspaceSwitcher';
import { useAuth } from '../context/AuthContext';
import { useWorkspace } from '../context/WorkspaceContext';

function canInvite(orgRole: string): boolean {
  return orgRole === 'owner' || orgRole === 'admin';
}

export function ShellLayout() {
  const { me } = useAuth();
  const { currentWorkspaceName, currentWorkspaceRole } = useWorkspace();

  if (!me) return null;

  return (
    <div className="shell">
      <aside className="shell-sidebar">
        <h2>Agent Studio</h2>
        <WorkspaceSwitcher />
        <nav className="shell-nav">
          <NavLink to="/" end data-testid="nav-agents">
            Agents
          </NavLink>
          <NavLink to="/runs" data-testid="nav-runs">
            Runs
          </NavLink>
          {canInvite(me.org_role) && (
            <NavLink to="/invite" data-testid="nav-invite">
              Invite
            </NavLink>
          )}
        </nav>
        <NavLink to="/logout" className="logout-link" data-testid="logout">
          Log out
        </NavLink>
      </aside>
      <main className="shell-main">
        <div className="shell-header">
          <div>
            <h1>{currentWorkspaceName ?? 'Workspace'}</h1>
            {currentWorkspaceRole && (
              <div className="workspace-info">Role: {currentWorkspaceRole}</div>
            )}
            {currentWorkspaceRole === null && canInvite(me.org_role) && (
              <div className="workspace-info">Role: org admin (no membership)</div>
            )}
          </div>
        </div>
        <Outlet />
      </main>
    </div>
  );
}

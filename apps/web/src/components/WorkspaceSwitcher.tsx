import { useWorkspace } from '../context/WorkspaceContext';
import { useAuth } from '../context/AuthContext';

export function WorkspaceSwitcher() {
  const { me } = useAuth();
  const { workspaceId, setWorkspaceId } = useWorkspace();

  if (!me || me.workspaces.length === 0) return null;

  return (
    <div className="workspace-switcher" data-testid="workspace-switcher">
      <select
        value={workspaceId ?? ''}
        onChange={(e) => setWorkspaceId(e.target.value)}
        aria-label="Workspace"
      >
        {me.workspaces.map((ws) => (
          <option key={ws.id} value={ws.id}>
            {ws.name}
          </option>
        ))}
      </select>
    </div>
  );
}

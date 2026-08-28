import { useEffect, useState } from 'react';
import { api } from '../api/client';
import type { WorkspaceMember } from '../api/types';
import { useAuth } from '../context/AuthContext';
import { useWorkspace } from '../context/WorkspaceContext';

function canCreateWorkspace(orgRole: string): boolean {
  return orgRole === 'owner' || orgRole === 'admin';
}

export function WorkspacePanel() {
  const { me, refresh } = useAuth();
  const { workspaceId } = useWorkspace();
  const [members, setMembers] = useState<WorkspaceMember[]>([]);
  const [newName, setNewName] = useState('');
  const [creating, setCreating] = useState(false);

  useEffect(() => {
    if (!workspaceId) {
      setMembers([]);
      return;
    }
    api.listMembers(workspaceId).then(setMembers).catch(() => setMembers([]));
  }, [workspaceId]);

  if (!me) return null;

  async function handleCreate() {
    if (!newName.trim()) return;
    setCreating(true);
    try {
      await api.createWorkspace({ name: newName.trim() });
      setNewName('');
      await refresh();
    } finally {
      setCreating(false);
    }
  }

  return (
    <div>
      {canCreateWorkspace(me.org_role) && (
        <div className="create-workspace">
          <input
            type="text"
            placeholder="New workspace name"
            value={newName}
            onChange={(e) => setNewName(e.target.value)}
          />
          <button type="button" onClick={handleCreate} disabled={creating}>
            Create workspace
          </button>
        </div>
      )}
      {workspaceId && members.length > 0 && (
        <div className="members-list">
          <h3>Members</h3>
          <ul>
            {members.map((m) => (
              <li key={m.user_id}>
                {m.email} — {m.role}
              </li>
            ))}
          </ul>
        </div>
      )}
    </div>
  );
}

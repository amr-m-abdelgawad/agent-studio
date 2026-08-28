import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useState,
  type ReactNode,
} from 'react';
import { useAuth } from './AuthContext';

interface WorkspaceContextValue {
  workspaceId: string | null;
  setWorkspaceId: (id: string) => void;
  currentWorkspaceName: string | null;
  currentWorkspaceRole: string | null;
}

const WorkspaceContext = createContext<WorkspaceContextValue | null>(null);

export function WorkspaceProvider({ children }: { children: ReactNode }) {
  const { me } = useAuth();
  const [workspaceId, setWorkspaceIdState] = useState<string | null>(null);

  useEffect(() => {
    if (!me || me.workspaces.length === 0) {
      setWorkspaceIdState(null);
      return;
    }
    if (!workspaceId || !me.workspaces.some((w) => w.id === workspaceId)) {
      setWorkspaceIdState(me.workspaces[0].id);
    }
  }, [me, workspaceId]);

  const setWorkspaceId = useCallback((id: string) => {
    setWorkspaceIdState(id);
  }, []);

  const current = me?.workspaces.find((w) => w.id === workspaceId) ?? null;

  const value = useMemo(
    () => ({
      workspaceId,
      setWorkspaceId,
      currentWorkspaceName: current?.name ?? null,
      currentWorkspaceRole: current?.role ?? null,
    }),
    [workspaceId, setWorkspaceId, current],
  );

  return (
    <WorkspaceContext.Provider value={value}>{children}</WorkspaceContext.Provider>
  );
}

export function useWorkspace(): WorkspaceContextValue {
  const ctx = useContext(WorkspaceContext);
  if (!ctx) throw new Error('useWorkspace must be used within WorkspaceProvider');
  return ctx;
}

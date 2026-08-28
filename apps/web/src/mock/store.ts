import type { OrgRole, WorkspaceRole } from '../api/types';

export interface UserRecord {
  id: string;
  email: string;
  password: string;
  orgId: string;
  orgRole: OrgRole;
}

export interface OrgRecord {
  id: string;
  name: string;
}

export interface WorkspaceRecord {
  id: string;
  name: string;
  orgId: string;
  require_publish_approval: boolean;
}

export interface WorkspaceMemberRecord {
  workspaceId: string;
  userId: string;
  role: WorkspaceRole;
}

export interface InviteRecord {
  id: string;
  token: string;
  email: string;
  role: OrgRole;
  orgId: string;
  used: boolean;
  expired: boolean;
}

export interface MockStore {
  users: UserRecord[];
  orgs: OrgRecord[];
  workspaces: WorkspaceRecord[];
  members: WorkspaceMemberRecord[];
  invites: InviteRecord[];
  sessions: Map<string, string>;
}

const ORG_ID = 'org-1';
const OWNER_ID = 'user-owner';
const EDITOR_ID = 'user-editor';
const WS_ALPHA_ID = 'ws-alpha';
const WS_BRAVO_ID = 'ws-bravo';

export function createSeedStore(): MockStore {
  return {
    orgs: [{ id: ORG_ID, name: 'Example Org' }],
    users: [
      {
        id: OWNER_ID,
        email: 'owner@example.com',
        password: 'password123!',
        orgId: ORG_ID,
        orgRole: 'owner',
      },
      {
        id: EDITOR_ID,
        email: 'editor@example.com',
        password: 'password123!',
        orgId: ORG_ID,
        orgRole: 'editor',
      },
    ],
    workspaces: [
      {
        id: WS_ALPHA_ID,
        name: 'Alpha',
        orgId: ORG_ID,
        require_publish_approval: false,
      },
      {
        id: WS_BRAVO_ID,
        name: 'Bravo',
        orgId: ORG_ID,
        require_publish_approval: false,
      },
    ],
    members: [
      { workspaceId: WS_ALPHA_ID, userId: OWNER_ID, role: 'owner' },
      { workspaceId: WS_BRAVO_ID, userId: OWNER_ID, role: 'owner' },
      { workspaceId: WS_ALPHA_ID, userId: EDITOR_ID, role: 'editor' },
    ],
    invites: [],
    sessions: new Map(),
  };
}

let store: MockStore = createSeedStore();

export function getStore(): MockStore {
  return store;
}

export function resetStore(): void {
  store = createSeedStore();
}

export function generateId(prefix: string): string {
  return `${prefix}-${crypto.randomUUID().slice(0, 8)}`;
}

export function generateToken(): string {
  return crypto.randomUUID().replace(/-/g, '');
}

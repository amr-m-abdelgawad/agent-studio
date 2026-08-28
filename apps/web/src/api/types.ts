export type OrgRole = 'owner' | 'admin' | 'editor' | 'viewer' | 'runner';
export type WorkspaceRole = OrgRole;

export interface ApiError {
  error: {
    code: string;
    message: string;
  };
}

export interface WorkspaceSummary {
  id: string;
  name: string;
  role: WorkspaceRole | null;
}

export interface Me {
  id: string;
  email: string;
  org: {
    id: string;
    name: string;
  };
  org_role: OrgRole;
  workspaces: WorkspaceSummary[];
}

export interface Workspace {
  id: string;
  name: string;
  require_publish_approval: boolean;
}

export interface WorkspaceMember {
  user_id: string;
  email: string;
  role: WorkspaceRole;
}

export interface OrgInvite {
  id: string;
  email: string;
  role: OrgRole;
  dev_token?: string;
}

export interface LoginRequest {
  email: string;
  password: string;
}

export interface AcceptInviteRequest {
  token: string;
  password: string;
}

export interface CreateInviteRequest {
  email: string;
  role: OrgRole;
}

export interface CreateWorkspaceRequest {
  name: string;
}

export interface AddMemberRequest {
  email: string;
  role: WorkspaceRole;
}

export interface UpdateMemberRequest {
  role: WorkspaceRole;
}

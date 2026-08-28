import type {
  AcceptInviteRequest,
  ApiError,
  CreateInviteRequest,
  CreateWorkspaceRequest,
  Me,
  OrgInvite,
  Workspace,
  WorkspaceMember,
  AddMemberRequest,
  UpdateMemberRequest,
  LoginRequest,
} from './types';

async function request<T>(
  path: string,
  options: RequestInit = {},
): Promise<T> {
  const response = await fetch(path, {
    ...options,
    credentials: 'include',
    headers: {
      'Content-Type': 'application/json',
      ...options.headers,
    },
  });

  const body = await response.json().catch(() => ({}));

  if (!response.ok) {
    const error = body as ApiError;
    throw Object.assign(new Error(error.error?.message ?? 'Request failed'), {
      code: error.error?.code ?? 'unknown',
      status: response.status,
      apiError: error,
    });
  }

  return body as T;
}

export const api = {
  login(data: LoginRequest): Promise<Me> {
    return request<Me>('/v1/auth/login', {
      method: 'POST',
      body: JSON.stringify(data),
    });
  },

  logout(): Promise<{ ok: boolean }> {
    return request<{ ok: boolean }>('/v1/auth/logout', { method: 'POST' });
  },

  me(): Promise<Me> {
    return request<Me>('/v1/me');
  },

  acceptInvite(data: AcceptInviteRequest): Promise<Me> {
    return request<Me>('/v1/auth/accept-invite', {
      method: 'POST',
      body: JSON.stringify(data),
    });
  },

  createOrgInvite(data: CreateInviteRequest): Promise<OrgInvite> {
    return request<OrgInvite>('/v1/org/invites', {
      method: 'POST',
      body: JSON.stringify(data),
    });
  },

  listWorkspaces(): Promise<Workspace[]> {
    return request<Workspace[]>('/v1/workspaces');
  },

  getWorkspace(id: string): Promise<Workspace> {
    return request<Workspace>(`/v1/workspaces/${id}`);
  },

  createWorkspace(data: CreateWorkspaceRequest): Promise<Workspace> {
    return request<Workspace>('/v1/workspaces', {
      method: 'POST',
      body: JSON.stringify(data),
    });
  },

  listMembers(workspaceId: string): Promise<WorkspaceMember[]> {
    return request<WorkspaceMember[]>(`/v1/workspaces/${workspaceId}/members`);
  },

  addMember(workspaceId: string, data: AddMemberRequest): Promise<WorkspaceMember> {
    return request<WorkspaceMember>(`/v1/workspaces/${workspaceId}/members`, {
      method: 'POST',
      body: JSON.stringify(data),
    });
  },

  updateMember(
    workspaceId: string,
    userId: string,
    data: UpdateMemberRequest,
  ): Promise<WorkspaceMember> {
    return request<WorkspaceMember>(
      `/v1/workspaces/${workspaceId}/members/${userId}`,
      {
        method: 'PATCH',
        body: JSON.stringify(data),
      },
    );
  },

  removeMember(workspaceId: string, userId: string): Promise<{ ok: boolean }> {
    return request<{ ok: boolean }>(
      `/v1/workspaces/${workspaceId}/members/${userId}`,
      { method: 'DELETE' },
    );
  },
};

export type ApiClientError = Error & {
  code: string;
  status: number;
  apiError: ApiError;
};

export function isApiError(error: unknown): error is ApiClientError {
  return error instanceof Error && 'code' in error;
}

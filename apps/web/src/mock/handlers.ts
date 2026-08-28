import type { IncomingMessage, ServerResponse } from 'node:http';
import type { OrgRole, WorkspaceRole } from '../api/types';
import {
  generateId,
  generateToken,
  getStore,
  resetStore,
  type UserRecord,
} from './store';

const SESSION_COOKIE = 'studio_session';
const MIN_PASSWORD_LENGTH = 12;

function parseCookies(header: string | undefined): Record<string, string> {
  if (!header) return {};
  return Object.fromEntries(
    header.split(';').map((part) => {
      const [key, ...rest] = part.trim().split('=');
      return [key, rest.join('=')];
    }),
  );
}

function setSessionCookie(res: ServerResponse, sessionId: string): void {
  res.setHeader(
    'Set-Cookie',
    `${SESSION_COOKIE}=${sessionId}; Path=/; HttpOnly; SameSite=Lax`,
  );
}

function clearSessionCookie(res: ServerResponse): void {
  res.setHeader(
    'Set-Cookie',
    `${SESSION_COOKIE}=; Path=/; HttpOnly; SameSite=Lax; Max-Age=0`,
  );
}

function getSessionUser(req: IncomingMessage): UserRecord | null {
  const cookies = parseCookies(req.headers.cookie);
  const sessionId = cookies[SESSION_COOKIE];
  if (!sessionId) return null;
  const store = getStore();
  const userId = store.sessions.get(sessionId);
  if (!userId) return null;
  return store.users.find((u) => u.id === userId) ?? null;
}

function sendJson(
  res: ServerResponse,
  status: number,
  body: unknown,
): void {
  res.statusCode = status;
  res.setHeader('Content-Type', 'application/json');
  res.end(JSON.stringify(body));
}

function sendError(
  res: ServerResponse,
  status: number,
  code: string,
  message: string,
): void {
  sendJson(res, status, { error: { code, message } });
}

function isOrgAdmin(role: OrgRole): boolean {
  return role === 'owner' || role === 'admin';
}

function buildMe(user: UserRecord) {
  const store = getStore();
  const org = store.orgs.find((o) => o.id === user.orgId)!;
  let workspaces;

  if (isOrgAdmin(user.orgRole)) {
    workspaces = store.workspaces
      .filter((w) => w.orgId === user.orgId)
      .map((w) => {
        const membership = store.members.find(
          (m) => m.workspaceId === w.id && m.userId === user.id,
        );
        return {
          id: w.id,
          name: w.name,
          role: membership?.role ?? null,
        };
      });
  } else {
    workspaces = store.members
      .filter((m) => m.userId === user.id)
      .map((m) => {
        const ws = store.workspaces.find((w) => w.id === m.workspaceId)!;
        return { id: ws.id, name: ws.name, role: m.role };
      });
  }

  return {
    id: user.id,
    email: user.email,
    org: { id: org.id, name: org.name },
    org_role: user.orgRole,
    workspaces,
  };
}

function canAccessWorkspace(user: UserRecord, workspaceId: string): boolean {
  const store = getStore();
  const workspace = store.workspaces.find((w) => w.id === workspaceId);
  if (!workspace || workspace.orgId !== user.orgId) return false;
  if (isOrgAdmin(user.orgRole)) return true;
  return store.members.some(
    (m) => m.workspaceId === workspaceId && m.userId === user.id,
  );
}

async function readBody(req: IncomingMessage): Promise<unknown> {
  const chunks: Buffer[] = [];
  for await (const chunk of req) {
    chunks.push(Buffer.from(chunk));
  }
  if (chunks.length === 0) return {};
  return JSON.parse(Buffer.concat(chunks).toString('utf8'));
}

export async function handleMockRequest(
  req: IncomingMessage,
  res: ServerResponse,
  url: URL,
): Promise<boolean> {
  if (!url.pathname.startsWith('/v1')) return false;

  const method = req.method ?? 'GET';
  const path = url.pathname;

  if (method === 'POST' && path === '/v1/_test/reset') {
    resetStore();
    sendJson(res, 200, { ok: true });
    return true;
  }

  if (method === 'POST' && path === '/v1/auth/login') {
    const body = (await readBody(req)) as { email?: string; password?: string };
    const store = getStore();
    const user = store.users.find(
      (u) => u.email === body.email && u.password === body.password,
    );
    if (!user) {
      sendError(res, 401, 'invalid_credentials', 'Invalid email or password');
      return true;
    }
    const sessionId = generateToken();
    store.sessions.set(sessionId, user.id);
    setSessionCookie(res, sessionId);
    sendJson(res, 200, buildMe(user));
    return true;
  }

  if (method === 'POST' && path === '/v1/auth/logout') {
    const cookies = parseCookies(req.headers.cookie);
    const sessionId = cookies[SESSION_COOKIE];
    if (sessionId) {
      getStore().sessions.delete(sessionId);
    }
    clearSessionCookie(res);
    sendJson(res, 200, { ok: true });
    return true;
  }

  if (method === 'GET' && path === '/v1/me') {
    const user = getSessionUser(req);
    if (!user) {
      sendError(res, 401, 'unauthorized', 'Not authenticated');
      return true;
    }
    sendJson(res, 200, buildMe(user));
    return true;
  }

  if (method === 'POST' && path === '/v1/org/invites') {
    const user = getSessionUser(req);
    if (!user) {
      sendError(res, 401, 'unauthorized', 'Not authenticated');
      return true;
    }
    if (!isOrgAdmin(user.orgRole)) {
      sendError(res, 403, 'forbidden', 'Forbidden');
      return true;
    }
    const body = (await readBody(req)) as { email?: string; role?: OrgRole };
    const store = getStore();
    const token = generateToken();
    const invite = {
      id: generateId('invite'),
      token,
      email: body.email ?? '',
      role: body.role ?? 'editor',
      orgId: user.orgId,
      used: false,
      expired: false,
    };
    store.invites.push(invite);
    sendJson(res, 201, {
      id: invite.id,
      email: invite.email,
      role: invite.role,
      dev_token: token,
    });
    return true;
  }

  if (method === 'POST' && path === '/v1/auth/accept-invite') {
    const body = (await readBody(req)) as { token?: string; password?: string };
    const password = body.password ?? '';
    if (password.length < MIN_PASSWORD_LENGTH) {
      sendError(res, 422, 'password_too_short', 'Password must be at least 12 characters');
      return true;
    }
    const store = getStore();
    const invite = store.invites.find((i) => i.token === body.token);
    if (!invite) {
      sendError(res, 410, 'invite_expired', 'Invite has expired');
      return true;
    }
    if (invite.expired) {
      sendError(res, 410, 'invite_expired', 'Invite has expired');
      return true;
    }
    if (invite.used) {
      sendError(res, 409, 'invite_used', 'Invite has already been used');
      return true;
    }
    const existing = store.users.find((u) => u.email === invite.email);
    if (existing) {
      sendError(res, 409, 'email_taken', 'Email is already taken');
      return true;
    }
    const newUser: UserRecord = {
      id: generateId('user'),
      email: invite.email,
      password,
      orgId: invite.orgId,
      orgRole: invite.role,
    };
    store.users.push(newUser);
    invite.used = true;
    const sessionId = generateToken();
    store.sessions.set(sessionId, newUser.id);
    setSessionCookie(res, sessionId);
    sendJson(res, 201, buildMe(newUser));
    return true;
  }

  if (method === 'GET' && path === '/v1/workspaces') {
    const user = getSessionUser(req);
    if (!user) {
      sendError(res, 401, 'unauthorized', 'Not authenticated');
      return true;
    }
    const store = getStore();
    const workspaces = isOrgAdmin(user.orgRole)
      ? store.workspaces.filter((w) => w.orgId === user.orgId)
      : store.members
          .filter((m) => m.userId === user.id)
          .map((m) => store.workspaces.find((w) => w.id === m.workspaceId)!)
          .filter(Boolean);
    sendJson(
      res,
      200,
      workspaces.map((w) => ({
        id: w.id,
        name: w.name,
        require_publish_approval: w.require_publish_approval,
      })),
    );
    return true;
  }

  if (method === 'POST' && path === '/v1/workspaces') {
    const user = getSessionUser(req);
    if (!user) {
      sendError(res, 401, 'unauthorized', 'Not authenticated');
      return true;
    }
    if (!isOrgAdmin(user.orgRole)) {
      sendError(res, 403, 'forbidden', 'Forbidden');
      return true;
    }
    const body = (await readBody(req)) as { name?: string };
    const store = getStore();
    const workspace = {
      id: generateId('ws'),
      name: body.name ?? 'New Workspace',
      orgId: user.orgId,
      require_publish_approval: false,
    };
    store.workspaces.push(workspace);
    store.members.push({
      workspaceId: workspace.id,
      userId: user.id,
      role: 'owner',
    });
    sendJson(res, 201, {
      id: workspace.id,
      name: workspace.name,
      require_publish_approval: workspace.require_publish_approval,
    });
    return true;
  }

  const workspaceMatch = path.match(/^\/v1\/workspaces\/([^/]+)$/);
  if (workspaceMatch) {
    const workspaceId = workspaceMatch[1];
    const user = getSessionUser(req);
    if (!user) {
      sendError(res, 401, 'unauthorized', 'Not authenticated');
      return true;
    }
    if (!canAccessWorkspace(user, workspaceId)) {
      sendError(res, 404, 'not_found', 'Workspace not found');
      return true;
    }
    const store = getStore();
    const workspace = store.workspaces.find((w) => w.id === workspaceId)!;
    if (method === 'GET') {
      sendJson(res, 200, {
        id: workspace.id,
        name: workspace.name,
        require_publish_approval: workspace.require_publish_approval,
      });
      return true;
    }
  }

  const membersMatch = path.match(/^\/v1\/workspaces\/([^/]+)\/members$/);
  if (membersMatch) {
    const workspaceId = membersMatch[1];
    const user = getSessionUser(req);
    if (!user) {
      sendError(res, 401, 'unauthorized', 'Not authenticated');
      return true;
    }
    if (!canAccessWorkspace(user, workspaceId)) {
      sendError(res, 404, 'not_found', 'Workspace not found');
      return true;
    }
    const store = getStore();

    if (method === 'GET') {
      const members = store.members
        .filter((m) => m.workspaceId === workspaceId)
        .map((m) => {
          const u = store.users.find((usr) => usr.id === m.userId)!;
          return { user_id: u.id, email: u.email, role: m.role };
        });
      sendJson(res, 200, members);
      return true;
    }

    if (method === 'POST') {
      const body = (await readBody(req)) as { email?: string; role?: WorkspaceRole };
      const target = store.users.find((u) => u.email === body.email);
      if (!target) {
        sendError(res, 404, 'not_found', 'User not found');
        return true;
      }
      const existing = store.members.find(
        (m) => m.workspaceId === workspaceId && m.userId === target.id,
      );
      if (existing) {
        sendError(res, 409, 'already_member', 'User is already a member');
        return true;
      }
      const member = {
        workspaceId,
        userId: target.id,
        role: body.role ?? 'editor',
      };
      store.members.push(member);
      sendJson(res, 201, {
        user_id: target.id,
        email: target.email,
        role: member.role,
      });
      return true;
    }
  }

  const memberMatch = path.match(
    /^\/v1\/workspaces\/([^/]+)\/members\/([^/]+)$/,
  );
  if (memberMatch) {
    const workspaceId = memberMatch[1];
    const memberUserId = memberMatch[2];
    const user = getSessionUser(req);
    if (!user) {
      sendError(res, 401, 'unauthorized', 'Not authenticated');
      return true;
    }
    if (!canAccessWorkspace(user, workspaceId)) {
      sendError(res, 404, 'not_found', 'Workspace not found');
      return true;
    }
    const store = getStore();
    const memberIdx = store.members.findIndex(
      (m) => m.workspaceId === workspaceId && m.userId === memberUserId,
    );
    if (memberIdx === -1) {
      sendError(res, 404, 'not_found', 'Member not found');
      return true;
    }

    if (method === 'PATCH') {
      const body = (await readBody(req)) as { role?: WorkspaceRole };
      store.members[memberIdx].role = body.role ?? store.members[memberIdx].role;
      const target = store.users.find((u) => u.id === memberUserId)!;
      sendJson(res, 200, {
        user_id: target.id,
        email: target.email,
        role: store.members[memberIdx].role,
      });
      return true;
    }

    if (method === 'DELETE') {
      store.members.splice(memberIdx, 1);
      sendJson(res, 200, { ok: true });
      return true;
    }
  }

  sendError(res, 404, 'not_found', 'Not found');
  return true;
}

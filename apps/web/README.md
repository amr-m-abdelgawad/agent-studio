# @agent-studio/web

M0 frontend (FE-01 auth + FE-02 workspaces) for Agent Studio.

## Prerequisites

- Node.js >= 22 (see repo `.nvmrc`)

## Dev server

```bash
cd apps/web
npm install
npm run dev
```

Opens at **http://localhost:5173** (Vite default). All `/v1` API routes are mocked in-process via a Vite dev middleware plugin (same origin as Playwright).

Authentication uses an httpOnly `studio_session` cookie. The client always sends `credentials: 'include'`.

## Seed accounts

| Email | Password | Org role | Workspaces |
|---|---|---|---|
| `owner@example.com` | `password123!` | owner | Alpha (owner), Bravo (owner) |
| `editor@example.com` | `password123!` | editor | Alpha (editor) |

## Routes

| Path | Description |
|---|---|
| `/login` | Email/password sign-in |
| `/invite/:token` | Accept org invite and set password |
| `/logout` | Clear session and redirect to login |
| `/` | Auth-gated shell (Agents placeholder) |
| `/runs` | Runs placeholder |
| `/invite` | Org invite form (owner/admin only) |

## Tests

```bash
npm test          # Vitest component tests (error codes)
npm run test:e2e  # Playwright e2e (starts dev server)
```

## Hard constraints

- No canvas / reactflow / `/canvas` / M2
- No unversioned `/auth/login`
- No localStorage session or password storage
- Cookie-based session only (`studio_session`, httpOnly)

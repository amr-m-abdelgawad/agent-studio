import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { MemoryRouter, Route, Routes } from 'react-router-dom';
import { beforeEach, describe, expect, it, vi } from 'vitest';
import { api } from '../api/client';
import { AuthProvider } from '../context/AuthContext';
import { WorkspaceProvider } from '../context/WorkspaceContext';
import { InvitePage } from '../pages/InvitePage';
import { LoginPage } from '../pages/LoginPage';

vi.mock('../api/client', async () => {
  const actual = await vi.importActual<typeof import('../api/client')>('../api/client');
  return {
    ...actual,
    api: {
      login: vi.fn(),
      logout: vi.fn(),
      me: vi.fn(),
      acceptInvite: vi.fn(),
      createOrgInvite: vi.fn(),
      listWorkspaces: vi.fn(),
      getWorkspace: vi.fn(),
      createWorkspace: vi.fn(),
      listMembers: vi.fn(),
      addMember: vi.fn(),
      updateMember: vi.fn(),
      removeMember: vi.fn(),
    },
  };
});

function renderLogin() {
  return render(
    <MemoryRouter>
      <AuthProvider>
        <WorkspaceProvider>
          <LoginPage />
        </WorkspaceProvider>
      </AuthProvider>
    </MemoryRouter>,
  );
}

function renderInvite(token = 'test-token') {
  return render(
    <MemoryRouter initialEntries={[`/invite/${token}`]}>
      <AuthProvider>
        <WorkspaceProvider>
          <Routes>
            <Route path="/invite/:token" element={<InvitePage />} />
          </Routes>
        </WorkspaceProvider>
      </AuthProvider>
    </MemoryRouter>,
  );
}

describe('LoginPage error codes', () => {
  beforeEach(() => {
    vi.mocked(api.me).mockRejectedValue(new Error('unauthorized'));
  });

  it('shows invalid_credentials message', async () => {
    const user = userEvent.setup();
    vi.mocked(api.login).mockRejectedValue(
      Object.assign(new Error('Invalid email or password'), {
        code: 'invalid_credentials',
        status: 401,
        apiError: {
          error: { code: 'invalid_credentials', message: 'Invalid email or password' },
        },
      }),
    );

    renderLogin();
    await user.type(screen.getByTestId('login-email'), 'bad@example.com');
    await user.type(screen.getByTestId('login-password'), 'wrong');
    await user.click(screen.getByTestId('login-submit'));

    await waitFor(() => {
      expect(screen.getByTestId('login-error')).toHaveTextContent(
        'Invalid email or password',
      );
    });
  });
});

describe('InvitePage error codes', () => {
  beforeEach(() => {
    vi.mocked(api.me).mockRejectedValue(new Error('unauthorized'));
  });

  it('shows password_too_short message', async () => {
    const user = userEvent.setup();
    vi.mocked(api.acceptInvite).mockRejectedValue(
      Object.assign(new Error('Password must be at least 12 characters'), {
        code: 'password_too_short',
        status: 422,
        apiError: {
          error: {
            code: 'password_too_short',
            message: 'Password must be at least 12 characters',
          },
        },
      }),
    );

    renderInvite();
    await user.type(screen.getByTestId('invite-password'), 'short');
    await user.click(screen.getByTestId('invite-submit'));

    await waitFor(() => {
      expect(screen.getByTestId('invite-error')).toHaveTextContent(
        'Password must be at least 12 characters',
      );
    });
  });

  it('shows invite_expired message', async () => {
    const user = userEvent.setup();
    vi.mocked(api.acceptInvite).mockRejectedValue(
      Object.assign(new Error('Invite has expired'), {
        code: 'invite_expired',
        status: 410,
        apiError: {
          error: { code: 'invite_expired', message: 'Invite has expired' },
        },
      }),
    );

    renderInvite('expired-token');
    await user.type(screen.getByTestId('invite-password'), 'validpassword1');
    await user.click(screen.getByTestId('invite-submit'));

    await waitFor(() => {
      expect(screen.getByTestId('invite-error')).toHaveTextContent('Invite has expired');
    });
  });

  it('shows invite_used message', async () => {
    const user = userEvent.setup();
    vi.mocked(api.acceptInvite).mockRejectedValue(
      Object.assign(new Error('Invite has already been used'), {
        code: 'invite_used',
        status: 409,
        apiError: {
          error: { code: 'invite_used', message: 'Invite has already been used' },
        },
      }),
    );

    renderInvite('used-token');
    await user.type(screen.getByTestId('invite-password'), 'validpassword1');
    await user.click(screen.getByTestId('invite-submit'));

    await waitFor(() => {
      expect(screen.getByTestId('invite-error')).toHaveTextContent(
        'Invite has already been used',
      );
    });
  });

  it('shows email_taken message', async () => {
    const user = userEvent.setup();
    vi.mocked(api.acceptInvite).mockRejectedValue(
      Object.assign(new Error('Email is already taken'), {
        code: 'email_taken',
        status: 409,
        apiError: {
          error: { code: 'email_taken', message: 'Email is already taken' },
        },
      }),
    );

    renderInvite('taken-token');
    await user.type(screen.getByTestId('invite-password'), 'validpassword1');
    await user.click(screen.getByTestId('invite-submit'));

    await waitFor(() => {
      expect(screen.getByTestId('invite-error')).toHaveTextContent('Email is already taken');
    });
  });
});

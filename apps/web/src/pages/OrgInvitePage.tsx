import { useState, type FormEvent } from 'react';
import { api, isApiError } from '../api/client';
import type { OrgRole } from '../api/types';

export function OrgInvitePage() {
  const [email, setEmail] = useState('');
  const [role, setRole] = useState<OrgRole>('editor');
  const [devToken, setDevToken] = useState('');
  const [error, setError] = useState('');
  const [submitting, setSubmitting] = useState(false);

  async function handleSubmit(e: FormEvent) {
    e.preventDefault();
    setError('');
    setDevToken('');
    setSubmitting(true);
    try {
      const invite = await api.createOrgInvite({ email, role });
      if (invite.dev_token) {
        setDevToken(invite.dev_token);
      }
      setEmail('');
    } catch (err) {
      if (isApiError(err)) {
        setError(err.apiError.error.message);
      } else {
        setError('Failed to create invite');
      }
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <div>
      <h2>Invite to organization</h2>
      {error && <div className="error-message">{error}</div>}
      {devToken && (
        <p>
          Invite link: <code>/invite/{devToken}</code>
        </p>
      )}
      <form onSubmit={handleSubmit}>
        <div className="form-field">
          <label htmlFor="invite-email">Email</label>
          <input
            id="invite-email"
            type="email"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            required
          />
        </div>
        <div className="form-field">
          <label htmlFor="invite-role">Role</label>
          <select
            id="invite-role"
            value={role}
            onChange={(e) => setRole(e.target.value as OrgRole)}
          >
            <option value="admin">Admin</option>
            <option value="editor">Editor</option>
            <option value="viewer">Viewer</option>
            <option value="runner">Runner</option>
          </select>
        </div>
        <button type="submit" className="btn-primary" disabled={submitting}>
          Send invite
        </button>
      </form>
    </div>
  );
}

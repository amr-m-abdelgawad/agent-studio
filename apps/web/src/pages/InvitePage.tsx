import { useState, type FormEvent } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import { api, isApiError } from '../api/client';
import { useAuth } from '../context/AuthContext';

export function InvitePage() {
  const { token } = useParams<{ token: string }>();
  const navigate = useNavigate();
  const { setMe } = useAuth();
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [submitting, setSubmitting] = useState(false);

  async function handleSubmit(e: FormEvent) {
    e.preventDefault();
    if (!token) return;
    setError('');
    setSubmitting(true);
    try {
      const me = await api.acceptInvite({ token, password });
      setMe(me);
      navigate('/', { replace: true });
    } catch (err) {
      if (isApiError(err)) {
        setError(err.apiError.error.message);
      } else {
        setError('Failed to accept invite');
      }
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <div className="auth-page">
      <div className="auth-card">
        <h1>Accept invite</h1>
        {error && (
          <div className="error-message" data-testid="invite-error">
            {error}
          </div>
        )}
        <form onSubmit={handleSubmit}>
          <div className="form-field">
            <label htmlFor="invite-password">Password</label>
            <input
              id="invite-password"
              data-testid="invite-password"
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              required
              minLength={12}
              autoComplete="new-password"
            />
          </div>
          <button
            type="submit"
            className="btn-primary"
            data-testid="invite-submit"
            disabled={submitting}
          >
            Create account
          </button>
        </form>
      </div>
    </div>
  );
}

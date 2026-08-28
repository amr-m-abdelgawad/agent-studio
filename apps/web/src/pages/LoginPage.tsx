import { useState, type FormEvent } from 'react';
import { useNavigate } from 'react-router-dom';
import { api, isApiError } from '../api/client';
import { useAuth } from '../context/AuthContext';

export function LoginPage() {
  const navigate = useNavigate();
  const { setMe } = useAuth();
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [submitting, setSubmitting] = useState(false);

  async function handleSubmit(e: FormEvent) {
    e.preventDefault();
    setError('');
    setSubmitting(true);
    try {
      const me = await api.login({ email, password });
      setMe(me);
      navigate('/', { replace: true });
    } catch (err) {
      if (isApiError(err)) {
        setError(err.apiError.error.message);
      } else {
        setError('Login failed');
      }
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <div className="auth-page">
      <div className="auth-card">
        <h1>Sign in</h1>
        {error && (
          <div className="error-message" data-testid="login-error">
            {error}
          </div>
        )}
        <form onSubmit={handleSubmit}>
          <div className="form-field">
            <label htmlFor="login-email">Email</label>
            <input
              id="login-email"
              data-testid="login-email"
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              required
              autoComplete="email"
            />
          </div>
          <div className="form-field">
            <label htmlFor="login-password">Password</label>
            <input
              id="login-password"
              data-testid="login-password"
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              required
              autoComplete="current-password"
            />
          </div>
          <button
            type="submit"
            className="btn-primary"
            data-testid="login-submit"
            disabled={submitting}
          >
            Sign in
          </button>
        </form>
      </div>
    </div>
  );
}

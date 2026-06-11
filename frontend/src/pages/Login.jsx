import React, { useState, useEffect } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import toast from 'react-hot-toast';
import { useAuth } from '../context/AuthContext';

export default function Login() {
  const { login } = useAuth();
  const navigate = useNavigate();
  const [form, setForm] = useState({ username: '', password: '' });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  useEffect(() => {
    document.body.className = 'state-calm';
    return () => { document.body.className = ''; };
  }, []);

  const handleChange = (e) => {
    setError('');
    setForm((prev) => ({ ...prev, [e.target.name]: e.target.value }));
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!form.username.trim() || !form.password) {
      setError('Please enter your username and password');
      return;
    }
    setLoading(true);
    setError('');
    try {
      const result = await login(form.username.trim(), form.password);
      toast.success('Welcome back!');
      navigate(result.onboardingComplete ? '/dashboard' : '/onboarding/budget', { replace: true });
    } catch (err) {
      setError(err.response?.data?.detail ?? 'Incorrect username or password');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div
      className="min-h-screen flex flex-col items-center justify-center px-5"
      style={{ maxWidth: 390, margin: '0 auto' }}
    >
      <div className="w-full fade-in" style={{ maxWidth: 360, marginTop: 64 }}>
        {/* Heading */}
        <div className="text-center mb-8">
          <h1 style={{ fontSize: 24, fontWeight: 400, marginBottom: 6 }}>welcome back 👋</h1>
          <p style={{ fontSize: 13, color: 'var(--text-muted)' }}>
            your wallet's been waiting
          </p>
        </div>

        {/* Card */}
        <form onSubmit={handleSubmit} className="glass-card p-6 flex flex-col gap-4">
          <div>
            <label className="field-label">Username</label>
            <input
              name="username"
              type="text"
              autoComplete="username"
              placeholder="your username"
              value={form.username}
              onChange={handleChange}
              disabled={loading}
            />
          </div>

          <div>
            <label className="field-label">Password</label>
            <input
              name="password"
              type="password"
              autoComplete="current-password"
              placeholder="••••••••"
              value={form.password}
              onChange={handleChange}
              disabled={loading}
            />
          </div>

          {/* Error */}
          {error && (
            <p style={{ fontSize: 12, color: '#E63946', marginTop: -8 }} role="alert">
              {error}
            </p>
          )}

          {/* Submit */}
          <button
            type="submit"
            disabled={loading}
            style={{
              width: '100%',
              height: 48,
              marginTop: 4,
              background: loading ? 'var(--accent-muted)' : 'var(--accent)',
              color: '#050D1A',
              fontWeight: 600,
              fontSize: 14,
              borderRadius: 14,
              border: 'none',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              gap: 8,
            }}
          >
            {loading ? (
              <>
                <Spinner />
                logging in...
              </>
            ) : (
              'Log in'
            )}
          </button>
        </form>

        <p className="text-center mt-5" style={{ fontSize: 13, color: 'var(--text-muted)' }}>
          don't have an account?{' '}
          <Link to="/register" style={{ color: 'var(--accent)', textDecoration: 'none' }}>
            register
          </Link>
        </p>
      </div>
    </div>
  );
}

function Spinner() {
  return (
    <span
      style={{
        display: 'inline-block',
        width: 14,
        height: 14,
        border: '2px solid rgba(5,13,26,0.3)',
        borderTopColor: '#050D1A',
        borderRadius: '50%',
        animation: 'spin 0.7s linear infinite',
      }}
    />
  );
}

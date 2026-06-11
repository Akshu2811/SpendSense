import React, { useState, useEffect } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import toast from 'react-hot-toast';
import { register } from '../services/api';
import { useAuth } from '../context/AuthContext';

const USERNAME_RE = /^[a-zA-Z0-9_]{3,30}$/;

export default function Register() {
  const { login } = useAuth();
  const navigate = useNavigate();
  const [form, setForm] = useState({ username: '', password: '', confirm: '' });
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

  const validate = () => {
    if (!form.username || !form.password || !form.confirm) return 'Please fill in all fields';
    if (!USERNAME_RE.test(form.username))
      return 'Username must be 3–30 characters: letters, numbers, underscores only';
    if (form.password.length < 6) return 'Password must be at least 6 characters';
    if (form.password !== form.confirm) return "Passwords don't match";
    return null;
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    const validationError = validate();
    if (validationError) {
      setError(validationError);
      return;
    }
    setLoading(true);
    setError('');
    try {
      await register(form.username.trim(), form.password);
      await login(form.username.trim(), form.password);
      toast.success('Account created! Let\'s set your budget.');
      navigate('/onboarding/budget', { replace: true });
    } catch (err) {
      setError(err.response?.data?.detail ?? 'Registration failed. Try a different username.');
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
          <h1 style={{ fontSize: 24, fontWeight: 400, marginBottom: 6 }}>create account</h1>
          <p style={{ fontSize: 13, color: 'var(--text-muted)' }}>
            let's get your wallet sorted
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
              placeholder="3–30 chars, letters & numbers"
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
              autoComplete="new-password"
              placeholder="minimum 6 characters"
              value={form.password}
              onChange={handleChange}
              disabled={loading}
            />
          </div>

          <div>
            <label className="field-label">Confirm Password</label>
            <input
              name="confirm"
              type="password"
              autoComplete="new-password"
              placeholder="••••••••"
              value={form.confirm}
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
                creating account...
              </>
            ) : (
              'Create Account'
            )}
          </button>
        </form>

        <p className="text-center mt-5" style={{ fontSize: 13, color: 'var(--text-muted)' }}>
          already have an account?{' '}
          <Link to="/login" style={{ color: 'var(--accent)', textDecoration: 'none' }}>
            log in
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

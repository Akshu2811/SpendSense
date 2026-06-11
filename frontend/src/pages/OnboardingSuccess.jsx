import React, { useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';

export default function OnboardingSuccess() {
  const navigate = useNavigate();
  const { completeOnboarding } = useAuth();

  useEffect(() => {
    document.body.className = 'state-calm';
    return () => { document.body.className = ''; };
  }, []);

  const goToDashboard = () => {
    completeOnboarding();
    navigate('/dashboard', { replace: true });
  };

  return (
    <div
      className="min-h-screen flex flex-col px-5 pt-10 pb-8"
      style={{ maxWidth: 390, margin: '0 auto' }}
    >
      <ProgressDots active={3} />

      <div className="fade-in flex flex-col flex-1 items-center mt-10">
        {/* Big checkmark */}
        <span style={{ fontSize: 56, marginBottom: 20 }}>✅</span>

        <h1
          className="text-center"
          style={{ fontSize: 24, fontWeight: 400, marginBottom: 10 }}
        >
          SpendSense is ready! 🎉
        </h1>
        <p
          className="text-center"
          style={{ fontSize: 13, color: 'var(--text-muted)', lineHeight: 1.6, maxWidth: 290 }}
        >
          Your budget is set and SpendSense is watching. Every rupee, every app — covered.
        </p>

        {/* Tip card */}
        <div
          className="glass-card w-full mt-8 p-4"
          style={{ display: 'flex', alignItems: 'flex-start', gap: 12 }}
        >
          <span style={{ fontSize: 20, lineHeight: 1, flexShrink: 0, marginTop: 2 }}>💡</span>
          <div>
            <p style={{ fontSize: 13, fontWeight: 500, marginBottom: 4 }}>
              Add your recent purchases
            </p>
            <p style={{ fontSize: 12, color: 'var(--text-muted)', lineHeight: 1.55 }}>
              SpendSense builds purchase memory from your screenshots. Add a few recent orders
              so it can start spotting duplicates from day one.
            </p>
          </div>
        </div>

        <div style={{ flex: 1 }} />

        {/* CTAs */}
        <div className="w-full flex flex-col gap-3 mt-8">
          <button
            type="button"
            onClick={() => navigate('/add-purchase')}
            style={{
              width: '100%',
              height: 48,
              background: 'var(--accent)',
              color: '#050D1A',
              fontWeight: 600,
              fontSize: 15,
              borderRadius: 14,
              border: 'none',
            }}
          >
            Add a Purchase →
          </button>
          <button
            type="button"
            onClick={goToDashboard}
            className="btn-secondary"
            style={{ width: '100%', height: 44, fontSize: 14 }}
          >
            Go to Dashboard
          </button>
        </div>
      </div>
    </div>
  );
}

function ProgressDots({ active }) {
  return (
    <div className="flex gap-2 justify-center">
      {[1, 2, 3].map((i) => (
        <span
          key={i}
          style={{
            width: i <= active ? 20 : 8,
            height: 8,
            borderRadius: 4,
            background: i <= active ? 'var(--accent)' : 'var(--card-border)',
            transition: 'all 0.3s ease',
          }}
        />
      ))}
    </div>
  );
}

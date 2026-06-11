import React, { useEffect, useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { isAuthenticated } from '../services/api';

const ACCENT_COLOURS = ['#4FC3F7', '#FFB347', '#FF7043', '#CE93D8'];

const ORB_COLOURS = [
  { orb: '#00B4D8', glow: 'rgba(0, 180, 216, 0.35)'  },  // calm
  { orb: '#F77F00', glow: 'rgba(247, 127, 0, 0.35)'  },  // aware
  { orb: '#E63946', glow: 'rgba(230, 57, 70, 0.35)'  },  // urgent
  { orb: '#9B5DE5', glow: 'rgba(155, 93, 229, 0.35)' },  // crisis
];

const FEATURES = [
  {
    icon: '🧠',
    label: 'AI Purchase Memory',
    desc: 'Gemini Vision reads your order screenshots — knows exactly what you bought',
  },
  {
    icon: '⚡',
    label: 'Pre-purchase checks',
    desc: 'Fires before you tap buy — not after the damage is done',
  },
  {
    icon: '📊',
    label: 'Cross-app tracking',
    desc: 'Sees Myntra, Zepto, Amazon, Flipkart — every rupee, every app',
  },
];

export default function Landing() {
  const navigate = useNavigate();
  const [colorIndex, setColorIndex] = useState(0);

  useEffect(() => {
    document.body.className = 'state-calm';
    if (isAuthenticated()) navigate('/dashboard', { replace: true });
    const id = setInterval(
      () => setColorIndex(i => (i + 1) % ORB_COLOURS.length),
      2500,
    );
    return () => {
      document.body.className = '';
      clearInterval(id);
    };
  }, [navigate]);

  return (
    <div
      className="min-h-screen flex flex-col items-center justify-between px-5 pt-14 pb-8"
      style={{ maxWidth: 390, margin: '0 auto' }}
    >
      {/* Hero */}
      <div className="w-full flex flex-col items-center text-center fade-in">
        {/* Orb */}
        <div className="mb-8" style={{ position: 'relative', width: 120, height: 120 }}>
          {/* Outer glow */}
          <div
            style={{
              position: 'absolute',
              inset: -20,
              borderRadius: '50%',
              background: ORB_COLOURS[colorIndex].orb,
              filter: 'blur(30px)',
              opacity: 0.4,
              transition: 'background 1s ease',
            }}
          />
          {/* Main orb */}
          <div
            className="orb-idle"
            style={{
              position: 'relative',
              width: 120,
              height: 120,
              borderRadius: '50%',
              background: `radial-gradient(circle at 38% 32%, ${ORB_COLOURS[colorIndex].orb} 0%, rgba(0,0,0,0) 70%)`,
              boxShadow: `0 0 40px ${ORB_COLOURS[colorIndex].glow}`,
              transition: 'background 1s ease, box-shadow 1s ease',
            }}
          />
        </div>

        {/* Wordmark + beta */}
        <div className="flex items-center gap-2 mb-3">
          <h1 style={{ fontSize: 34, fontWeight: 300, letterSpacing: '-0.02em', lineHeight: 1 }}>
            SpendSense
          </h1>
          <span
            style={{
              fontSize: 9,
              fontWeight: 600,
              letterSpacing: '0.1em',
              textTransform: 'uppercase',
              background: 'var(--accent-muted)',
              border: '0.5px solid var(--accent)',
              color: 'var(--accent)',
              padding: '2px 7px',
              borderRadius: 6,
              alignSelf: 'flex-start',
              marginTop: 4,
            }}
          >
            beta
          </span>
        </div>

        {/* Tagline */}
        <p
          style={{
            fontSize: 14,
            color: 'var(--text-muted)',
            maxWidth: 280,
            lineHeight: 1.55,
            marginBottom: 32,
          }}
        >
          Your money's guardian —{' '}
          <span style={{ color: 'var(--accent)' }}>stops impulse buys before they happen.</span>
        </p>

        {/* Feature chips */}
        <div className="w-full flex flex-col gap-2 mb-10">
          {FEATURES.map((f) => (
            <div
              key={f.label}
              className="glass-card flex items-start gap-3 px-4 py-3 slide-up"
              style={{ textAlign: 'left' }}
            >
              <span style={{ fontSize: 20, lineHeight: 1, marginTop: 1 }}>{f.icon}</span>
              <div>
                <p style={{ fontSize: 13, fontWeight: 500, marginBottom: 2 }}>{f.label}</p>
                <p style={{ fontSize: 11, color: 'var(--text-muted)', lineHeight: 1.5 }}>{f.desc}</p>
              </div>
            </div>
          ))}
        </div>

        {/* CTAs */}
        <div className="w-full flex flex-col gap-3">
          <Link to="/register" style={{ width: '100%' }}>
            <button
              style={{
                width: '100%',
                height: 52,
                background: ACCENT_COLOURS[colorIndex],
                color: '#050D1A',
                fontWeight: 600,
                fontSize: 15,
                borderRadius: 14,
                border: 'none',
                transition: 'background 1s ease',
              }}
            >
              Get Started — it's free
            </button>
          </Link>
          <Link to="/login" style={{ width: '100%' }}>
            <button
              className="btn-secondary"
              style={{ width: '100%', height: 48, fontSize: 14 }}
            >
              I already have an account
            </button>
          </Link>
        </div>
      </div>

      {/* Footer note */}
      <p style={{ fontSize: 11, color: 'var(--text-faint)', marginTop: 32, textAlign: 'center' }}>
        Built for GenZ India 🇮🇳 · Free forever · No bank passwords
      </p>
    </div>
  );
}

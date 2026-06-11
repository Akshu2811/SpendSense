import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import toast from 'react-hot-toast';
import { setupBudget } from '../services/api';

const CATEGORIES = [
  { key: 'food',          emoji: '🍕', label: 'Food & Delivery',        color: 'var(--food)' },
  { key: 'fashion',       emoji: '👗', label: 'Shopping & Fashion',     color: 'var(--fashion)' },
  { key: 'electronics',  emoji: '📱', label: 'Electronics & Tech',      color: 'var(--electronics)' },
  { key: 'entertainment',emoji: '🎬', label: 'Entertainment & Subs',    color: 'var(--entertainment)' },
  { key: 'health',        emoji: '💚', label: 'Health & Lifestyle',      color: 'var(--health)' },
  { key: 'others',        emoji: '🏷️', label: 'Others',                 color: 'var(--others)' },
];

export default function OnboardingBudget() {
  const navigate = useNavigate();
  const [master, setMaster]         = useState('');
  const [catOpen, setCatOpen]       = useState(false);
  const [cats, setCats]             = useState({});
  const [loading, setLoading]       = useState(false);
  const [error, setError]           = useState('');

  useEffect(() => {
    document.body.className = 'state-calm';
    return () => { document.body.className = ''; };
  }, []);

  const handleCat = (key, val) =>
    setCats((prev) => ({ ...prev, [key]: val }));

  const handleSubmit = async (e) => {
    e.preventDefault();
    const amount = parseFloat(master);
    if (!amount || amount <= 0) {
      setError('Please enter a valid monthly budget');
      return;
    }
    setError('');
    setLoading(true);
    try {
      const categories = Object.fromEntries(
        Object.entries(cats)
          .filter(([, v]) => v !== '' && !isNaN(parseFloat(v)))
          .map(([k, v]) => [k, parseFloat(v)])
      );
      await setupBudget(amount, categories);
      navigate('/onboarding/connect');
    } catch (err) {
      toast.error(err.response?.data?.detail ?? 'Could not save budget. Try again.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div
      className="min-h-screen flex flex-col px-5 pt-10 pb-8"
      style={{ maxWidth: 390, margin: '0 auto' }}
    >
      {/* Progress dots */}
      <ProgressDots active={1} />

      <div className="fade-in flex flex-col flex-1 mt-8">
        <h1 style={{ fontSize: 22, fontWeight: 500, marginBottom: 8 }}>set your budget 💰</h1>
        <p style={{ fontSize: 13, color: 'var(--text-muted)', lineHeight: 1.55, marginBottom: 32 }}>
          SpendSense watches this limit every day — it's what tells your wallet when to
          breathe easy and when to panic.
        </p>

        <form onSubmit={handleSubmit} className="flex flex-col gap-6 flex-1">
          {/* Master budget input */}
          <div className="glass-card px-5 py-4">
            <label className="field-label">Monthly Budget</label>
            <div className="flex items-baseline gap-2 mt-1">
              <span style={{ fontSize: 28, fontWeight: 300, color: 'var(--accent)' }}>₹</span>
              <input
                type="number"
                min="1"
                placeholder="15000"
                value={master}
                onChange={(e) => { setError(''); setMaster(e.target.value); }}
                style={{
                  fontSize: 24,
                  fontWeight: 300,
                  background: 'transparent',
                  border: 'none',
                  borderBottom: '1px solid var(--card-border)',
                  borderRadius: 0,
                  padding: '4px 0',
                  width: '100%',
                }}
              />
            </div>
            {error && (
              <p style={{ fontSize: 11, color: '#E63946', marginTop: 8 }} role="alert">
                {error}
              </p>
            )}
          </div>

          {/* Category limits expandable */}
          <div className="glass-card overflow-hidden">
            <button
              type="button"
              onClick={() => setCatOpen((o) => !o)}
              style={{
                width: '100%',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'space-between',
                padding: '14px 20px',
                background: 'transparent',
                border: 'none',
                color: 'var(--text-primary)',
                height: 'auto',
                borderRadius: 0,
              }}
            >
              <span style={{ fontSize: 13, fontWeight: 500 }}>set category limits</span>
              <Chevron open={catOpen} />
            </button>

            {catOpen && (
              <div className="flex flex-col gap-1 px-4 pb-4 slide-up">
                <p style={{ fontSize: 11, color: 'var(--text-muted)', marginBottom: 12 }}>
                  Optional — skip any you don't want to track
                </p>
                {CATEGORIES.map((cat) => (
                  <div key={cat.key} className="flex items-center gap-3 py-2">
                    <span style={{ fontSize: 18, lineHeight: 1, flexShrink: 0 }}>{cat.emoji}</span>
                    <span
                      style={{
                        width: 8,
                        height: 8,
                        borderRadius: '50%',
                        background: cat.color,
                        flexShrink: 0,
                      }}
                    />
                    <span style={{ fontSize: 12, color: 'var(--text-muted)', flex: 1, minWidth: 0 }}>
                      {cat.label}
                    </span>
                    <div className="flex items-center gap-1" style={{ flexShrink: 0 }}>
                      <span style={{ fontSize: 12, color: 'var(--text-muted)' }}>₹</span>
                      <input
                        type="number"
                        min="0"
                        placeholder="optional"
                        value={cats[cat.key] ?? ''}
                        onChange={(e) => handleCat(cat.key, e.target.value)}
                        style={{
                          width: 90,
                          fontSize: 13,
                          padding: '6px 10px',
                          borderRadius: 8,
                        }}
                      />
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>

          <div style={{ flex: 1 }} />

          {/* Submit */}
          <button
            type="submit"
            disabled={loading}
            style={{
              width: '100%',
              height: 48,
              background: loading ? 'var(--accent-muted)' : 'var(--accent)',
              color: '#050D1A',
              fontWeight: 600,
              fontSize: 15,
              borderRadius: 14,
              border: 'none',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              gap: 8,
            }}
          >
            {loading ? <><Spinner /> Saving...</> : 'Set My Budget →'}
          </button>
        </form>
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

function Chevron({ open }) {
  return (
    <svg
      width="16"
      height="16"
      viewBox="0 0 16 16"
      fill="none"
      style={{ transform: open ? 'rotate(180deg)' : 'rotate(0deg)', transition: 'transform 0.25s ease' }}
    >
      <path d="M4 6l4 4 4-4" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" />
    </svg>
  );
}

function Spinner() {
  return (
    <span
      style={{
        display: 'inline-block', width: 14, height: 14,
        border: '2px solid rgba(5,13,26,0.3)', borderTopColor: '#050D1A',
        borderRadius: '50%', animation: 'spin 0.7s linear infinite',
      }}
    />
  );
}

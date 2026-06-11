import React, { useState, useEffect, useRef } from 'react';
import { useNavigate } from 'react-router-dom';
import toast from 'react-hot-toast';
import { uploadCsv } from '../services/api';

const GPAY_STEPS = [
  'Open Google Pay → tap your photo → Activity',
  'Tap the ··· menu → Download statement',
  'Choose your date range → Export as CSV',
  'Upload that CSV file using the button below',
];

export default function OnboardingConnect() {
  const navigate = useNavigate();
  const csvRef  = useRef(null);
  const gpayRef = useRef(null);

  const [gpayOpen,  setGpayOpen]  = useState(false);
  const [syncing,   setSyncing]   = useState(false);
  const [result,    setResult]    = useState(null); // { count, source }
  const [activeCard, setActiveCard] = useState(null); // 'csv' | 'gpay'

  useEffect(() => {
    document.body.className = 'state-calm';
    return () => { document.body.className = ''; };
  }, []);

  const handleFile = async (file, source) => {
    if (!file) return;
    setSyncing(true);
    setActiveCard(source);
    setResult(null);
    try {
      const data = await uploadCsv(file);
      setResult({ count: data?.count ?? data?.transactions_synced ?? '?', source });
      toast.success('Transactions imported!');
    } catch (err) {
      toast.error(err.response?.data?.detail ?? 'Sync failed. Check CSV format and try again.');
      setSyncing(false);
      setActiveCard(null);
    } finally {
      setSyncing(false);
    }
  };

  return (
    <div
      className="min-h-screen flex flex-col px-5 pt-10 pb-8"
      style={{ maxWidth: 390, margin: '0 auto' }}
    >
      <ProgressDots active={2} />

      <div className="fade-in flex flex-col flex-1 mt-8">
        <h1 style={{ fontSize: 22, fontWeight: 500, marginBottom: 8 }}>connect your data 📊</h1>
        <p style={{ fontSize: 13, color: 'var(--text-muted)', lineHeight: 1.55, marginBottom: 32 }}>
          SpendSense needs your transaction history to track your budget position in real time.
          Upload a UPI or bank CSV — no bank passwords, no Gmail access, ever.
        </p>

        <div className="flex flex-col gap-3">
          {/* CSV upload card */}
          <div className="glass-card p-5">
            {activeCard === 'csv' && syncing ? (
              <SyncingState />
            ) : result?.source === 'csv' ? (
              <SuccessState count={result.count} />
            ) : (
              <>
                <div className="flex items-center gap-3 mb-3">
                  <span style={{ fontSize: 24 }}>📁</span>
                  <div>
                    <p style={{ fontSize: 14, fontWeight: 500 }}>Upload CSV file</p>
                    <p style={{ fontSize: 11, color: 'var(--text-muted)' }}>
                      UPI statement, bank export, any CSV
                    </p>
                  </div>
                </div>
                <button
                  type="button"
                  onClick={() => csvRef.current?.click()}
                  className="btn-primary"
                  style={{ fontSize: 13, height: 40 }}
                >
                  Choose file
                </button>
                <input
                  ref={csvRef}
                  type="file"
                  accept=".csv"
                  style={{ display: 'none' }}
                  onChange={(e) => handleFile(e.target.files?.[0], 'csv')}
                />
              </>
            )}
          </div>

          {/* Google Pay card */}
          <div className="glass-card p-5">
            {activeCard === 'gpay' && syncing ? (
              <SyncingState />
            ) : result?.source === 'gpay' ? (
              <SuccessState count={result.count} />
            ) : (
              <>
                <button
                  type="button"
                  onClick={() => setGpayOpen((o) => !o)}
                  style={{
                    width: '100%', background: 'transparent', border: 'none',
                    display: 'flex', alignItems: 'center', gap: 12,
                    padding: 0, height: 'auto', borderRadius: 0, color: 'var(--text-primary)',
                  }}
                >
                  <span style={{ fontSize: 24 }}>📱</span>
                  <div style={{ flex: 1, textAlign: 'left' }}>
                    <p style={{ fontSize: 14, fontWeight: 500 }}>Google Pay Export</p>
                    <p style={{ fontSize: 11, color: 'var(--text-muted)' }}>
                      Export your GPay history as CSV
                    </p>
                  </div>
                  <Chevron open={gpayOpen} />
                </button>

                {gpayOpen && (
                  <div className="slide-up mt-4">
                    <ol className="flex flex-col gap-2 mb-4">
                      {GPAY_STEPS.map((step, i) => (
                        <li
                          key={i}
                          className="flex items-start gap-3"
                          style={{ fontSize: 12, color: 'var(--text-muted)', lineHeight: 1.5 }}
                        >
                          <span
                            style={{
                              flexShrink: 0, width: 18, height: 18,
                              borderRadius: '50%', background: 'var(--accent-muted)',
                              border: '0.5px solid var(--accent)', color: 'var(--accent)',
                              fontSize: 10, fontWeight: 600,
                              display: 'flex', alignItems: 'center', justifyContent: 'center',
                            }}
                          >
                            {i + 1}
                          </span>
                          {step}
                        </li>
                      ))}
                    </ol>
                    <button
                      type="button"
                      onClick={() => gpayRef.current?.click()}
                      className="btn-primary"
                      style={{ fontSize: 13, height: 40 }}
                    >
                      Upload GPay CSV
                    </button>
                    <input
                      ref={gpayRef}
                      type="file"
                      accept=".csv"
                      style={{ display: 'none' }}
                      onChange={(e) => handleFile(e.target.files?.[0], 'gpay')}
                    />
                  </div>
                )}
              </>
            )}
          </div>
        </div>

        <div style={{ flex: 1 }} />

        {/* Skip */}
        <button
          type="button"
          onClick={() => navigate('/onboarding/success')}
          style={{
            background: 'transparent', border: 'none', height: 'auto',
            color: 'var(--text-muted)', fontSize: 13, marginTop: 20,
            textDecoration: 'underline', textUnderlineOffset: 3,
          }}
        >
          Skip for now →
        </button>
      </div>
    </div>
  );
}

function SyncingState() {
  return (
    <div className="flex flex-col gap-3">
      <div className="shimmer-card" style={{ height: 16, borderRadius: 8, width: '60%' }} />
      <div className="shimmer-card" style={{ height: 12, borderRadius: 8, width: '80%' }} />
      <p style={{ fontSize: 12, color: 'var(--text-muted)', marginTop: 4 }}>
        Reading your transactions...
      </p>
    </div>
  );
}

function SuccessState({ count }) {
  return (
    <div className="flex items-center gap-3">
      <span style={{ fontSize: 28 }}>✓</span>
      <div>
        <p style={{ fontSize: 14, fontWeight: 500, color: 'var(--accent)' }}>
          {count} transactions imported
        </p>
        <p style={{ fontSize: 11, color: 'var(--text-muted)' }}>
          SpendSense is now tracking your budget
        </p>
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
      width="16" height="16" viewBox="0 0 16 16" fill="none"
      style={{ transform: open ? 'rotate(180deg)' : 'rotate(0deg)', transition: 'transform 0.25s ease', flexShrink: 0 }}
    >
      <path d="M4 6l4 4 4-4" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" />
    </svg>
  );
}

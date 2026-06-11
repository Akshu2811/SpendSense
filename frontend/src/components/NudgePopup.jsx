import React, { useState, useEffect } from 'react';

const TIER_EMOJI = {
  light:  '💸',
  medium: '👀',
  urgent: '😬',
  crisis: '😱',
};

const PLATFORM_CATEGORY_LABEL = {
  myntra:   'fashion budget',
  ajio:     'fashion budget',
  nykaa:    'fashion budget',
  zepto:    'quick commerce budget',
  blinkit:  'quick commerce budget',
  swiggy:   'quick commerce budget',
  amazon:   'overall budget',
  flipkart: 'overall budget',
};

// These platforms cover all categories — always show master_pct
const MASTER_PCT_PLATFORMS = new Set(['amazon', 'flipkart']);

export default function NudgePopup({ nudge, onPause, onSkip }) {
  const [flashing, setFlashing] = useState(false);

  console.log('NUDGE RECEIVED:', JSON.stringify(nudge?.context));

  const ctx         = nudge?.context ?? {};
  const masterPct   = ctx.master_pct ?? ctx.spend_pct ?? ctx.percent_spent ?? 0;
  const categoryPct = ctx.category_pct ?? 0;
  const masterAmt   = ctx.master_monthly ?? ctx.budget_amount ?? 0;
  const spentAmt    = ctx.spent_amount ?? Math.round((masterAmt * masterPct) / 100);
  const tierEmoji   = TIER_EMOJI[nudge?.tier] ?? '🤔';

  const platformKey    = (ctx.platform || '').toLowerCase();
  const alwaysMaster   = MASTER_PCT_PLATFORMS.has(platformKey);
  // Use category view whenever backend explicitly sent a category_pct (not null/absent)
  const isCategoryView = !alwaysMaster && ctx.category_pct != null;
  const displayPct     = isCategoryView ? categoryPct : masterPct;
  const barLabel       = alwaysMaster
    ? (PLATFORM_CATEGORY_LABEL[platformKey] ?? 'overall budget')
    : isCategoryView
      ? (PLATFORM_CATEGORY_LABEL[platformKey] ?? 'category budget')
      : spentAmt > 0
        ? `₹${Math.round(spentAmt).toLocaleString('en-IN')} spent this month`
        : 'spent this month';

  useEffect(() => {
    const onKey = (e) => { if (e.key === 'Escape') onSkip(); };
    window.addEventListener('keydown', onKey);
    return () => window.removeEventListener('keydown', onKey);
  }, [onSkip]);

  const handlePause = () => {
    setFlashing(true);
    setTimeout(() => onPause(), 500);
  };

  return (
    <>
      <style>{`
        @keyframes modal-enter {
          from { opacity: 0; transform: scale(0.85); }
          to   { opacity: 1; transform: scale(1); }
        }
        @keyframes backdrop-in {
          from { opacity: 0; }
          to   { opacity: 1; }
        }
      `}</style>

      {/* Backdrop */}
      <div
        onClick={onSkip}
        style={{
          position: 'fixed',
          inset: 0,
          background: 'rgba(0,0,0,0.7)',
          backdropFilter: 'blur(8px)',
          WebkitBackdropFilter: 'blur(8px)',
          zIndex: 50,
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          padding: 20,
          animation: 'backdrop-in 0.2s ease forwards',
        }}
      >
        {/* Card */}
        <div
          onClick={(e) => e.stopPropagation()}
          style={{
            position: 'relative',
            width: '100%',
            maxWidth: 340,
            background: 'color-mix(in srgb, var(--bg-secondary) 92%, transparent)',
            border: '1px solid rgba(255,255,255,0.12)',
            borderRadius: 24,
            padding: 24,
            backdropFilter: 'blur(20px)',
            WebkitBackdropFilter: 'blur(20px)',
            animation: 'modal-enter 0.25s ease-out forwards',
            boxShadow: '0 20px 60px rgba(0,0,0,0.5), 0 0 40px var(--orb-glow)',
            textAlign: 'center',
          }}
        >
          {/* Close X */}
          <button
            type="button"
            onClick={onSkip}
            style={{
              position: 'absolute',
              top: 16,
              right: 16,
              width: 20,
              height: 20,
              background: 'none',
              border: 'none',
              color: 'var(--text-faint)',
              fontSize: 14,
              lineHeight: 1,
              cursor: 'pointer',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              padding: 0,
            }}
          >
            ✕
          </button>

          {/* Tag chip */}
          <div style={{ display: 'flex', justifyContent: 'center', marginBottom: 12 }}>
            <span
              style={{
                display: 'inline-flex',
                alignItems: 'center',
                background: 'var(--accent-muted)',
                border: '1px solid color-mix(in srgb, var(--accent) 30%, transparent)',
                borderRadius: 20,
                padding: '4px 12px',
                fontSize: 12,
                color: 'var(--accent)',
                fontWeight: 500,
              }}
            >
              {nudge?.tag ?? '⚡ SpendSense Check'}
            </span>
          </div>

          {/* Tier emoji */}
          <p style={{ fontSize: 32, marginBottom: 8, lineHeight: 1 }}>
            {tierEmoji}
          </p>

          {/* Title */}
          <p
            style={{
              fontSize: 18,
              fontWeight: 600,
              color: '#FFFFFF',
              marginBottom: 8,
              lineHeight: 1.3,
            }}
          >
            {nudge?.title ?? 'Hold on a second...'}
          </p>

          {/* Body */}
          <p
            style={{
              fontSize: 13,
              color: 'var(--text-muted)',
              lineHeight: 1.6,
              marginBottom: 16,
              padding: '0 8px',
            }}
          >
            {nudge?.body ?? nudge?.message ?? 'SpendSense wants you to pause before this purchase.'}
          </p>

          {/* Divider */}
          <div
            style={{
              height: 1,
              background: 'rgba(255,255,255,0.08)',
              marginBottom: 16,
            }}
          />

          {/* Context row */}
          <div style={{ marginBottom: 16 }}>
            <div
              style={{
                display: 'flex',
                justifyContent: 'space-between',
                alignItems: 'center',
                marginBottom: 6,
              }}
            >
              <span style={{ fontSize: 11, color: 'var(--text-faint)' }}>
                {barLabel}
              </span>
              <span style={{ fontSize: 11, color: 'var(--accent)', fontWeight: 500 }}>
                {Math.round(displayPct)}% of budget
              </span>
            </div>
            {/* Mini progress bar */}
            <div
              style={{
                height: 3,
                borderRadius: 2,
                background: 'rgba(255,255,255,0.1)',
                overflow: 'hidden',
              }}
            >
              <div
                style={{
                  height: '100%',
                  width: `${Math.min(displayPct, 100)}%`,
                  background: 'var(--accent)',
                  borderRadius: 2,
                  transition: 'width 0.6s ease',
                }}
              />
            </div>
          </div>

          {/* Action buttons */}
          <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
            {/* i'll wait — primary, on top */}
            <button
              type="button"
              onClick={handlePause}
              style={{
                width: '100%',
                height: 48,
                borderRadius: 14,
                background: flashing ? '#4ECCA3' : 'var(--accent)',
                color: '#050D1A',
                fontSize: 14,
                fontWeight: 600,
                border: 'none',
                cursor: 'pointer',
                transition: 'background 0.2s ease',
              }}
            >
              i'll wait ✓
            </button>

            {/* skip anyway — below */}
            <button
              type="button"
              onClick={onSkip}
              style={{
                width: '100%',
                height: 44,
                borderRadius: 14,
                background: 'rgba(255,255,255,0.06)',
                border: '1px solid rgba(255,255,255,0.12)',
                color: 'var(--text-muted)',
                fontSize: 13,
                fontWeight: 400,
                cursor: 'pointer',
              }}
            >
              skip anyway
            </button>
          </div>
        </div>
      </div>
    </>
  );
}

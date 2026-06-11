import React, { useEffect, useState, useRef } from 'react';
import toast from 'react-hot-toast';
import {
  getWalletState,
  getCurrentBudget,
  fireNudge,
  respondToNudge,
  checkBeforeBuy,
} from '../services/api';
import BottomNav from '../components/BottomNav';
import NudgePopup from '../components/NudgePopup';

const APPS = [
  { name: 'Myntra',   emoji: '👗', color: '#FF6B4A' },
  { name: 'Amazon',   emoji: '📦', color: '#FFB347' },
  { name: 'Flipkart', emoji: '🏷️', color: '#89B4FF' },
  { name: 'Zepto',    emoji: '⚡', color: '#4ECCA3' },
  { name: 'Blinkit',  emoji: '🟡', color: '#FFE566' },
  { name: 'Swiggy',   emoji: '🍊', color: '#FF8C42' },
];

// Maps each app to its budget category wallet field; general apps (Amazon, Flipkart) are absent
const APP_CATEGORY_FIELD = {
  Myntra:  'shopping_fashion',
  Ajio:    'shopping_fashion',
  Nykaa:   'shopping_fashion',
  Zepto:   'food_dining_delivery',
  Blinkit: 'food_dining_delivery',
  Swiggy:  'food_dining_delivery',
};

export default function ShopCheck() {
  const fileRef   = useRef(null);
  const walletRef = useRef(null);

  const [loadingApp,   setLoadingApp]   = useState(null);
  const [activeNudge,  setActiveNudge]  = useState(null);
  const [checkLoading, setCheckLoading] = useState(false);
  const [checkResult,  setCheckResult]  = useState(null);

  useEffect(() => {
    document.body.className = 'state-calm';
    (async () => {
      try {
        const ws = await getWalletState();
        if (ws?.state) document.body.className = `state-${ws.state}`;
        walletRef.current = ws;
      } catch {}
    })();
    return () => { document.body.className = ''; };
  }, []);

  // ── App tap ──────────────────────────────────────────────────────────────
  const handleAppTap = async (appName) => {
    if (loadingApp) return;
    setLoadingApp(appName);
    try {
      const catField = APP_CATEGORY_FIELD[appName];
      const context = {};
      if (catField) {
        const catPct = walletRef.current?.category_pcts?.[catField];
        context.category_pct = catPct ?? null;
        context.category = catField;
      } else {
        // General apps (Amazon, Flipkart) — no category context
        context.category_pct = null;
        context.category = null;
      }
      console.log('APP:', appName, 'CONTEXT:', JSON.stringify(context));
      const nudge = await fireNudge('pre_shop_check', appName, context);
      setActiveNudge(nudge);
    } catch (err) {
      toast.error('Could not load check. Try again.');
    } finally {
      setLoadingApp(null);
    }
  };

  // ── Item screenshot check ────────────────────────────────────────────────
  const handleFileSelected = async (file) => {
    if (!file) return;
    setCheckLoading(true);
    setCheckResult(null);
    try {
      const result = await checkBeforeBuy(file);
      if (result?.nudge_needed) {
        const nudge = await fireNudge('pre_shop_check', null, result);
        setActiveNudge(nudge);
      } else {
        setCheckResult(result);
      }
    } catch (err) {
      toast.error(err.response?.data?.detail ?? "Couldn't read this image. Try a clearer screenshot.");
    } finally {
      setCheckLoading(false);
    }
  };

  // ── Nudge responses ──────────────────────────────────────────────────────
  const handlePause = async () => {
    try {
      await respondToNudge(activeNudge?.nudge_id ?? activeNudge?._id, 'paused');
    } catch {}
    let streakLabel = '';
    try {
      const budget = await getCurrentBudget();
      const n = budget?.current_streak ?? budget?.streak;
      if (n != null) streakLabel = ` Streak: ${n} days`;
    } catch {}
    toast.success(`Nice one!${streakLabel} 🔥`);
    setTimeout(() => setActiveNudge(null), 500);
  };

  const handleSkip = async () => {
    try {
      await respondToNudge(activeNudge?.nudge_id ?? activeNudge?._id, 'overridden');
    } catch {}
    setActiveNudge(null);
  };

  // ── Render ───────────────────────────────────────────────────────────────
  return (
    <div
      style={{
        minHeight: '100vh',
        display: 'flex',
        flexDirection: 'column',
        maxWidth: 390,
        margin: '0 auto',
        paddingBottom: 80,
      }}
    >
      {/* Header */}
      <div style={{ padding: '20px 20px 0' }}>
        <h1 style={{ fontSize: 20, fontWeight: 500, marginBottom: 4 }}>shop check 🛍️</h1>
        <p style={{ fontSize: 13, color: 'var(--text-muted)' }}>
          tap an app before you open it
        </p>
      </div>

      {/* App grid — 3×2 */}
      <div
        style={{
          display: 'grid',
          gridTemplateColumns: 'repeat(3, 1fr)',
          gap: 12,
          padding: '20px 16px 0',
        }}
      >
        {APPS.map((app) => {
          const isLoading = loadingApp === app.name;
          return (
            <button
              key={app.name}
              type="button"
              onClick={() => handleAppTap(app.name)}
              disabled={!!loadingApp}
              style={{
                display: 'flex',
                flexDirection: 'column',
                alignItems: 'center',
                gap: 8,
                padding: 16,
                background: 'var(--card-bg)',
                border: `0.5px solid var(--card-border)`,
                borderRadius: 16,
                backdropFilter: 'blur(12px)',
                WebkitBackdropFilter: 'blur(12px)',
                cursor: loadingApp ? 'not-allowed' : 'pointer',
                position: 'relative',
                overflow: 'hidden',
                height: 'auto',
                transition: 'transform 0.1s ease, opacity 0.15s ease',
                opacity: loadingApp && !isLoading ? 0.5 : 1,
              }}
              onMouseDown={(e) => e.currentTarget.style.transform = 'scale(0.95)'}
              onMouseUp={(e)   => e.currentTarget.style.transform = 'scale(1)'}
              onMouseLeave={(e) => e.currentTarget.style.transform = 'scale(1)'}
            >
              <span style={{ fontSize: 28, lineHeight: 1 }}>{app.emoji}</span>
              <span style={{ fontSize: 13, color: '#FFFFFF', fontWeight: 400 }}>{app.name}</span>

              {/* Spinner overlay */}
              {isLoading && (
                <div
                  style={{
                    position: 'absolute',
                    inset: 0,
                    background: 'rgba(0,0,0,0.55)',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    borderRadius: 16,
                  }}
                >
                  <AppSpinner color={app.color} />
                </div>
              )}
            </button>
          );
        })}
      </div>

      {/* Divider */}
      <p
        style={{
          fontSize: 11,
          color: 'var(--text-faint)',
          textAlign: 'center',
          margin: '16px 0',
          letterSpacing: '0.05em',
        }}
      >
        — or —
      </p>

      {/* Check specific item card */}
      <div style={{ padding: '0 16px' }}>
        <div
          className="glass-card"
          style={{
            padding: 16,
            cursor: checkLoading ? 'default' : 'pointer',
            minHeight: 72,
            display: 'flex',
            alignItems: 'center',
          }}
          onClick={() => !checkLoading && fileRef.current?.click()}
        >
          {checkLoading ? (
            <div
              style={{
                flex: 1,
                display: 'flex',
                flexDirection: 'column',
                alignItems: 'center',
                justifyContent: 'center',
                gap: 8,
              }}
            >
              <AppSpinner color="#FFB347" />
              <span style={{ fontSize: 13, color: 'var(--text-muted)' }}>
                Checking your history...
              </span>
            </div>
          ) : (
            <div style={{ display: 'flex', alignItems: 'center', gap: 12, width: '100%' }}>
              <span style={{ fontSize: 28, lineHeight: 1, flexShrink: 0 }}>📸</span>
              <div>
                <p style={{ fontSize: 15, fontWeight: 500 }}>Check a specific item</p>
                <p style={{ fontSize: 12, color: 'var(--text-muted)', marginTop: 2 }}>
                  Upload a product screenshot
                </p>
              </div>
              <span style={{ marginLeft: 'auto', color: 'var(--text-muted)', fontSize: 18 }}>›</span>
            </div>
          )}
        </div>

        <input
          ref={fileRef}
          type="file"
          accept="image/*"
          style={{ display: 'none' }}
          onChange={(e) => handleFileSelected(e.target.files?.[0])}
        />
      </div>

      {/* Success card */}
      {checkResult && !activeNudge && (() => {
        const walletRemaining = walletRef.current?.budget_amount != null
          ? Math.round(walletRef.current.budget_amount - (walletRef.current.spent_amount ?? 0))
          : null;
        const budgetRemaining = checkResult.budget_remaining ?? walletRemaining;
        return (
          <div
            className="glass-card slide-up"
            style={{ margin: '12px 16px 0', padding: 16, textAlign: 'center' }}
          >
            <p style={{ fontSize: 24, marginBottom: 8 }}>✅</p>
            <p style={{ fontSize: 16, color: '#FFFFFF', marginBottom: 4 }}>Looks good!</p>
            <p style={{ fontSize: 13, color: 'var(--text-muted)', marginBottom: budgetRemaining != null ? 4 : 0 }}>
              Nothing similar in your history.
            </p>
            {budgetRemaining != null && (
              <p style={{ fontSize: 13, color: 'var(--accent)' }}>
                Budget remaining: ₹{budgetRemaining.toLocaleString('en-IN')}
              </p>
            )}
          </div>
        );
      })()}

      {/* Nudge popup */}
      {activeNudge && (
        <NudgePopup
          nudge={activeNudge}
          onPause={handlePause}
          onSkip={handleSkip}
        />
      )}

      <BottomNav active="shopcheck" />
    </div>
  );
}

function AppSpinner({ color }) {
  return (
    <span
      style={{
        display: 'inline-block',
        width: 20,
        height: 20,
        border: `2.5px solid rgba(255,255,255,0.15)`,
        borderTopColor: color ?? 'var(--accent)',
        borderRadius: '50%',
        animation: 'spin 0.75s linear infinite',
        flexShrink: 0,
      }}
    />
  );
}

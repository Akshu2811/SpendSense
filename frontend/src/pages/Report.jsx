import React, { useEffect, useState, useRef } from 'react';
import { format } from 'date-fns';
import toast from 'react-hot-toast';
import { getWalletState, getCurrentReport } from '../services/api';
import BottomNav from '../components/BottomNav';

const CAT_MAP = {
  food_dining_delivery: { emoji: '🍕', label: 'Food & Delivery' },
  shopping_fashion:     { emoji: '👗', label: 'Fashion' },
  electronics_tech:     { emoji: '📱', label: 'Electronics' },
  entertainment_subs:   { emoji: '🎬', label: 'Entertainment' },
  health_lifestyle:     { emoji: '💊', label: 'Health' },
  others:               { emoji: '💸', label: 'Others' },
};

// ── Count-up hook ─────────────────────────────────────────────────────────────
function useCountUp(target, duration = 1200) {
  const [val, setVal] = useState(0);
  const rafRef = useRef(null);
  useEffect(() => {
    if (!target && target !== 0) return;
    const startTime = performance.now();
    const animate = (now) => {
      const elapsed = now - startTime;
      const progress = Math.min(elapsed / duration, 1);
      // ease-out quad
      const eased = 1 - (1 - progress) ** 2;
      setVal(Math.round(eased * target));
      if (progress < 1) rafRef.current = requestAnimationFrame(animate);
    };
    rafRef.current = requestAnimationFrame(animate);
    return () => cancelAnimationFrame(rafRef.current);
  }, [target, duration]);
  return val;
}

// ── Stat card with count-up ───────────────────────────────────────────────────
function StatCard({ emoji, value, label }) {
  const counted = useCountUp(Number(value) || 0);
  return (
    <div className="glass-card" style={{ flex: 1, padding: 12, textAlign: 'center' }}>
      <p style={{ fontSize: 20, marginBottom: 6 }}>{emoji}</p>
      <p style={{ fontSize: 24, fontWeight: 300, color: '#FFFFFF', lineHeight: 1 }}>{counted}</p>
      <p style={{ fontSize: 10, color: 'var(--text-muted)', marginTop: 4 }}>{label}</p>
    </div>
  );
}

export default function Report() {
  const [loading,  setLoading]  = useState(true);
  const [report,   setReport]   = useState(null);
  const [error,    setError]    = useState(false);

  const monthLabel = format(new Date(), "MMMM yyyy").toLowerCase();

  useEffect(() => {
    document.body.className = 'state-calm';
    (async () => {
      try {
        const ws = await getWalletState();
        if (ws?.state) document.body.className = `state-${ws.state}`;
        const data = await getCurrentReport();
        setReport(data);
      } catch {
        setError(true);
      } finally {
        setLoading(false);
      }
    })();
    return () => { document.body.className = ''; };
  }, []);

  // Derived values with safe defaults
  const nudges    = report?.nudge_summary    ?? {};
  const streaks   = report?.streak_summary   ?? {};
  const budget    = report?.budget_summary   ?? {};
  const insights  = report?.insights         ?? {};

  const totalFired   = nudges.total_fired        ?? 0;
  const totalPaused  = nudges.total_paused       ?? 0;
  const estimated    = nudges.estimated_saved    ?? 0;
  const bestStreak   = streaks.best_streak_days  ?? 0;
  const utilisePct   = budget.utilisation_pct    ?? 0;
  const masterBudget = budget.master_budget       ?? 0;
  const totalSpent   = budget.total_spent         ?? 0;
  const topCat       = insights.top_impulse_category ?? '';
  const topCatCount  = insights.category_count   ?? 0;
  const catMeta      = CAT_MAP[topCat] ?? { emoji: '💸', label: topCat };

  const estimatedCounted = useCountUp(estimated, 1400);

  const handleShare = async () => {
    const text = `${monthLabel}: ${totalFired} nudges, ${totalPaused} paused, ₹${estimated.toLocaleString('en-IN')} saved! 💰 #SpendSense`;
    if (navigator.share) {
      try { await navigator.share({ title: 'My SpendSense Report', text }); } catch {}
    } else {
      try {
        await navigator.clipboard.writeText(text);
        toast.success('Copied to clipboard!');
      } catch {
        toast.error('Could not copy. Try sharing manually.');
      }
    }
  };

  return (
    <div style={{ minHeight: '100vh', maxWidth: 390, margin: '0 auto', paddingBottom: 80, padding: '0 16px 80px' }}>
      {/* Loading */}
      {loading && (
        <div style={{ padding: '20px 0', display: 'flex', flexDirection: 'column', gap: 12 }}>
          {[1,2,3,4].map((i) => (
            <div key={i} className="shimmer-card" style={{ height: i === 1 ? 30 : 80, borderRadius: 16 }} />
          ))}
        </div>
      )}

      {/* Empty / error */}
      {!loading && (error || !report) && (
        <div style={{ paddingTop: 60, textAlign: 'center' }}>
          <p style={{ fontSize: 16 }}>your report is building... 💪</p>
          <p style={{ fontSize: 13, color: 'var(--text-muted)', marginTop: 8 }}>Keep using SpendSense!</p>
        </div>
      )}

      {/* Content */}
      {!loading && report && (
        <div className="fade-in">
          {/* Header */}
          <h1 style={{ fontSize: 18, fontWeight: 300, paddingTop: 20, marginBottom: 16, lineHeight: 1.4 }}>
            {monthLabel} / your month, honestly.
          </h1>

          {/* Stat cards */}
          <div style={{ display: 'flex', gap: 10, marginBottom: 12 }}>
            <StatCard emoji="🛑" value={totalFired}  label="nudges fired" />
            <StatCard emoji="✅" value={totalPaused} label="times paused" />
            <StatCard emoji="🔥" value={bestStreak}  label="day streak"   />
          </div>

          {/* Savings card */}
          <div className="glass-card" style={{ padding: 20, marginBottom: 12, textAlign: 'center' }}>
            <p style={{ fontSize: 10, color: 'var(--text-muted)', letterSpacing: '0.1em', textTransform: 'uppercase', marginBottom: 8 }}>
              estimated saved
            </p>
            <p style={{ fontSize: 40, fontWeight: 300, color: 'var(--accent)', lineHeight: 1 }}>
              ₹{estimatedCounted.toLocaleString('en-IN')}
            </p>
            <p style={{ fontSize: 12, color: 'var(--text-muted)', marginTop: 6 }}>✨ this month</p>
          </div>

          {/* Budget bar */}
          <div className="glass-card" style={{ padding: 16, marginBottom: 12 }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 8 }}>
              <span style={{ fontSize: 12, color: 'var(--text-muted)' }}>budget used</span>
              <span style={{ fontSize: 12, color: 'var(--accent)', fontWeight: 500 }}>{Math.round(utilisePct)}%</span>
            </div>
            <div style={{ height: 8, borderRadius: 4, background: 'rgba(255,255,255,0.1)', overflow: 'hidden' }}>
              <div style={{
                height: '100%', borderRadius: 4, background: 'var(--accent)',
                width: `${Math.min(utilisePct, 100)}%`, transition: 'width 0.8s ease',
              }} />
            </div>
            <p style={{ fontSize: 11, color: 'var(--text-faint)', marginTop: 8 }}>
              ₹{Math.round(totalSpent).toLocaleString('en-IN')} of ₹{Math.round(masterBudget).toLocaleString('en-IN')}
            </p>
          </div>

          {/* Insight card */}
          {topCat && (
            <div className="glass-card" style={{ padding: 16, marginBottom: 16 }}>
              <p style={{ fontSize: 10, color: 'var(--text-muted)', letterSpacing: '0.1em', textTransform: 'uppercase', marginBottom: 6 }}>
                top impulse zone
              </p>
              <p style={{ fontSize: 16, color: '#FFFFFF', marginBottom: 4 }}>
                {catMeta.emoji} {catMeta.label}
              </p>
              <p style={{ fontSize: 12, color: 'var(--text-muted)' }}>
                ({topCatCount} of {totalFired} nudges)
              </p>
            </div>
          )}

          {/* Share */}
          <button
            type="button"
            onClick={handleShare}
            style={{
              width: '100%', height: 48,
              background: 'var(--accent)', color: '#050D1A',
              fontWeight: 600, fontSize: 15, borderRadius: 14, border: 'none',
              marginBottom: 20,
            }}
          >
            Share Report 📤
          </button>
        </div>
      )}

      <BottomNav active="report" />
    </div>
  );
}

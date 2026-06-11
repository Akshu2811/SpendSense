import React, { useEffect, useState, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import { format } from 'date-fns';
import { getWalletState, getCurrentBudget, getRecentTransactions } from '../services/api';
import { useAuth } from '../context/AuthContext';
import BottomNav from '../components/BottomNav';

// ── Constants ────────────────────────────────────────────────────────────────

const MOOD = {
  calm:   'breathing easy ✦',
  aware:  'heads up, bestie 👀',
  urgent: 'feeling the heat 🌶️',
  crisis: 'wallet in crisis 💀',
};

const CAT_CONFIG = {
  food_dining_delivery:  { emoji: '🍕', short: 'Food',    colour: '#FF6B4A', rgb: '255,107,74'  },
  shopping_fashion:      { emoji: '👗', short: 'Fashion', colour: '#A89CF0', rgb: '168,156,240' },
  electronics_tech:      { emoji: '📱', short: 'Tech',    colour: '#89B4FF', rgb: '137,180,255' },
  entertainment_subs:    { emoji: '🎬', short: 'Fun',     colour: '#F15BB5', rgb: '241,91,181'  },
  health_lifestyle:      { emoji: '💊', short: 'Health',  colour: '#4ECCA3', rgb: '78,204,163'  },
  others:                { emoji: '💸', short: 'Others',  colour: '#888780', rgb: '136,135,128' },
};

const PILL_STYLES = {
  food_dining_delivery: { bg: 'rgba(255,107,74,0.25)',  border: 'rgba(255,107,74,0.5)',  color: '#FF6B4A' },
  shopping_fashion:     { bg: 'rgba(168,156,240,0.25)', border: 'rgba(168,156,240,0.5)', color: '#A89CF0' },
  electronics_tech:     { bg: 'rgba(137,180,255,0.25)', border: 'rgba(137,180,255,0.5)', color: '#89B4FF' },
  entertainment_subs:   { bg: 'rgba(241,91,181,0.25)',  border: 'rgba(241,91,181,0.5)',  color: '#F15BB5' },
  health_lifestyle:     { bg: 'rgba(78,204,163,0.25)',  border: 'rgba(78,204,163,0.5)',  color: '#4ECCA3' },
  others:               { bg: 'rgba(136,135,128,0.25)', border: 'rgba(136,135,128,0.5)', color: '#888780' },
};

const TX_CAT_EMOJI = {
  food_dining_delivery: '🍕',
  shopping_fashion: '👗',
  electronics_tech: '📱',
  entertainment_subs: '🎬',
  health_lifestyle: '💊',
  others: '💸',
};

const formatINR = (n) =>
  `₹${Math.round(n || 0).toLocaleString('en-IN')}`;

// ── Component ────────────────────────────────────────────────────────────────

export default function Dashboard() {
  const navigate = useNavigate();
  const { user } = useAuth();

  const [loading,      setLoading]      = useState(true);
  const [walletState,  setWalletState]  = useState('calm');
  const [pctSpent,     setPctSpent]     = useState(0);
  const [spentAmt,     setSpentAmt]     = useState(0);
  const [leftAmt,      setLeftAmt]      = useState(0);
  const [categories,   setCategories]   = useState([]);
  const [transactions, setTransactions] = useState([]);
  const [streak,       setStreak]       = useState(0);
  const [bestStreak,   setBestStreak]   = useState(0);

  const loadData = useCallback(async () => {
    try {
      // 1. Wallet state → apply body class immediately
      const ws = await getWalletState();
      const state = ws?.state ?? 'calm';
      setWalletState(state);
      document.body.className = `state-${state}`;

      // WalletStateResponse fields: state, spend_pct, spent_amount, budget_amount, category_pcts
      const pct    = ws?.spend_pct ?? 0;
      const master = ws?.budget_amount ?? 0;
      const spent  = ws?.spent_amount  ?? (master * pct / 100);
      setPctSpent(Math.round(pct));
      setSpentAmt(spent);
      setLeftAmt(master - spent);

      // Build category pills from category_pcts (keyed by category slug → number)
      const catData = ws?.category_pcts ?? {};
      const pills = Object.entries(CAT_CONFIG).map(([key, cfg]) => ({
        key,
        ...cfg,
        pct: Math.round(typeof catData[key] === 'object' ? (catData[key]?.percent_spent ?? 0) : (catData[key] ?? 0)),
      }));
      setCategories(pills);

      // 2. Budget → streak info (budget_current returns current_streak + best_streak)
      const budget = await getCurrentBudget();
      setStreak(budget?.current_streak ?? 0);
      setBestStreak(budget?.best_streak ?? 0);

      // Overwrite spent/left with budget master if wallet state lacked it
      if (budget?.master_monthly && master === 0) {
        const s = budget.current_spend ?? spent;
        setSpentAmt(s);
        setLeftAmt(budget.master_monthly - s);
      }

      // 3. Transactions
      const txData = await getRecentTransactions();
      setTransactions(Array.isArray(txData) ? txData.slice(0, 5) : []);
    } catch (err) {
      // Graceful degradation — show whatever we have
      console.error('Dashboard load error:', err);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    document.body.className = 'state-calm'; // immediate dark bg before first fetch
    loadData();
    return () => { document.body.className = ''; };
  }, [loadData]);

  if (loading) return <LoadingSkeleton />;

  const monthLabel = format(new Date(), 'MMMM yyyy');
  const username   = user?.username ?? 'there';

  return (
    <div
      style={{
        height: '100vh',
        overflow: 'hidden',
        display: 'flex',
        flexDirection: 'column',
        maxWidth: 390,
        margin: '0 auto',
        position: 'relative',
      }}
    >
      {/* ── Top bar ── */}
      <div
        style={{
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          padding: '12px 20px 8px',
          flexShrink: 0,
        }}
      >
        <span style={{ fontSize: 15, fontWeight: 500 }}>hi {username}! 👋</span>
        <span style={{ fontSize: 14, color: 'var(--text-muted)' }}>{monthLabel}</span>
      </div>

      {/* ── Living Wallet Aura ── */}
      <div
        style={{
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
          paddingTop: 8,
          paddingBottom: 12,
          flexShrink: 0,
        }}
      >
        {/* "your wallet is" label */}
        <p
          style={{
            fontSize: 10,
            color: 'var(--text-faint)',
            letterSpacing: '0.12em',
            textTransform: 'uppercase',
            marginBottom: 16,
          }}
        >
          your wallet is
        </p>

        {/* Orb container */}
        <div style={{ position: 'relative', width: 200, height: 200, display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
          {/* Outer glow */}
          <div
            style={{
              position: 'absolute',
              width: 240,
              height: 240,
              borderRadius: '50%',
              background: 'var(--orb-glow)',
              filter: 'blur(30px)',
              transition: 'background 1.5s ease',
              pointerEvents: 'none',
            }}
          />

          {/* Main orb */}
          <div
            className="orb-idle"
            style={{
              width: 160,
              height: 160,
              borderRadius: '50%',
              background: `radial-gradient(circle at 38% 32%, var(--orb) 0%, rgba(0,0,0,0.6) 80%)`,
              boxShadow: '0 0 50px var(--orb-glow)',
              transition: 'all 1.5s ease',
              display: 'flex',
              flexDirection: 'column',
              alignItems: 'center',
              justifyContent: 'center',
              position: 'relative',
              zIndex: 1,
            }}
          >
            <span style={{ fontSize: 36, fontWeight: 300, lineHeight: 1 }}>
              {pctSpent}%
            </span>
            <span style={{ fontSize: 10, color: 'var(--text-muted)', marginTop: 4 }}>
              spent
            </span>
          </div>
        </div>

        {/* Mood text */}
        <p
          style={{
            fontSize: 12,
            color: 'var(--accent)',
            fontWeight: 500,
            marginTop: 12,
            transition: 'color 1.5s ease',
          }}
        >
          {MOOD[walletState] ?? MOOD.calm}
        </p>
      </div>

      {/* ── Spent / Left row ── */}
      <div
        className="glass-card"
        style={{
          margin: '0 16px',
          display: 'flex',
          flexShrink: 0,
        }}
      >
        {/* Left: spent */}
        <div
          style={{
            flex: 1,
            display: 'flex',
            flexDirection: 'column',
            alignItems: 'center',
            padding: '12px 16px',
          }}
        >
          <span style={{ fontSize: 18, fontWeight: 300 }}>{formatINR(spentAmt)}</span>
          <span style={{ fontSize: 10, color: 'var(--text-muted)', marginTop: 2 }}>spent</span>
        </div>

        {/* Divider */}
        <div style={{ width: 1, background: 'var(--card-border)', alignSelf: 'stretch', margin: '10px 0' }} />

        {/* Right: left */}
        <div
          style={{
            flex: 1,
            display: 'flex',
            flexDirection: 'column',
            alignItems: 'center',
            padding: '12px 16px',
          }}
        >
          <span style={{ fontSize: 18, fontWeight: 300, color: 'var(--accent)' }}>
            {formatINR(leftAmt)}
          </span>
          <span style={{ fontSize: 10, color: 'var(--text-muted)', marginTop: 2 }}>left</span>
        </div>
      </div>

      {/* ── Category pills ── */}
      <div
        style={{
          display: 'flex',
          gap: 8,
          overflowX: 'auto',
          padding: '10px 16px',
          flexShrink: 0,
          scrollbarWidth: 'none',
          msOverflowStyle: 'none',
        }}
      >
        {categories.map((cat) => {
          const ps = PILL_STYLES[cat.key] ?? { bg: 'rgba(255,255,255,0.07)', border: 'rgba(255,255,255,0.15)', color: 'var(--text-muted)' };
          console.log('PIL:', cat.key, 'rgb:', cat.rgb, 'bg:', `rgba(${cat.rgb}, 0.15)`);
          return (
            <div
              key={cat.key}
              style={{
                flexShrink: 0,
                display: 'flex',
                alignItems: 'center',
                gap: 5,
                background: ps.bg,
                border: `1px solid ${ps.border}`,
                borderRadius: 20,
                padding: '6px 12px',
                fontSize: 12,
                whiteSpace: 'nowrap',
              }}
            >
              <span style={{ fontSize: 14 }}>{cat.emoji}</span>
              <span>{cat.short}</span>
              <span style={{ color: cat.pct > 90 ? '#E63946' : ps.color, fontWeight: cat.pct > 90 ? 600 : 400 }}>
                {cat.pct}%
              </span>
              {cat.pct > 90 && <span>⚠️</span>}
            </div>
          );
        })}
      </div>

      {/* ── Transaction feed ── */}
      <div
        className="glass-card"
        style={{
          margin: '0 16px',
          flex: 1,
          overflow: 'hidden',
          display: 'flex',
          flexDirection: 'column',
          minHeight: 0,
        }}
      >
        <p
          style={{
            fontSize: 10,
            color: 'var(--text-muted)',
            letterSpacing: '0.1em',
            textTransform: 'uppercase',
            padding: '12px 16px 8px',
            flexShrink: 0,
          }}
        >
          recent activity
        </p>

        {transactions.length === 0 ? (
          <div
            style={{
              flex: 1,
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              padding: '0 16px',
            }}
          >
            <p style={{ fontSize: 12, color: 'var(--text-muted)', textAlign: 'center' }}>
              No transactions yet. Upload your bank CSV.
            </p>
          </div>
        ) : (
          <div style={{ overflow: 'hidden', flex: 1 }}>
            {transactions.map((tx, i) => (
              <React.Fragment key={tx.id ?? i}>
                <TxRow tx={tx} />
                {i < transactions.length - 1 && (
                  <div style={{ height: 1, background: 'var(--card-border)', margin: '0 16px' }} />
                )}
              </React.Fragment>
            ))}
          </div>
        )}
      </div>

      {/* ── Streak bar ── */}
      <div
        className="glass-card"
        style={{
          margin: '8px 16px',
          padding: '10px 16px',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          flexShrink: 0,
          marginBottom: 76, // space for bottom nav + floating btn
        }}
      >
        <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
          <span style={{ fontSize: 18 }}>🔥</span>
          <span style={{ fontSize: 13, color: 'var(--accent)', fontWeight: 500 }}>
            {streak} day streak
          </span>
        </div>
        <span style={{ fontSize: 11, color: 'var(--text-muted)' }}>
          best: {bestStreak} days
        </span>
      </div>

      {/* ── Bottom nav ── */}
      <BottomNav active="dashboard" />

      {/* ── Floating + button ── */}
      <button
        type="button"
        onClick={() => navigate('/add-purchase')}
        style={{
          position: 'fixed',
          bottom: 76,
          right: 20,
          width: 52,
          height: 52,
          borderRadius: '50%',
          background: '#E63946',
          boxShadow: '0 4px 20px rgba(230,57,70,0.5)',
          border: 'none',
          color: '#FFFFFF',
          fontSize: 26,
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          zIndex: 50,
          padding: 0,
          lineHeight: 1,
        }}
      >
        +
      </button>
    </div>
  );
}

// ── Sub-components ────────────────────────────────────────────────────────────

function TxRow({ tx }) {
  const emoji = TX_CAT_EMOJI[tx.category] ?? '💸';
  let dateStr = '';
  try {
    dateStr = format(new Date(tx.date ?? tx.transaction_date), 'MMM d');
  } catch {
    dateStr = '';
  }

  return (
    <div
      style={{
        display: 'flex',
        alignItems: 'center',
        gap: 12,
        padding: '10px 16px',
      }}
    >
      {/* Emoji circle */}
      <div
        style={{
          width: 34,
          height: 34,
          borderRadius: '50%',
          background: 'var(--accent-muted)',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          fontSize: 16,
          flexShrink: 0,
        }}
      >
        {emoji}
      </div>

      {/* Merchant + date */}
      <div style={{ flex: 1, minWidth: 0 }}>
        <p
          style={{
            fontSize: 13,
            fontWeight: 400,
            whiteSpace: 'nowrap',
            overflow: 'hidden',
            textOverflow: 'ellipsis',
          }}
        >
          {tx.merchant ?? tx.description ?? 'Unknown'}
        </p>
        <p style={{ fontSize: 10, color: 'var(--text-muted)', marginTop: 1 }}>{dateStr}</p>
      </div>

      {/* Amount */}
      <span style={{ fontSize: 13, fontWeight: 500, flexShrink: 0 }}>
        {formatINR(tx.amount)}
      </span>
    </div>
  );
}

function LoadingSkeleton() {
  return (
    <div
      style={{
        height: '100vh',
        overflow: 'hidden',
        display: 'flex',
        flexDirection: 'column',
        maxWidth: 390,
        margin: '0 auto',
        padding: '12px 16px',
        gap: 12,
      }}
    >
      {/* Top bar */}
      <div className="shimmer-card" style={{ height: 24, width: '60%', borderRadius: 8 }} />

      {/* Orb */}
      <div style={{ display: 'flex', justifyContent: 'center', padding: '16px 0' }}>
        <div className="shimmer-card" style={{ width: 160, height: 160, borderRadius: '50%' }} />
      </div>

      {/* Spent/left */}
      <div className="shimmer-card" style={{ height: 64, borderRadius: 16 }} />

      {/* Pills */}
      <div style={{ display: 'flex', gap: 8, overflow: 'hidden' }}>
        {[1, 2, 3, 4].map((i) => (
          <div key={i} className="shimmer-card" style={{ width: 80, height: 32, borderRadius: 20, flexShrink: 0 }} />
        ))}
      </div>

      {/* Feed */}
      <div className="shimmer-card" style={{ flex: 1, borderRadius: 16 }} />

      {/* Streak */}
      <div className="shimmer-card" style={{ height: 44, borderRadius: 16 }} />

      <BottomNav active="dashboard" />
    </div>
  );
}

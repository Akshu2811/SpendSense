import React from 'react';
import { useNavigate } from 'react-router-dom';

const TABS = [
  { key: 'dashboard',  icon: '🏠', label: 'Home',     path: '/dashboard' },
  { key: 'shopcheck',  icon: '🛍️', label: 'Shop',     path: '/check-before-buy' },
  { key: 'report',     icon: '📊', label: 'Report',   path: '/report' },
  { key: 'settings',  icon: '⚙️', label: 'Settings', path: '/settings' },
];

export default function BottomNav({ active }) {
  const navigate = useNavigate();

  return (
    <nav
      style={{
        position: 'fixed',
        bottom: 0,
        left: 0,
        right: 0,
        height: 64,
        background: 'rgba(5,13,26,0.85)',
        backdropFilter: 'blur(20px)',
        WebkitBackdropFilter: 'blur(20px)',
        borderTop: '0.5px solid rgba(255,255,255,0.1)',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-around',
        zIndex: 100,
        paddingBottom: 'env(safe-area-inset-bottom)',
      }}
    >
      {TABS.map((tab) => {
        const isActive = tab.key === active;
        return (
          <button
            key={tab.key}
            type="button"
            onClick={() => navigate(tab.path)}
            style={{
              flex: 1,
              height: '100%',
              background: 'transparent',
              border: 'none',
              borderRadius: 0,
              display: 'flex',
              flexDirection: 'column',
              alignItems: 'center',
              justifyContent: 'center',
              gap: 3,
              padding: 0,
              color: isActive ? 'var(--accent)' : 'var(--text-muted)',
              transition: 'color 0.2s ease',
            }}
          >
            <span style={{ fontSize: 20, lineHeight: 1 }}>{tab.icon}</span>
            <span
              style={{
                fontSize: 9,
                fontWeight: isActive ? 600 : 400,
                letterSpacing: '0.04em',
                textTransform: 'uppercase',
              }}
            >
              {tab.label}
            </span>
          </button>
        );
      })}
    </nav>
  );
}

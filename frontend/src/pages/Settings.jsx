import React, { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { format } from 'date-fns';
import toast from 'react-hot-toast';
import {
  getWalletState, getCurrentBudget, updateBudget,
  syncTransactions, deleteAccount, uploadCsv,
} from '../services/api';
import { useAuth } from '../context/AuthContext';
import BottomNav from '../components/BottomNav';

export default function Settings() {
  const navigate = useNavigate();
  const { user, logout } = useAuth();

  const [budgetData,  setBudgetData]  = useState(null);
  const [editBudget,  setEditBudget]  = useState(false);
  const [budgetInput, setBudgetInput] = useState('');
  const [savingBudget,setSavingBudget]= useState(false);
  const [syncing,     setSyncing]     = useState(false);
  const [uploading,   setUploading]   = useState(false);
  const [lastSync,    setLastSync]    = useState('Never');
  const [showConfirm, setShowConfirm] = useState(false);
  const [deleting,    setDeleting]    = useState(false);

  useEffect(() => {
    document.body.className = 'state-calm';
    (async () => {
      try {
        const ws = await getWalletState();
        if (ws?.state) document.body.className = `state-${ws.state}`;
        const b = await getCurrentBudget();
        setBudgetData(b);
        setBudgetInput(String(b?.master_monthly ?? ''));
        if (b?.last_sync) setLastSync(format(new Date(b.last_sync), 'MMM d, h:mm a'));
      } catch {}
    })();
    return () => { document.body.className = ''; };
  }, []);

  const handleSaveBudget = async () => {
    const val = parseFloat(budgetInput);
    if (!val || val <= 0) { toast.error('Enter a valid amount'); return; }
    setSavingBudget(true);
    try {
      await updateBudget({ master_monthly: val });
      setBudgetData((prev) => ({ ...prev, master_monthly: val }));
      setEditBudget(false);
      toast.success('Budget updated!');
    } catch (err) {
      toast.error(err.response?.data?.detail ?? 'Could not update budget');
    } finally {
      setSavingBudget(false);
    }
  };

  const handleSync = async () => {
    setSyncing(true);
    try {
      await syncTransactions();
      toast.success('Synced!');
    } catch (err) {
      toast.error(err.response?.data?.detail ?? 'Sync failed. Try again.');
    } finally {
      setSyncing(false);
    }
  };

  const handleCsvUpload = async (e) => {
    const file = e.target.files[0];
    if (!file) return;
    setUploading(true);
    try {
      const result = await uploadCsv(file);
      toast.success(`${result.transactions_imported} transactions imported!`);
      setLastSync('Just now');
    } catch (err) {
      toast.error(err.response?.data?.detail || err.message || 'Upload failed. Try again.');
    } finally {
      setUploading(false);
      e.target.value = '';
    }
  };

  const handleLogout = () => {
    logout();
    navigate('/', { replace: true });
  };

  const handleDeleteConfirm = async () => {
    setDeleting(true);
    try {
      await deleteAccount();
    } catch {}
    logout();
    navigate('/register', { replace: true });
  };

  return (
    <div style={{ minHeight: '100vh', maxWidth: 390, margin: '0 auto', paddingBottom: 80 }}>
      {/* Header */}
      <h1 style={{ fontSize: 20, fontWeight: 500, padding: '20px 20px 16px' }}>settings ⚙️</h1>

      <div style={{ padding: '0 16px', display: 'flex', flexDirection: 'column', gap: 12 }}>

        {/* Budget section */}
        <div className="glass-card" style={{ overflow: 'hidden' }}>
          <p style={{ fontSize: 12, color: 'var(--text-muted)', letterSpacing: '0.08em', textTransform: 'uppercase', padding: '14px 16px 8px' }}>
            Budget
          </p>

          <div style={{ padding: '0 16px 16px' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
              {/* Left: label + large value */}
              <div>
                <p style={{ fontSize: 12, color: 'var(--text-muted)', marginBottom: 6 }}>monthly budget</p>
                <p style={{ fontSize: 24, fontWeight: 300, color: '#FFFFFF', lineHeight: 1 }}>
                  ₹{Number(budgetData?.master_monthly ?? 0).toLocaleString('en-IN')}
                </p>
              </div>
              {/* Right: Edit button (only when not editing) */}
              {!editBudget && (
                <button
                  type="button"
                  onClick={() => { setEditBudget(true); setBudgetInput(String(budgetData?.master_monthly ?? '')); }}
                  style={{
                    background: 'rgba(255,255,255,0.07)',
                    border: '1px solid rgba(255,255,255,0.15)',
                    color: 'var(--text-muted)',
                    borderRadius: 8, padding: '4px 12px',
                    height: 'auto', fontSize: 12, fontWeight: 500, flexShrink: 0,
                  }}
                >
                  Edit
                </button>
              )}
            </div>

            {editBudget && (
              <div className="slide-up" style={{ marginTop: 14 }}>
                <input
                  type="number" min="1"
                  value={budgetInput}
                  onChange={(e) => setBudgetInput(e.target.value)}
                  style={{ width: '100%', fontSize: 16, marginBottom: 10 }}
                  autoFocus
                />
                <div style={{ display: 'flex', gap: 8 }}>
                  <button
                    type="button"
                    disabled={savingBudget}
                    onClick={handleSaveBudget}
                    style={{
                      flex: 1, height: 40,
                      background: 'var(--accent)', color: '#050D1A',
                      borderRadius: 10, fontSize: 13, fontWeight: 600, border: 'none',
                    }}
                  >
                    {savingBudget ? '...' : 'Save'}
                  </button>
                  <button
                    type="button"
                    onClick={() => { setEditBudget(false); setBudgetInput(String(budgetData?.master_monthly ?? '')); }}
                    style={{
                      flex: 1, height: 40,
                      background: 'rgba(255,255,255,0.07)',
                      border: '1px solid rgba(255,255,255,0.15)',
                      color: 'var(--text-muted)',
                      borderRadius: 10, fontSize: 13,
                    }}
                  >
                    Cancel
                  </button>
                </div>
              </div>
            )}
          </div>
        </div>

        {/* Data & Sync section */}
        <div className="glass-card" style={{ padding: '14px 16px' }}>
          <p style={{ fontSize: 12, color: 'var(--text-muted)', letterSpacing: '0.08em', textTransform: 'uppercase', marginBottom: 12 }}>
            Data & Sync
          </p>
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
            <div>
              <p style={{ fontSize: 14, color: 'var(--text-muted)' }}>Last sync</p>
              <p style={{ fontSize: 12, color: 'var(--text-faint)', marginTop: 2 }}>{lastSync}</p>
            </div>
            <button
              type="button"
              disabled={syncing}
              onClick={handleSync}
              style={{
                background: 'rgba(255,255,255,0.07)', border: '1px solid rgba(255,255,255,0.15)',
                color: syncing ? 'var(--text-faint)' : 'var(--text-muted)',
                borderRadius: 10, padding: '0 16px', height: 36, fontSize: 13, flexShrink: 0,
              }}
            >
              {syncing ? 'Syncing...' : 'Sync Now'}
            </button>
          </div>

          <div style={{ borderTop: '1px solid rgba(255,255,255,0.08)', margin: '12px 0' }} />

          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
            <div>
              <span style={{ display: 'block', fontSize: 13, color: '#FFFFFF' }}>Import bank CSV</span>
              <span style={{ display: 'block', fontSize: 11, color: 'var(--text-muted)', marginTop: 2 }}>
                Upload UPI or bank statement export
              </span>
            </div>
            <button
              type="button"
              disabled={uploading}
              style={{
                position: 'relative',
                background: 'rgba(255,255,255,0.07)',
                border: '1px solid rgba(255,255,255,0.15)',
                color: uploading ? 'var(--text-faint)' : 'var(--text-muted)',
                borderRadius: 10, padding: '6px 12px', fontSize: 13,
                flexShrink: 0, cursor: uploading ? 'default' : 'pointer',
              }}
            >
              <input
                type="file"
                accept=".csv"
                onChange={handleCsvUpload}
                style={{
                  position: 'absolute', inset: 0, opacity: 0,
                  width: '100%', height: '100%',
                  cursor: uploading ? 'default' : 'pointer',
                  pointerEvents: uploading ? 'none' : 'auto',
                }}
              />
              <span style={{ pointerEvents: 'none' }}>
                {uploading ? 'Importing...' : 'Upload CSV'}
              </span>
            </button>
          </div>
        </div>

        {/* Account section */}
        <div className="glass-card" style={{ padding: '14px 16px' }}>
          <p style={{ fontSize: 12, color: 'var(--text-muted)', letterSpacing: '0.08em', textTransform: 'uppercase', marginBottom: 12 }}>
            Account
          </p>
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 12 }}>
            <span style={{ fontSize: 14, color: 'var(--text-muted)' }}>Signed in as</span>
            <span style={{ fontSize: 14, fontWeight: 500 }}>{user?.username ?? '—'}</span>
          </div>
          <button
            type="button"
            onClick={handleLogout}
            style={{
              width: '100%', height: 40,
              background: 'rgba(255,255,255,0.07)', border: '1px solid rgba(255,255,255,0.15)',
              color: 'var(--text-muted)', borderRadius: 12, fontSize: 14,
            }}
          >
            Log Out
          </button>
        </div>

        {/* Danger zone */}
        <div
          className="glass-card"
          style={{ padding: '14px 16px', border: '1px solid rgba(230,57,70,0.25)', marginBottom: 8 }}
        >
          <p style={{ fontSize: 12, color: '#E63946', letterSpacing: '0.08em', textTransform: 'uppercase', marginBottom: 12 }}>
            Danger Zone
          </p>
          <button
            type="button"
            onClick={() => setShowConfirm(true)}
            style={{
              width: '100%', height: 44,
              background: 'rgba(230,57,70,0.12)', border: '1px solid rgba(230,57,70,0.25)',
              color: '#E63946', borderRadius: 12, fontSize: 14, fontWeight: 500,
            }}
          >
            Delete all my data
          </button>
        </div>
      </div>

      {/* Confirmation modal */}
      {showConfirm && (
        <>
          <div
            className="fade-in"
            style={{ position: 'fixed', inset: 0, background: 'rgba(0,0,0,0.7)', zIndex: 50 }}
            onClick={() => !deleting && setShowConfirm(false)}
          />
          <div
            className="glass-card slide-up"
            style={{
              position: 'fixed', top: '50%', left: '50%',
              transform: 'translate(-50%, -50%)',
              width: 'min(340px, calc(100vw - 40px))',
              padding: 24, zIndex: 51,
            }}
          >
            <h2 style={{ fontSize: 18, color: '#FFFFFF', marginBottom: 8 }}>Are you sure?</h2>
            <p style={{ fontSize: 13, color: 'var(--text-muted)', lineHeight: 1.6, marginBottom: 20 }}>
              This permanently deletes all your SpendSense data — budgets, purchases, nudges, and reports.
            </p>
            <div style={{ display: 'flex', gap: 10 }}>
              <button
                type="button"
                disabled={deleting}
                onClick={() => setShowConfirm(false)}
                style={{ flex: 1, height: 44, background: 'rgba(255,255,255,0.07)', border: '1px solid rgba(255,255,255,0.15)', color: 'var(--text-muted)', borderRadius: 12, fontSize: 14 }}
              >
                Cancel
              </button>
              <button
                type="button"
                disabled={deleting}
                onClick={handleDeleteConfirm}
                style={{ flex: 1, height: 44, background: 'rgba(230,57,70,0.2)', border: '1px solid rgba(230,57,70,0.4)', color: '#E63946', borderRadius: 12, fontSize: 13, fontWeight: 500 }}
              >
                {deleting ? 'Deleting...' : 'Yes, delete everything'}
              </button>
            </div>
          </div>
        </>
      )}

      <BottomNav active="settings" />
    </div>
  );
}

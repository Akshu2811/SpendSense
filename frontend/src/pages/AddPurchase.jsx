import React, { useEffect, useState, useRef } from 'react';
import { useNavigate } from 'react-router-dom';
import toast from 'react-hot-toast';
import { getWalletState, uploadScreenshots, addManual } from '../services/api';

const PLATFORMS = [
  'Myntra','Amazon','Flipkart','Zepto','Blinkit','Swiggy','Ajio','Nykaa','Other',
];

const CATEGORIES = [
  { value: 'food_dining_delivery',  label: '🍕 Food & Delivery' },
  { value: 'shopping_fashion',      label: '👗 Fashion' },
  { value: 'electronics_tech',      label: '📱 Electronics' },
  { value: 'entertainment_subs',    label: '🎬 Entertainment' },
  { value: 'health_lifestyle',      label: '💊 Health' },
  { value: 'others',                label: '💸 Others' },
];

const yesterday = () => {
  const d = new Date();
  d.setDate(d.getDate() - 1);
  return d.toISOString().split('T')[0];
};

export default function AddPurchase() {
  const navigate = useNavigate();
  const fileRef  = useRef(null);

  // Screenshot state machine
  const [status,        setStatus]        = useState('idle');
  const [extracted,     setExtracted]     = useState(null);
  const [dateVal,       setDateVal]       = useState('');
  const [selectedFiles, setSelectedFiles] = useState([]);
  const [previewUrls,   setPreviewUrls]   = useState([]);

  // Manual form
  const [manual,  setManual]  = useState({ item: '', platform: 'Myntra', amount: '', category: 'shopping_fashion' });
  const [saving,  setSaving]  = useState(false);

  useEffect(() => {
    document.body.className = 'state-calm';
    (async () => {
      try { const ws = await getWalletState(); if (ws?.state) document.body.className = `state-${ws.state}`; } catch {}
    })();
    return () => { document.body.className = ''; };
  }, []);

  // ── Screenshot handlers ──────────────────────────────────────────────────
  const handleFileChange = (e) => {
    const incoming = Array.from(e.target.files || []);
    if (!incoming.length) return;
    // Revoke old URLs before creating new ones
    previewUrls.forEach(url => URL.revokeObjectURL(url));
    const combined = [...selectedFiles, ...incoming].slice(0, 3);
    setSelectedFiles(combined);
    setPreviewUrls(combined.map(f => URL.createObjectURL(f)));
    if (fileRef.current) fileRef.current.value = '';
  };

  const removeFile = (index) => {
    URL.revokeObjectURL(previewUrls[index]);
    setSelectedFiles(prev => prev.filter((_, i) => i !== index));
    setPreviewUrls(prev => prev.filter((_, i) => i !== index));
  };

  const handleAnalyseScreenshots = async () => {
    if (!selectedFiles.length) return;
    // Snapshot URLs before clearing so we can revoke after the await
    const snapshotUrls = [...previewUrls];
    setStatus('loading');
    setExtracted(null);
    try {
      const result = await uploadScreenshots(selectedFiles);
      setExtracted(result.purchase ?? result.preview ?? null);
      // Normalise 'saved' → 'success' so the success block renders
      const displayStatus = result.status === 'saved' ? 'success' : (result.status ?? 'success');
      setStatus(displayStatus);
      if (displayStatus === 'already_logged') {
        setTimeout(() => setStatus('idle'), 2000);
      }
    } catch (err) {
      setStatus('idle');
      setExtracted(null);
      toast.error('Something went wrong. Please try again.');
    }
    snapshotUrls.forEach(url => URL.revokeObjectURL(url));
    setPreviewUrls([]);
    setSelectedFiles([]);
    if (fileRef.current) fileRef.current.value = '';
  };

  const resetScreenshot = () => {
    previewUrls.forEach(url => URL.revokeObjectURL(url));
    setStatus('idle');
    setExtracted(null);
    setDateVal('');
    setSelectedFiles([]);
    setPreviewUrls([]);
  };

  const confirmWithDate = async (date) => {
    if (!extracted) return;
    try {
      await addManual(
        extracted.item_name ?? extracted.name ?? '',
        extracted.platform ?? '',
        parseFloat(extracted.amount ?? 0),
        extracted.category ?? 'others',
      );
      toast.success('Added to history! ✓');
      resetScreenshot();
    } catch (err) {
      toast.error(err.response?.data?.detail ?? 'Could not save. Try again.');
    }
  };

  // ── Manual form handler ──────────────────────────────────────────────────
  const handleManualChange = (field, value) =>
    setManual((prev) => ({ ...prev, [field]: value }));

  const handleManualSubmit = async (e) => {
    e.preventDefault();
    if (!manual.item.trim() || !manual.platform || !manual.amount || !manual.category) {
      toast.error('Please fill in all 4 fields');
      return;
    }
    const amount = parseFloat(manual.amount);
    if (!amount || amount <= 0) { toast.error('Enter a valid amount'); return; }
    setSaving(true);
    try {
      await addManual(manual.item.trim(), manual.platform, amount, manual.category);
      toast.success('Added! ✓');
      setManual({ item: '', platform: 'Myntra', amount: '', category: 'shopping_fashion' });
    } catch (err) {
      toast.error(err.response?.data?.detail ?? 'Could not save. Try again.');
    } finally {
      setSaving(false);
    }
  };

  const isCardClickable = status === 'idle' && selectedFiles.length === 0;

  // ── Render ───────────────────────────────────────────────────────────────
  return (
    <div style={{ minHeight: '100vh', maxWidth: 390, margin: '0 auto', paddingBottom: 40 }}>
      {/* Header */}
      <div style={{ display: 'flex', alignItems: 'center', gap: 12, padding: '16px 20px 12px' }}>
        <button
          type="button"
          onClick={() => navigate(-1)}
          style={{ background: 'transparent', border: 'none', color: 'var(--text-muted)', fontSize: 20, padding: 0, height: 'auto', width: 'auto', lineHeight: 1 }}
        >←</button>
        <h1 style={{ fontSize: 18, fontWeight: 500 }}>add purchase</h1>
      </div>

      <div style={{ padding: '0 16px', display: 'flex', flexDirection: 'column', gap: 12 }}>

        {/* ── Screenshot card ── */}
        <div
          className="glass-card"
          style={{ padding: 16, cursor: isCardClickable ? 'pointer' : 'default', position: 'relative', overflow: 'hidden' }}
          onClick={() => isCardClickable && fileRef.current?.click()}
        >
          {/* Hidden input — multiple files, 3-cap enforced in handler */}
          <input
            ref={fileRef}
            type="file"
            accept="image/*"
            multiple
            style={{ display: 'none' }}
            onChange={handleFileChange}
          />

          {/* IDLE — no files yet */}
          {status === 'idle' && selectedFiles.length === 0 && (
            <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
              <span style={{ fontSize: 28, flexShrink: 0 }}>📸</span>
              <div>
                <p style={{ fontSize: 15, fontWeight: 500 }}>Upload Screenshots</p>
                <p style={{ fontSize: 12, color: 'var(--text-muted)', marginTop: 2 }}>
                  Upload up to 3 screenshots — Gemini reads them all
                </p>
              </div>
              <span style={{ marginLeft: 'auto', color: 'var(--text-muted)', fontSize: 20 }}>›</span>
            </div>
          )}

          {/* IDLE — files selected: thumbnail strip + analyse button */}
          {status === 'idle' && selectedFiles.length > 0 && (
            <div>
              <div style={{ display: 'flex', gap: 8, marginBottom: 10 }}>
                {previewUrls.map((url, i) => (
                  <div key={i} style={{ position: 'relative', flexShrink: 0 }}>
                    <img
                      src={url}
                      alt={`screenshot ${i + 1}`}
                      style={{ width: 60, height: 60, borderRadius: 8, objectFit: 'cover', display: 'block' }}
                    />
                    <button
                      type="button"
                      onClick={(e) => { e.stopPropagation(); removeFile(i); }}
                      style={{
                        position: 'absolute', top: -6, right: -6,
                        width: 18, height: 18, borderRadius: '50%',
                        background: '#E63946', border: 'none',
                        color: '#fff', fontSize: 9, lineHeight: 1,
                        display: 'flex', alignItems: 'center', justifyContent: 'center',
                        padding: 0, cursor: 'pointer', flexShrink: 0,
                      }}
                    >✕</button>
                  </div>
                ))}
                {selectedFiles.length < 3 && (
                  <button
                    type="button"
                    onClick={(e) => { e.stopPropagation(); fileRef.current?.click(); }}
                    style={{
                      width: 60, height: 60, borderRadius: 8,
                      background: 'rgba(255,255,255,0.05)',
                      border: '1px dashed rgba(255,255,255,0.2)',
                      color: 'var(--text-muted)', fontSize: 22,
                      display: 'flex', alignItems: 'center', justifyContent: 'center',
                      cursor: 'pointer', flexShrink: 0,
                    }}
                  >+</button>
                )}
              </div>
              <p style={{ fontSize: 12, color: 'var(--text-muted)', marginBottom: 12 }}>
                {selectedFiles.length} screenshot{selectedFiles.length > 1 ? 's' : ''} selected
              </p>
              <button
                type="button"
                onClick={(e) => { e.stopPropagation(); handleAnalyseScreenshots(); }}
                style={{
                  width: '100%', height: 44,
                  background: 'var(--accent)', color: '#050D1A',
                  borderRadius: 12, fontSize: 14, fontWeight: 600,
                  border: 'none', cursor: 'pointer',
                }}
              >
                Analyse Screenshots
              </button>
            </div>
          )}

          {/* LOADING */}
          {status === 'loading' && (
            <div>
              <div className="shimmer-card" style={{ height: 14, width: '55%', borderRadius: 7, marginBottom: 10 }} />
              <div className="shimmer-card" style={{ height: 10, width: '75%', borderRadius: 5, marginBottom: 6 }} />
              <div className="shimmer-card" style={{ height: 10, width: '40%', borderRadius: 5, marginBottom: 14 }} />
              <p style={{ fontSize: 12, color: 'var(--text-muted)' }}>Reading your order... ✨</p>
              {selectedFiles.length > 0 && (
                <p style={{ fontSize: 11, color: 'var(--text-faint)', marginTop: 4 }}>
                  Analysing {selectedFiles.length} screenshot{selectedFiles.length > 1 ? 's' : ''} with Gemini
                </p>
              )}
            </div>
          )}

          {/* SUCCESS */}
          {status === 'success' && extracted && (
            <div>
              <p style={{ fontSize: 15, color: '#FFFFFF', fontWeight: 500, marginBottom: 4 }}>
                {String(extracted?.item_name || extracted?.name || '')}
              </p>
              <p style={{ fontSize: 13, color: 'var(--text-muted)', marginBottom: 2 }}>
                {String(extracted?.platform || '')} · ₹{Number(extracted?.amount ?? 0).toLocaleString('en-IN')}
              </p>
              <p style={{ fontSize: 12, color: 'var(--text-faint)', marginBottom: 14 }}>
                {String(extracted?.order_date || extracted?.date || '')}
              </p>
              <div style={{ display: 'flex', gap: 10 }}>
                <button type="button" className="btn-primary" style={{ flex: 1, height: 40, fontSize: 13 }}
                  onClick={() => { toast.success('Added to history! ✓'); resetScreenshot(); }}>
                  ✓ Looks right!
                </button>
                <button type="button" className="btn-secondary" style={{ flex: 1, height: 40, fontSize: 13 }}
                  onClick={resetScreenshot}>
                  Try again
                </button>
              </div>
            </div>
          )}

          {/* DATE_UNCONFIRMED */}
          {status === 'date_unconfirmed' && (
            <div>
              <div style={{ background: 'rgba(247,127,0,0.12)', border: '1px solid rgba(247,127,0,0.3)', borderRadius: 10, padding: '8px 12px', marginBottom: 12 }}>
                <p style={{ fontSize: 12, color: '#FFB347' }}>📅 Couldn't find the order date</p>
              </div>
              {extracted && (
                <>
                  <p style={{ fontSize: 14, fontWeight: 500, marginBottom: 2 }}>{String(extracted?.item_name || extracted?.name || '')}</p>
                  <p style={{ fontSize: 12, color: 'var(--text-muted)', marginBottom: 12 }}>
                    {String(extracted?.platform || '')} · ₹{Number(extracted?.amount ?? 0).toLocaleString('en-IN')}
                  </p>
                </>
              )}
              <label className="field-label">Order date</label>
              <input type="date" value={dateVal} onChange={(e) => setDateVal(e.target.value)} style={{ marginBottom: 10 }} />
              <div style={{ display: 'flex', gap: 10 }}>
                <button type="button" className="btn-primary" style={{ flex: 1, height: 40, fontSize: 13 }}
                  onClick={() => confirmWithDate(dateVal)}>
                  Confirm Date
                </button>
                <button type="button" className="btn-secondary" style={{ flex: 1, height: 40, fontSize: 13 }}
                  onClick={() => confirmWithDate(yesterday())}>
                  Use Yesterday
                </button>
              </div>
            </div>
          )}

          {/* ALREADY_LOGGED */}
          {status === 'already_logged' && (
            <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
              <span
                style={{
                  display: 'inline-flex', alignItems: 'center', gap: 6,
                  background: 'var(--accent-muted)', border: '1px solid var(--accent)',
                  borderRadius: 20, padding: '6px 14px', fontSize: 13, color: 'var(--accent)',
                }}
              >
                ✓ Already in your history
              </span>
            </div>
          )}

          {/* ERROR */}
          {status === 'error' && (
            <div>
              <p style={{ fontSize: 13, color: '#E63946', marginBottom: 12 }}>
                Couldn't read these images. Try clearer screenshots.
              </p>
              <div style={{ display: 'flex', gap: 10, alignItems: 'center' }}>
                <button type="button" className="btn-primary" style={{ height: 40, fontSize: 13, flex: 1 }}
                  onClick={resetScreenshot}>
                  Try Again
                </button>
                <button type="button"
                  style={{ background: 'transparent', border: 'none', height: 'auto', padding: 0, fontSize: 13, color: 'var(--text-muted)', textDecoration: 'underline', textUnderlineOffset: 3 }}
                  onClick={resetScreenshot}>
                  Add manually instead
                </button>
              </div>
            </div>
          )}
        </div>

        {/* ── Manual card ── */}
        <div className="glass-card" style={{ padding: 16 }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 10, marginBottom: 12 }}>
            <span style={{ fontSize: 22 }}>✏️</span>
            <div>
              <p style={{ fontSize: 15, fontWeight: 500 }}>Add Manually</p>
              <p style={{ fontSize: 12, color: 'var(--text-muted)', marginTop: 2 }}>
                Takes under 20 seconds
              </p>
            </div>
          </div>

          <form onSubmit={handleManualSubmit} style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
            <div>
              <label className="field-label">What did you buy?</label>
              <input type="text" placeholder="Blue Printed Kurta"
                value={manual.item} onChange={(e) => handleManualChange('item', e.target.value)} />
            </div>

            <div>
              <label className="field-label">Where?</label>
              <select value={manual.platform} onChange={(e) => handleManualChange('platform', e.target.value)}>
                {PLATFORMS.map((p) => <option key={p} value={p}>{p}</option>)}
              </select>
            </div>

            <div>
              <label className="field-label">How much? (₹)</label>
              <input type="number" min="1" placeholder="899"
                value={manual.amount} onChange={(e) => handleManualChange('amount', e.target.value)} />
            </div>

            <div>
              <label className="field-label">Category?</label>
              <select value={manual.category} onChange={(e) => handleManualChange('category', e.target.value)}>
                {CATEGORIES.map((c) => <option key={c.value} value={c.value}>{c.label}</option>)}
              </select>
            </div>

            <button
              type="submit"
              disabled={saving}
              style={{
                height: 44, marginTop: 8,
                background: saving ? 'var(--accent-muted)' : 'var(--accent)',
                color: '#050D1A', fontWeight: 600, fontSize: 14,
                borderRadius: 14, border: 'none', width: '100%',
                display: 'flex', alignItems: 'center', justifyContent: 'center', gap: 8,
              }}
            >
              {saving ? <><Spinner /> Saving...</> : 'Save Purchase'}
            </button>
          </form>
        </div>
      </div>
    </div>
  );
}

function Spinner() {
  return (
    <span style={{
      display: 'inline-block', width: 14, height: 14,
      border: '2px solid rgba(5,13,26,0.3)', borderTopColor: '#050D1A',
      borderRadius: '50%', animation: 'spin 0.7s linear infinite',
    }} />
  );
}

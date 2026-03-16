import React from 'react'

const s = {
  bar: {
    display: 'flex', gap: 12, alignItems: 'center', flexWrap: 'wrap',
    padding: '16px 0', borderTop: '1px solid #e2e8f0', marginTop: 8,
  },
  btn: {
    padding: '10px 22px', borderRadius: 8, border: 'none', cursor: 'pointer',
    fontFamily: 'Inter, sans-serif', fontSize: 14, fontWeight: 600,
    transition: 'opacity 0.2s',
  },
  analyzeBtn: { background: '#7C3AED', color: '#fff' },
  exportBtn: { background: '#1F4E79', color: '#fff' },
  calAllBtn: { background: '#0B8043', color: '#fff' },
  resetBtn: { background: 'none', color: '#718096', border: '1.5px solid #cbd5e0' },
  count: { fontSize: 13, color: '#718096', marginLeft: 'auto' },
}

export default function ActionBar({
  hasRawData,
  hasProcessed,
  loading,
  authStatus,
  equipmentCount,
  onAnalyze,
  onExport,
  onAddAll,
  onReset,
}) {
  const calDisabled = !authStatus?.authenticated || !hasProcessed || loading

  return (
    <div style={s.bar}>
      {hasRawData && !hasProcessed && (
        <button
          style={{ ...s.btn, ...s.analyzeBtn, opacity: loading ? 0.6 : 1 }}
          onClick={onAnalyze}
          disabled={loading}
        >
          {loading ? 'Analyzing...' : '✨ Analyze with Gemini'}
        </button>
      )}

      {hasProcessed && (
        <>
          <button
            style={{ ...s.btn, ...s.exportBtn }}
            onClick={onExport}
            disabled={loading}
          >
            ⬇ Download XLSX
          </button>
          <button
            style={{ ...s.btn, ...s.calAllBtn, opacity: calDisabled ? 0.5 : 1 }}
            onClick={onAddAll}
            disabled={calDisabled}
            title={!authStatus?.authenticated ? 'Connect Google account to add calendar events' : ''}
          >
            📅 Add All to Calendar
          </button>
        </>
      )}

      {(hasRawData || hasProcessed) && (
        <button style={{ ...s.btn, ...s.resetBtn }} onClick={onReset} disabled={loading}>
          Reset
        </button>
      )}

      {equipmentCount > 0 && (
        <span style={s.count}>{equipmentCount} item{equipmentCount !== 1 ? 's' : ''}</span>
      )}
    </div>
  )
}

import React from 'react'

const VARIANTS = {
  idle: { bg: '#edf2f7', color: '#4a5568', label: 'Idle' },
  uploading: { bg: '#ebf8ff', color: '#2b6cb0', label: 'Uploading...' },
  processing: { bg: '#fffbeb', color: '#b7791f', label: 'Analyzing with Gemini...' },
  done: { bg: '#f0fff4', color: '#276749', label: 'Done' },
  error: { bg: '#fff5f5', color: '#c53030', label: 'Error' },
}

export default function StatusBadge({ status, message }) {
  const v = VARIANTS[status] || VARIANTS.idle
  return (
    <div style={{
      display: 'inline-flex', alignItems: 'center', gap: 8,
      background: v.bg, color: v.color,
      borderRadius: 20, padding: '6px 14px', fontSize: 13, fontWeight: 600,
    }}>
      {status === 'processing' && (
        <span style={{
          width: 10, height: 10, borderRadius: '50%',
          border: `2px solid ${v.color}`, borderTopColor: 'transparent',
          display: 'inline-block',
          animation: 'spin 0.8s linear infinite',
        }} />
      )}
      {v.label}{message ? `: ${message}` : ''}
      <style>{`@keyframes spin { to { transform: rotate(360deg); } }`}</style>
    </div>
  )
}

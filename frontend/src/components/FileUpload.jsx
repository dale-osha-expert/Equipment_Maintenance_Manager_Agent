import React, { useRef, useState } from 'react'

const s = {
  wrap: { display: 'flex', flexDirection: 'column', gap: 16 },
  dropZone: {
    border: '2px dashed #a0aec0', borderRadius: 12, padding: '40px 24px',
    textAlign: 'center', cursor: 'pointer', transition: 'all 0.2s',
    background: '#fff',
  },
  dropZoneActive: { borderColor: '#4285F4', background: '#ebf8ff' },
  icon: { fontSize: 40, marginBottom: 8 },
  title: { fontWeight: 600, fontSize: 16, color: '#2d3748', marginBottom: 4 },
  sub: { fontSize: 13, color: '#718096' },
  or: { textAlign: 'center', color: '#a0aec0', fontSize: 13, fontWeight: 600, letterSpacing: 1 },
  sheetsRow: { display: 'flex', gap: 8 },
  input: {
    flex: 1, padding: '10px 14px', borderRadius: 8, border: '1.5px solid #cbd5e0',
    fontSize: 14, outline: 'none', fontFamily: 'Inter, sans-serif',
  },
  btn: {
    padding: '10px 20px', borderRadius: 8, border: 'none', cursor: 'pointer',
    background: '#4285F4', color: '#fff', fontWeight: 600, fontSize: 14,
    fontFamily: 'Inter, sans-serif', whiteSpace: 'nowrap',
  },
  fileBtn: {
    display: 'inline-block', marginTop: 10, padding: '8px 20px',
    borderRadius: 8, border: '1.5px solid #cbd5e0', cursor: 'pointer',
    background: '#fff', fontWeight: 500, fontSize: 13, fontFamily: 'Inter, sans-serif',
  },
}

export default function FileUpload({ onXlsxUpload, onSheetsImport, loading, authStatus }) {
  const [dragging, setDragging] = useState(false)
  const [sheetUrl, setSheetUrl] = useState('')
  const fileRef = useRef()

  const handleDrop = (e) => {
    e.preventDefault()
    setDragging(false)
    const file = e.dataTransfer.files[0]
    if (file) onXlsxUpload(file)
  }

  const handleFileChange = (e) => {
    const file = e.target.files[0]
    if (file) onXlsxUpload(file)
  }

  const handleSheetsImport = () => {
    if (sheetUrl.trim()) onSheetsImport(sheetUrl.trim())
  }

  return (
    <div style={s.wrap}>
      {/* XLSX Drop Zone */}
      <div
        style={{ ...s.dropZone, ...(dragging ? s.dropZoneActive : {}) }}
        onDragOver={(e) => { e.preventDefault(); setDragging(true) }}
        onDragLeave={() => setDragging(false)}
        onDrop={handleDrop}
        onClick={() => fileRef.current?.click()}
      >
        <div style={s.icon}>📊</div>
        <div style={s.title}>Drop your spreadsheet here</div>
        <div style={s.sub}>Supports .xlsx and .xls files</div>
        <label style={s.fileBtn} onClick={(e) => e.stopPropagation()}>
          Browse file
          <input
            ref={fileRef}
            type="file"
            accept=".xlsx,.xls"
            style={{ display: 'none' }}
            onChange={handleFileChange}
            disabled={loading}
          />
        </label>
      </div>

      <div style={s.or}>— OR —</div>

      {/* Google Sheets URL */}
      <div>
        <div style={{ fontSize: 13, fontWeight: 600, color: '#4a5568', marginBottom: 6 }}>
          Import from Google Sheets
          {!authStatus?.authenticated && (
            <span style={{ marginLeft: 8, color: '#a0aec0', fontWeight: 400 }}>
              (Connect Google account first)
            </span>
          )}
        </div>
        <div style={s.sheetsRow}>
          <input
            style={s.input}
            placeholder="https://docs.google.com/spreadsheets/d/..."
            value={sheetUrl}
            onChange={(e) => setSheetUrl(e.target.value)}
            disabled={loading || !authStatus?.authenticated}
          />
          <button
            style={{ ...s.btn, opacity: (!authStatus?.authenticated || loading) ? 0.5 : 1 }}
            onClick={handleSheetsImport}
            disabled={!authStatus?.authenticated || loading || !sheetUrl.trim()}
          >
            Import
          </button>
        </div>
      </div>
    </div>
  )
}

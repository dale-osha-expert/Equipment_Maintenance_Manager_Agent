import React, { useCallback, useEffect, useState } from 'react'
import ActionBar from './components/ActionBar.jsx'
import AuthButton from './components/AuthButton.jsx'
import EquipmentTable from './components/EquipmentTable.jsx'
import FileUpload from './components/FileUpload.jsx'
import StatusBadge from './components/StatusBadge.jsx'
import {
  addAllToCalendar,
  addToCalendar,
  checkAuthStatus,
  exportXlsx,
  importSheets,
  processEquipment,
  uploadXlsx,
} from './services/api.js'

const s = {
  app: { minHeight: '100vh', background: '#f0f4f8', padding: '0 0 40px' },
  header: {
    background: '#1F4E79', color: '#fff', padding: '0 32px',
    display: 'flex', alignItems: 'center', justifyContent: 'space-between',
    height: 64, boxShadow: '0 2px 8px rgba(0,0,0,0.15)',
  },
  logo: { display: 'flex', alignItems: 'center', gap: 10 },
  logoText: { fontSize: 20, fontWeight: 700 },
  logoSub: { fontSize: 12, opacity: 0.7, marginTop: 2 },
  main: { maxWidth: 1400, margin: '32px auto', padding: '0 24px' },
  card: {
    background: '#fff', borderRadius: 14, boxShadow: '0 2px 12px rgba(0,0,0,0.07)',
    padding: 28, marginBottom: 24,
  },
  cardTitle: { fontSize: 15, fontWeight: 700, color: '#2d3748', marginBottom: 16 },
  errorBox: {
    background: '#fff5f5', border: '1px solid #fed7d7', borderRadius: 8,
    padding: '12px 16px', color: '#c53030', fontSize: 13, marginBottom: 16,
  },
  successBox: {
    background: '#f0fff4', border: '1px solid #c6f6d5', borderRadius: 8,
    padding: '12px 16px', color: '#276749', fontSize: 13, marginBottom: 16,
  },
  statusRow: { display: 'flex', alignItems: 'center', gap: 12, marginBottom: 16 },
}

export default function App() {
  const [authStatus, setAuthStatus] = useState(null)
  const [rawEquipment, setRawEquipment] = useState([])
  const [processedEquipment, setProcessedEquipment] = useState([])
  const [status, setStatus] = useState('idle')
  const [errorMsg, setErrorMsg] = useState('')
  const [successMsg, setSuccessMsg] = useState('')
  const [addingIds, setAddingIds] = useState(new Set())

  const refreshAuth = useCallback(async () => {
    try {
      const data = await checkAuthStatus()
      setAuthStatus(data)
    } catch {
      setAuthStatus({ authenticated: false, email: '' })
    }
  }, [])

  useEffect(() => {
    refreshAuth()
    // Handle OAuth redirect params
    const params = new URLSearchParams(window.location.search)
    if (params.get('auth') === 'success') {
      refreshAuth()
      setSuccessMsg('Google account connected successfully!')
      window.history.replaceState({}, '', '/')
      setTimeout(() => setSuccessMsg(''), 4000)
    } else if (params.get('auth') === 'error') {
      setErrorMsg(`Google auth failed: ${params.get('reason') || 'unknown error'}`)
      window.history.replaceState({}, '', '/')
    }
  }, [refreshAuth])

  const handleError = (msg) => {
    setErrorMsg(msg)
    setStatus('error')
    setTimeout(() => setErrorMsg(''), 6000)
  }

  const handleXlsxUpload = async (file) => {
    setErrorMsg('')
    setStatus('uploading')
    try {
      const items = await uploadXlsx(file)
      setRawEquipment(items)
      setProcessedEquipment([])
      setStatus('idle')
    } catch (err) {
      handleError(err.response?.data?.detail || 'Failed to upload file')
    }
  }

  const handleSheetsImport = async (url) => {
    setErrorMsg('')
    setStatus('uploading')
    try {
      const items = await importSheets(url)
      setRawEquipment(items)
      setProcessedEquipment([])
      setStatus('idle')
    } catch (err) {
      handleError(err.response?.data?.detail || 'Failed to import Google Sheet')
    }
  }

  const handleAnalyze = async () => {
    setErrorMsg('')
    setStatus('processing')
    try {
      const results = await processEquipment(rawEquipment)
      setProcessedEquipment(results)
      setStatus('done')
    } catch (err) {
      handleError(err.response?.data?.detail || 'Gemini analysis failed')
    }
  }

  const handleExport = async () => {
    try {
      await exportXlsx(processedEquipment)
    } catch (err) {
      handleError('Failed to export XLSX')
    }
  }

  const handleAddToCalendar = async (item) => {
    setAddingIds(prev => new Set(prev).add(item.id))
    try {
      const result = await addToCalendar(item)
      setProcessedEquipment(prev =>
        prev.map(e => e.id === item.id ? { ...e, calendar_event_id: result.event_id } : e)
      )
      setSuccessMsg(`Maintenance reminder added to Google Calendar!`)
      setTimeout(() => setSuccessMsg(''), 3000)
    } catch (err) {
      handleError(err.response?.data?.detail || 'Failed to add calendar event')
    } finally {
      setAddingIds(prev => { const s = new Set(prev); s.delete(item.id); return s })
    }
  }

  const handleAddAll = async () => {
    setErrorMsg('')
    const eligible = processedEquipment.filter(e => e.next_maintenance_date && !e.calendar_event_id)
    if (!eligible.length) {
      setSuccessMsg('All events already added to calendar!')
      return
    }
    const ids = new Set(eligible.map(e => e.id))
    setAddingIds(ids)
    try {
      const result = await addAllToCalendar(processedEquipment)
      const resultMap = result.results || {}
      setProcessedEquipment(prev =>
        prev.map(e => {
          const eventId = resultMap[e.id]
          if (eventId && !eventId.startsWith('error:')) {
            return { ...e, calendar_event_id: eventId }
          }
          return e
        })
      )
      setSuccessMsg(`${Object.keys(resultMap).length} maintenance reminder(s) added to Google Calendar!`)
      setTimeout(() => setSuccessMsg(''), 4000)
    } catch (err) {
      handleError(err.response?.data?.detail || 'Failed to add calendar events')
    } finally {
      setAddingIds(new Set())
    }
  }

  const handleReset = () => {
    setRawEquipment([])
    setProcessedEquipment([])
    setStatus('idle')
    setErrorMsg('')
    setSuccessMsg('')
    setAddingIds(new Set())
  }

  const isLoading = status === 'uploading' || status === 'processing'
  const displayEquipment = processedEquipment.length > 0 ? processedEquipment : rawEquipment
  const isProcessed = processedEquipment.length > 0

  return (
    <div style={s.app}>
      {/* Header */}
      <header style={s.header}>
        <div style={s.logo}>
          <span style={{ fontSize: 28 }}>🏭</span>
          <div>
            <div style={s.logoText}>Equipment Maintenance Manager</div>
            <div style={s.logoSub}>Powered by Google Gemini</div>
          </div>
        </div>
        <AuthButton authStatus={authStatus} onAuthChange={refreshAuth} />
      </header>

      <main style={s.main}>
        {/* Upload Card */}
        <div style={s.card}>
          <div style={s.cardTitle}>Import Equipment Data</div>
          <FileUpload
            onXlsxUpload={handleXlsxUpload}
            onSheetsImport={handleSheetsImport}
            loading={isLoading}
            authStatus={authStatus}
          />
        </div>

        {/* Status + Alerts */}
        {(status !== 'idle' || errorMsg || successMsg) && (
          <div>
            {errorMsg && <div style={s.errorBox}>⚠ {errorMsg}</div>}
            {successMsg && <div style={s.successBox}>✓ {successMsg}</div>}
            {(status === 'uploading' || status === 'processing') && (
              <div style={s.statusRow}>
                <StatusBadge status={status} />
                {status === 'processing' && (
                  <span style={{ fontSize: 13, color: '#718096' }}>
                    Searching manuals and estimating maintenance dates…
                  </span>
                )}
              </div>
            )}
          </div>
        )}

        {/* Equipment Table */}
        {displayEquipment.length > 0 && (
          <div style={s.card}>
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 16 }}>
              <div style={s.cardTitle}>
                {isProcessed ? '✅ Maintenance Schedule' : '📋 Equipment Preview'}
              </div>
              {isProcessed && <StatusBadge status="done" />}
            </div>

            <EquipmentTable
              equipment={displayEquipment}
              isProcessed={isProcessed}
              authStatus={authStatus}
              onAddToCalendar={handleAddToCalendar}
              addingIds={addingIds}
            />

            <ActionBar
              hasRawData={rawEquipment.length > 0}
              hasProcessed={isProcessed}
              loading={isLoading}
              authStatus={authStatus}
              equipmentCount={displayEquipment.length}
              onAnalyze={handleAnalyze}
              onExport={handleExport}
              onAddAll={handleAddAll}
              onReset={handleReset}
            />
          </div>
        )}

        {/* Empty state */}
        {displayEquipment.length === 0 && !isLoading && (
          <div style={{ ...s.card, textAlign: 'center', padding: '48px 24px', color: '#a0aec0' }}>
            <div style={{ fontSize: 48, marginBottom: 12 }}>📂</div>
            <div style={{ fontSize: 16, fontWeight: 600, marginBottom: 8 }}>No equipment loaded</div>
            <div style={{ fontSize: 14 }}>Upload an .xlsx file or import from Google Sheets to get started</div>
          </div>
        )}
      </main>
    </div>
  )
}

import React from 'react'

const s = {
  wrapper: { overflowX: 'auto', borderRadius: 10, border: '1px solid #e2e8f0' },
  table: { width: '100%', borderCollapse: 'collapse', fontSize: 13, background: '#fff' },
  th: {
    padding: '10px 14px', background: '#1F4E79', color: '#fff',
    fontWeight: 600, textAlign: 'left', whiteSpace: 'nowrap', fontSize: 12,
  },
  td: { padding: '10px 14px', borderBottom: '1px solid #e2e8f0', verticalAlign: 'top' },
  tdAlt: { padding: '10px 14px', borderBottom: '1px solid #e2e8f0', background: '#f7fafc', verticalAlign: 'top' },
  calBtn: {
    padding: '5px 12px', borderRadius: 6, border: 'none', cursor: 'pointer',
    background: '#0B8043', color: '#fff', fontSize: 12, fontWeight: 600,
    fontFamily: 'Inter, sans-serif', whiteSpace: 'nowrap',
  },
  addedBadge: {
    padding: '4px 10px', borderRadius: 6, background: '#c6f6d5',
    color: '#276749', fontSize: 12, fontWeight: 600,
  },
  noDate: { color: '#a0aec0', fontStyle: 'italic' },
  source: { color: '#4299e1', textDecoration: 'none', fontSize: 12 },
  reasoning: { color: '#718096', fontSize: 12, maxWidth: 300 },
  highlight: { color: '#c05621', fontWeight: 700 },
}

function formatDate(d) {
  if (!d) return null
  const date = new Date(d + 'T00:00:00')
  return date.toLocaleDateString('en-US', { year: 'numeric', month: 'short', day: 'numeric' })
}

function isOverdue(dateStr) {
  if (!dateStr) return false
  return new Date(dateStr) < new Date()
}

export default function EquipmentTable({ equipment, isProcessed, authStatus, onAddToCalendar, addingIds }) {
  if (!equipment || equipment.length === 0) return null

  const RAW_COLS = ['equipment_type', 'brand', 'model', 'installation_date', 'last_maintenance_date']
  const PROCESSED_COLS = [
    ...RAW_COLS,
    'next_maintenance_date',
    'maintenance_interval_months',
    'manual_source',
    'gemini_reasoning',
    'actions',
  ]

  const headers = {
    equipment_type: 'Type',
    brand: 'Brand',
    model: 'Model',
    installation_date: 'Installed',
    last_maintenance_date: 'Last Maintenance',
    next_maintenance_date: 'Next Maintenance',
    maintenance_interval_months: 'Interval',
    manual_source: 'Manual Source',
    gemini_reasoning: 'Notes',
    actions: 'Calendar',
  }

  const cols = isProcessed ? PROCESSED_COLS : RAW_COLS

  return (
    <div style={s.wrapper}>
      <table style={s.table}>
        <thead>
          <tr>
            {cols.map(col => (
              <th key={col} style={s.th}>{headers[col]}</th>
            ))}
          </tr>
        </thead>
        <tbody>
          {equipment.map((item, idx) => {
            const tdStyle = idx % 2 === 0 ? s.td : s.tdAlt
            const overdue = isOverdue(item.next_maintenance_date)
            const isAdded = !!item.calendar_event_id
            const isAdding = addingIds?.has(item.id)

            return (
              <tr key={item.id}>
                {cols.map(col => {
                  if (col === 'actions') {
                    return (
                      <td key={col} style={tdStyle}>
                        {isAdded ? (
                          <span style={s.addedBadge}>✓ Added</span>
                        ) : (
                          <button
                            style={{
                              ...s.calBtn,
                              opacity: (!authStatus?.authenticated || isAdding || !item.next_maintenance_date) ? 0.5 : 1,
                            }}
                            onClick={() => onAddToCalendar(item)}
                            disabled={!authStatus?.authenticated || isAdding || !item.next_maintenance_date}
                            title={!authStatus?.authenticated ? 'Connect Google account first' : ''}
                          >
                            {isAdding ? '...' : '📅 Add'}
                          </button>
                        )}
                      </td>
                    )
                  }

                  if (col === 'next_maintenance_date') {
                    const formatted = formatDate(item[col])
                    return (
                      <td key={col} style={tdStyle}>
                        {formatted ? (
                          <span style={overdue ? s.highlight : {}}>
                            {formatted}{overdue ? ' ⚠ Overdue' : ''}
                          </span>
                        ) : (
                          <span style={s.noDate}>—</span>
                        )}
                      </td>
                    )
                  }

                  if (col === 'installation_date' || col === 'last_maintenance_date') {
                    return (
                      <td key={col} style={tdStyle}>
                        {formatDate(item[col]) || <span style={s.noDate}>—</span>}
                      </td>
                    )
                  }

                  if (col === 'maintenance_interval_months') {
                    return (
                      <td key={col} style={tdStyle}>
                        {item[col] != null ? `${item[col]} mo` : <span style={s.noDate}>—</span>}
                      </td>
                    )
                  }

                  if (col === 'manual_source') {
                    const src = item[col]
                    if (!src) return <td key={col} style={tdStyle}><span style={s.noDate}>—</span></td>
                    const isUrl = src.startsWith('http')
                    return (
                      <td key={col} style={tdStyle}>
                        {isUrl ? (
                          <a href={src} target="_blank" rel="noreferrer" style={s.source}>
                            View manual ↗
                          </a>
                        ) : (
                          <span style={s.source}>{src}</span>
                        )}
                      </td>
                    )
                  }

                  if (col === 'gemini_reasoning') {
                    return (
                      <td key={col} style={tdStyle}>
                        <span style={s.reasoning}>{item[col] || '—'}</span>
                      </td>
                    )
                  }

                  return (
                    <td key={col} style={tdStyle}>
                      {item[col] || <span style={s.noDate}>—</span>}
                    </td>
                  )
                })}
              </tr>
            )
          })}
        </tbody>
      </table>
    </div>
  )
}

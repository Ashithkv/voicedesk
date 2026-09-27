import { useState } from 'react'
import IntentTag from './IntentTag.jsx'

function formatTime(iso) {
  const d = new Date(iso)
  return d.toLocaleString(undefined, {
    month: 'short',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
  })
}

export default function CallsTable({ calls }) {
  const [openId, setOpenId] = useState(null)

  if (calls.length === 0) {
    return (
      <div className="empty-state">
        No calls logged yet. Once your VAPI assistant sends a webhook
        event to <code>/webhook/vapi</code>, it'll show up here.
      </div>
    )
  }

  return (
    <div className="calls-table">
      <div className="calls-row calls-head">
        <span>Time</span>
        <span>Call ID</span>
        <span>Phone</span>
        <span>Intent</span>
        <span></span>
      </div>
      {calls.map((c) => (
        <div key={c.id} className="calls-group">
          <button
            className="calls-row calls-row-clickable"
            onClick={() => setOpenId(openId === c.id ? null : c.id)}
          >
            <span className="mono dim">{formatTime(c.created_at)}</span>
            <span className="mono">{c.call_id}</span>
            <span className="mono dim">{c.phone || '—'}</span>
            <span><IntentTag intent={c.intent} /></span>
            <span className="chevron">{openId === c.id ? '−' : '+'}</span>
          </button>
          {openId === c.id && (
            <div className="transcript-panel">
              <div className="transcript-block">
                <span className="transcript-label">Caller said</span>
                <p>{c.transcript || '—'}</p>
              </div>
              <div className="transcript-block">
                <span className="transcript-label">Assistant replied</span>
                <p>{c.assistant_response || '—'}</p>
              </div>
            </div>
          )}
        </div>
      ))}
    </div>
  )
}

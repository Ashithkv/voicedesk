function formatDate(iso) {
  const d = new Date(iso)
  return d.toLocaleDateString(undefined, { month: 'short', day: 'numeric' })
}

export function AppointmentsList({ appointments }) {
  if (appointments.length === 0) {
    return <div className="empty-state small">No appointment requests yet.</div>
  }
  return (
    <ul className="request-list">
      {appointments.map((a) => (
        <li key={a.id} className="request-item">
          <div className="request-main">
            <span className="request-name">{a.name}</span>
            <span className="request-meta">{a.date} · {a.time}</span>
          </div>
          <span className="request-phone mono dim">{a.phone || '—'}</span>
        </li>
      ))}
    </ul>
  )
}

export function CallbacksList({ callbacks }) {
  if (callbacks.length === 0) {
    return <div className="empty-state small">No callback requests yet.</div>
  }
  return (
    <ul className="request-list">
      {callbacks.map((c) => (
        <li key={c.id} className="request-item">
          <div className="request-main">
            <span className="request-name">{c.name}</span>
            <span className="request-meta">requested {formatDate(c.created_at)}</span>
          </div>
          <span className="request-phone mono dim">{c.phone}</span>
        </li>
      ))}
    </ul>
  )
}

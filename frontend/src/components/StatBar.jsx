export default function StatBar({ calls, appointments, callbacks }) {
  const intentCounts = calls.reduce((acc, c) => {
    const key = c.intent || 'unlogged'
    acc[key] = (acc[key] || 0) + 1
    return acc
  }, {})

  const stats = [
    { label: 'Total calls', value: calls.length },
    { label: 'Appointments booked', value: appointments.length },
    { label: 'Callback requests', value: callbacks.length },
    { label: 'General info answered', value: intentCounts.general_information || 0 },
  ]

  return (
    <div className="stat-bar">
      {stats.map((s) => (
        <div className="stat-cell" key={s.label}>
          <span className="stat-value">{s.value}</span>
          <span className="stat-label">{s.label}</span>
        </div>
      ))}
    </div>
  )
}

import { useEffect, useState, useCallback } from 'react'
import { api } from '../services/api.js'
import StatBar from '../components/StatBar.jsx'
import CallsTable from '../components/CallsTable.jsx'
import { AppointmentsList, CallbacksList } from '../components/RequestsPanel.jsx'

export default function Dashboard() {
  const [calls, setCalls] = useState([])
  const [appointments, setAppointments] = useState([])
  const [callbacks, setCallbacks] = useState([])
  const [error, setError] = useState(null)
  const [loading, setLoading] = useState(true)

  const load = useCallback(async () => {
    try {
      const [c, a, cb] = await Promise.all([
        api.getCalls(),
        api.getAppointments(),
        api.getCallbacks(),
      ])
      setCalls(c)
      setAppointments(a)
      setCallbacks(cb)
      setError(null)
    } catch (e) {
      setError('Could not reach the VoiceDesk API. Is the backend running on port 8000?')
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    load()
    const interval = setInterval(load, 8000)
    return () => clearInterval(interval)
  }, [load])

  return (
    <div className="page">
      <header className="page-header">
        <div className="brand">
          <span className="brand-mark" aria-hidden="true">
            <span className="pulse-bar" />
            <span className="pulse-bar" />
            <span className="pulse-bar" />
          </span>
          <div>
            <h1>VoiceDesk</h1>
            <p>Live console for the phone assistant</p>
          </div>
        </div>
        <button className="refresh-btn" onClick={load}>
          {loading ? 'Loading…' : 'Refresh'}
        </button>
      </header>

      {error && <div className="error-banner">{error}</div>}

      <StatBar calls={calls} appointments={appointments} callbacks={callbacks} />

      <div className="main-grid">
        <section className="panel panel-wide">
          <h2>Recent calls</h2>
          <CallsTable calls={calls} />
        </section>

        <div className="side-column">
          <section className="panel">
            <h2>Appointment requests</h2>
            <AppointmentsList appointments={appointments} />
          </section>

          <section className="panel">
            <h2>Callback requests</h2>
            <CallbacksList callbacks={callbacks} />
          </section>
        </div>
      </div>
    </div>
  )
}

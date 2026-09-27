const BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000'

async function request(path) {
  const res = await fetch(`${BASE_URL}${path}`)
  if (!res.ok) {
    throw new Error(`Request to ${path} failed: ${res.status}`)
  }
  return res.json()
}

export const api = {
  getCalls: () => request('/calls'),
  getAppointments: () => request('/appointments'),
  getCallbacks: () => request('/callbacks'),
}

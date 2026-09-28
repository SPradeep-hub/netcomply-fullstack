const configuredApiUrl = import.meta.env.VITE_API_URL?.trim()
const defaultApiUrl = import.meta.env.DEV
  ? 'http://127.0.0.1:5000'
  : 'https://netcomply-fullstack-2.onrender.com'
const apiOrigin = (configuredApiUrl || defaultApiUrl).replace(/\/+$/, '')
const BASE = apiOrigin.endsWith('/api') ? apiOrigin : `${apiOrigin}/api`

async function req(path, opts) {
  const res = await fetch(BASE + path, opts)
  if (!res.ok) {
    const body = await res.json().catch(() => ({}))
    throw new Error(body.error || `Request failed: ${res.status}`)
  }
  return res.json()
}

export const api = {
  listSamples: () => req('/samples'),
  dashboard: () => req('/dashboard'),
  analyze: (payload) =>
    req('/analyze', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload),
    }),
  getDevice: (id) => req(`/devices/${id}`),
  pdfUrl: (id) => `${BASE}/devices/${id}/pdf`,
  pendingTraining: () => req('/training/pending'),
  confirmMapping: (payload) =>
    req('/training/confirm', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload),
    }),
}

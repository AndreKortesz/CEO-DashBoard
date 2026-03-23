/**
 * API client for CEO Dashboard backend.
 * Handles all fetch calls with error handling + auth token.
 */

const API_BASE = import.meta.env.VITE_API_URL || '/api'
const API_TOKEN = import.meta.env.VITE_API_TOKEN || ''

async function fetchAPI(endpoint, options = {}) {
  const url = `${API_BASE}${endpoint}`
  const headers = { 'Content-Type': 'application/json', ...options.headers }
  if (API_TOKEN) {
    headers['Authorization'] = `Bearer ${API_TOKEN}`
  }
  try {
    const res = await fetch(url, { headers, ...options })
    if (!res.ok) {
      throw new Error(`API ${res.status}: ${res.statusText}`)
    }
    return await res.json()
  } catch (err) {
    console.error(`API Error [${endpoint}]:`, err)
    return null
  }
}

// --- Pulse ---
export const getPulse = () => fetchAPI('/pulse')

// --- Funnel ---
export const getMarketing = (period = 'month') => fetchAPI(`/funnel/marketing?period=${period}`)
export const getSales = () => fetchAPI('/funnel/sales')
export const getConversions = (groupBy, days = 30) => {
  const params = new URLSearchParams({ days })
  if (groupBy) params.set('group_by', groupBy)
  return fetchAPI(`/funnel/conversions?${params}`)
}

// --- People ---
export const getManagers = () => fetchAPI('/people/managers')
export const getManagerDetail = (name) => fetchAPI(`/people/managers/${encodeURIComponent(name)}`)
export const getInstallers = () => fetchAPI('/people/installers')

// --- Admin ---
export const getSalesPlans = (year) => fetchAPI(`/admin/sales-plan${year ? `?year=${year}` : ''}`)
export const setSalesPlan = (data) => fetchAPI('/admin/sales-plan', {
  method: 'POST',
  body: JSON.stringify(data),
})

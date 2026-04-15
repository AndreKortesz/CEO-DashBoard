/**
 * API client for CEO Dashboard backend.
 * Handles all fetch calls with error handling + auth token.
 * All data endpoints accept optional { from, to } date range.
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

function dateParams(range) {
  if (!range) return ''
  return `&date_from=${range.from}&date_to=${range.to}`
}

// --- Pulse ---
export const getPulse = (range) =>
  fetchAPI(`/pulse?_=1${dateParams(range)}`)

// --- Funnel ---
export const getMarketing = (range) =>
  fetchAPI(`/funnel/marketing?_=1${dateParams(range)}`)

export const getSales = (range) =>
  fetchAPI(`/funnel/sales?_=1${dateParams(range)}`)

export const getConversions = (groupBy, range) => {
  const params = new URLSearchParams()
  if (groupBy) params.set('group_by', groupBy)
  if (range) {
    params.set('date_from', range.from)
    params.set('date_to', range.to)
  }
  return fetchAPI(`/funnel/conversions?${params}`)
}

// --- People ---
export const getManagers = (range) =>
  fetchAPI(`/people/managers?_=1${dateParams(range)}`)

export const getManagerDetail = (name, range) =>
  fetchAPI(`/people/managers/${encodeURIComponent(name)}?_=1${dateParams(range)}`)

export const getInstallers = (range) =>
  fetchAPI(`/people/installers?_=1${dateParams(range)}`)

// --- Admin ---
export const getSalesPlans = (year) => fetchAPI(`/admin/sales-plan${year ? `?year=${year}` : ''}`)
export const setSalesPlan = (data) => fetchAPI('/admin/sales-plan', {
  method: 'POST',
  body: JSON.stringify(data),
})

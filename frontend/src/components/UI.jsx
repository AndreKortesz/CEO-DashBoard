import React from 'react'
import { useNavigate, useLocation } from 'react-router-dom'
import {
  Activity, TrendingUp, Users, Wallet, Radar,
} from 'lucide-react'

// ─── Metric card ────────────────────────────
export function MetricCard({ label, value, sub, trend }) {
  const trendColor = trend === 'up' ? 'text-emerald-600'
    : trend === 'down' ? 'text-red-600'
    : 'text-gray-500'

  return (
    <div className="bg-gray-50 rounded-lg p-4">
      <div className="text-xs text-gray-500 mb-1">{label}</div>
      <div className="text-xl font-medium text-gray-900">{value}</div>
      {sub && <div className={`text-xs mt-1 ${trendColor}`}>{sub}</div>}
    </div>
  )
}

// ─── Status badge ───────────────────────────
export function Badge({ children, variant = 'default' }) {
  const styles = {
    danger: 'bg-red-50 text-red-700',
    warning: 'bg-amber-50 text-amber-700',
    success: 'bg-emerald-50 text-emerald-700',
    info: 'bg-blue-50 text-blue-700',
    default: 'bg-gray-100 text-gray-600',
  }
  return (
    <span className={`text-xs font-medium px-2 py-0.5 rounded ${styles[variant] || styles.default}`}>
      {children}
    </span>
  )
}

// ─── Horizontal bar ─────────────────────────
export function HBar({ label, value, max, color = '#3266ad', displayValue }) {
  const pct = max > 0 ? Math.min((value / max) * 100, 100) : 0
  return (
    <div className="flex items-center gap-2 mb-1.5">
      <span className="text-xs text-gray-500 w-24 text-right shrink-0">{label}</span>
      <div className="flex-1 h-1.5 bg-gray-200 rounded-full overflow-hidden">
        <div
          className="h-full rounded-full transition-all duration-500"
          style={{ width: `${pct}%`, background: color }}
        />
      </div>
      <span className="text-xs text-gray-500 w-12 shrink-0">{displayValue ?? value}</span>
    </div>
  )
}

// ─── Red flag row ───────────────────────────
export function RedFlag({ text, count, variant = 'danger', onClick }) {
  const bg = variant === 'danger' ? 'bg-red-50' : 'bg-amber-50'
  const txt = variant === 'danger' ? 'text-red-700' : 'text-amber-700'
  const dot = variant === 'danger' ? 'bg-red-500' : 'bg-amber-500'

  return (
    <div
      className={`flex items-center gap-2.5 px-3.5 py-2.5 rounded-lg text-sm cursor-pointer hover:brightness-95 transition ${bg} ${txt}`}
      onClick={onClick}
    >
      <span className={`w-2 h-2 rounded-full shrink-0 ${dot}`} />
      <span className="flex-1">{text}</span>
      {count != null && <span className="font-medium text-sm">{count}</span>}
    </div>
  )
}

// ─── Section label ──────────────────────────
export function SectionLabel({ children }) {
  return (
    <div className="text-xs font-medium text-gray-500 uppercase tracking-wide mb-2.5">
      {children}
    </div>
  )
}

// ─── Navigation bar ─────────────────────────
const NAV_ITEMS = [
  { path: '/', label: 'Пульс', icon: Activity },
  { path: '/funnel', label: 'Воронка', icon: TrendingUp },
  { path: '/people', label: 'Люди', icon: Users },
  { path: '/money', label: 'Деньги', icon: Wallet },
  { path: '/radar', label: 'Радар', icon: Radar },
]

export function NavBar() {
  const navigate = useNavigate()
  const location = useLocation()

  return (
    <nav className="flex gap-1.5 mt-6 pb-4">
      {NAV_ITEMS.map(({ path, label, icon: Icon }) => {
        const active = location.pathname === path
        return (
          <button
            key={path}
            onClick={() => navigate(path)}
            className={`flex items-center gap-1.5 px-3.5 py-2 rounded-lg text-sm font-medium transition-all
              ${active
                ? 'bg-gray-900 text-white'
                : 'bg-transparent text-gray-500 border border-gray-300 hover:bg-gray-100'
              }`}
          >
            <Icon size={14} />
            {label}
          </button>
        )
      })}
    </nav>
  )
}

// ─── Loading skeleton ───────────────────────
export function Skeleton({ className = '' }) {
  return (
    <div className={`animate-pulse bg-gray-200 rounded ${className}`} />
  )
}

// ─── Page wrapper ───────────────────────────
export function PageWrapper({ title, children }) {
  return (
    <div className="max-w-4xl mx-auto px-4 py-6">
      <h1 className="text-xl font-medium text-gray-900 mb-5">{title}</h1>
      {children}
      <NavBar />
    </div>
  )
}

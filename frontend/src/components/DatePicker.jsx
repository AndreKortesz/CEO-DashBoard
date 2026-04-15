import React, { useState, useRef, useEffect } from 'react'

const PRESETS = [
  { key: 'today', label: 'Сегодня' },
  { key: 'yesterday', label: 'Вчера' },
  { key: 'week', label: 'Неделя' },
  { key: 'month', label: 'Месяц' },
  { key: 'quarter', label: 'Квартал' },
  { key: 'year', label: 'Год' },
]

function getPresetDates(key) {
  const today = new Date()
  const yyyy = today.getFullYear()
  const mm = today.getMonth()
  const dd = today.getDate()

  switch (key) {
    case 'today':
      return { from: fmtDate(today), to: fmtDate(today) }
    case 'yesterday': {
      const y = new Date(yyyy, mm, dd - 1)
      return { from: fmtDate(y), to: fmtDate(y) }
    }
    case 'week': {
      const w = new Date(yyyy, mm, dd - 6)
      return { from: fmtDate(w), to: fmtDate(today) }
    }
    case 'month':
      return { from: `${yyyy}-${pad(mm + 1)}-01`, to: fmtDate(today) }
    case 'quarter': {
      const qm = mm - (mm % 3)
      return { from: `${yyyy}-${pad(qm + 1)}-01`, to: fmtDate(today) }
    }
    case 'year':
      return { from: `${yyyy}-01-01`, to: fmtDate(today) }
    default:
      return { from: `${yyyy}-${pad(mm + 1)}-01`, to: fmtDate(today) }
  }
}

function fmtDate(d) {
  return `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())}`
}

function pad(n) {
  return n < 10 ? `0${n}` : `${n}`
}

function formatDisplayDate(dateStr) {
  if (!dateStr) return ''
  const d = new Date(dateStr + 'T00:00:00')
  return d.toLocaleDateString('ru-RU', { day: 'numeric', month: 'short' })
}

export function useDateRange() {
  const [preset, setPreset] = useState('month')
  const [range, setRange] = useState(() => getPresetDates('month'))

  const selectPreset = (key) => {
    setPreset(key)
    setRange(getPresetDates(key))
  }

  const setCustomRange = (from, to) => {
    setPreset(null)
    setRange({ from, to })
  }

  const label = preset
    ? PRESETS.find(p => p.key === preset)?.label || ''
    : `${formatDisplayDate(range.from)} — ${formatDisplayDate(range.to)}`

  return { preset, range, selectPreset, setCustomRange, label }
}

export default function DatePicker({ preset, range, onPreset, onCustomRange }) {
  const [open, setOpen] = useState(false)
  const [customFrom, setCustomFrom] = useState(range.from)
  const [customTo, setCustomTo] = useState(range.to)
  const ref = useRef(null)

  useEffect(() => {
    const handler = (e) => {
      if (ref.current && !ref.current.contains(e.target)) setOpen(false)
    }
    document.addEventListener('mousedown', handler)
    return () => document.removeEventListener('mousedown', handler)
  }, [])

  useEffect(() => {
    setCustomFrom(range.from)
    setCustomTo(range.to)
  }, [range])

  const activeLabel = preset
    ? PRESETS.find(p => p.key === preset)?.label
    : `${formatDisplayDate(range.from)} — ${formatDisplayDate(range.to)}`

  return (
    <div className="relative" ref={ref}>
      <button
        onClick={() => setOpen(!open)}
        className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-sm border border-gray-300 hover:bg-gray-50 transition text-gray-700"
      >
        <svg width="14" height="14" viewBox="0 0 16 16" fill="none" stroke="currentColor" strokeWidth="1.3">
          <rect x="2" y="3" width="12" height="11" rx="2" />
          <path d="M2 7h12M5 1v4M11 1v4" strokeLinecap="round" />
        </svg>
        {activeLabel}
        <svg width="10" height="10" viewBox="0 0 10 10" fill="none" stroke="currentColor" strokeWidth="1.5">
          <path d="M2 4l3 3 3-3" strokeLinecap="round" strokeLinejoin="round" />
        </svg>
      </button>

      {open && (
        <div className="absolute right-0 top-full mt-1 bg-white border border-gray-200 rounded-xl shadow-lg z-50 p-3 min-w-[280px]">
          <div className="text-xs text-gray-500 font-medium mb-2">Быстрый выбор</div>
          <div className="flex flex-wrap gap-1.5 mb-3">
            {PRESETS.map(p => (
              <button
                key={p.key}
                onClick={() => { onPreset(p.key); setOpen(false) }}
                className={`px-2.5 py-1 rounded-md text-xs font-medium transition
                  ${preset === p.key
                    ? 'bg-gray-900 text-white'
                    : 'bg-gray-100 text-gray-600 hover:bg-gray-200'}`}
              >
                {p.label}
              </button>
            ))}
          </div>

          <div className="border-t border-gray-100 pt-3">
            <div className="text-xs text-gray-500 font-medium mb-2">Произвольный период</div>
            <div className="flex items-center gap-2">
              <input
                type="date"
                value={customFrom}
                onChange={e => setCustomFrom(e.target.value)}
                className="flex-1 text-xs border border-gray-300 rounded-md px-2 py-1.5 text-gray-700"
              />
              <span className="text-gray-400 text-xs">—</span>
              <input
                type="date"
                value={customTo}
                onChange={e => setCustomTo(e.target.value)}
                className="flex-1 text-xs border border-gray-300 rounded-md px-2 py-1.5 text-gray-700"
              />
            </div>
            <button
              onClick={() => {
                if (customFrom && customTo) {
                  onCustomRange(customFrom, customTo)
                  setOpen(false)
                }
              }}
              className="mt-2 w-full text-xs bg-gray-900 text-white rounded-md py-1.5 font-medium hover:bg-gray-800 transition"
            >
              Применить
            </button>
          </div>
        </div>
      )}
    </div>
  )
}

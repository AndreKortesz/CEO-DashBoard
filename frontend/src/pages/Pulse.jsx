import React, { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { getPulse } from '../api'
import {
  PageWrapper, MetricCard, RedFlag, SectionLabel, HBar, Skeleton,
} from '../components/UI'

export default function Pulse() {
  const [data, setData] = useState(null)
  const [loading, setLoading] = useState(true)
  const navigate = useNavigate()

  useEffect(() => {
    getPulse().then(d => { setData(d); setLoading(false) })
  }, [])

  const today = new Date().toLocaleDateString('ru-RU', {
    weekday: 'long', day: 'numeric', month: 'long', year: 'numeric',
  })

  if (loading) {
    return (
      <PageWrapper title="Mos-GSM — утренний пульс">
        <div className="grid grid-cols-4 gap-3 mb-6">
          {Array(8).fill(0).map((_, i) => <Skeleton key={i} className="h-20" />)}
        </div>
      </PageWrapper>
    )
  }

  const m = data?.metrics || {}
  const rf = data?.red_flags || {}
  const pf = data?.plan_fact || {}

  return (
    <PageWrapper title="Mos-GSM — утренний пульс">
      <div className="text-xs text-gray-500 -mt-3 mb-5 capitalize">{today}</div>

      {/* AI Summary */}
      <div className="bg-gray-50 border-l-[3px] border-blue-500 rounded-r-lg p-4 mb-6 text-sm leading-relaxed text-gray-800">
        <div className="text-xs text-blue-600 font-medium mb-1.5 flex items-center gap-1.5">
          <svg width="14" height="14" viewBox="0 0 16 16" fill="none">
            <circle cx="8" cy="8" r="7" stroke="currentColor" strokeWidth="1.2"/>
            <path d="M8 4v4.5l3 1.5" stroke="currentColor" strokeWidth="1.2" strokeLinecap="round"/>
          </svg>
          AI-саммари
        </div>
        Данные загружаются из Bitrix24 и Roistat. Подключите источники данных для получения AI-аналитики.
      </div>

      {/* Key metrics */}
      <SectionLabel>Ключевые метрики вчера</SectionLabel>
      <div className="grid grid-cols-4 gap-3 mb-6">
        <MetricCard label="Выручка вчера" value={formatMoney(m.revenue_yesterday)} />
        <MetricCard label="Новых лидов" value={m.leads_yesterday} />
        <MetricCard label="Закрыто сделок" value={m.closed_deals_yesterday} />
        <MetricCard label="Монтажей завершено" value={m.montages_yesterday} />
      </div>

      {/* Red flags */}
      <SectionLabel>Красные флаги</SectionLabel>
      <div className="flex flex-col gap-2 mb-6">
        {rf.stale_deals_7d > 0 && (
          <RedFlag
            text="Сделки без активности > 7 дней"
            count={rf.stale_deals_7d}
            variant="danger"
          />
        )}
        {rf.stuck_montages > 0 && (
          <RedFlag
            text="Монтаж завис (ловушка)"
            count={rf.stuck_montages}
            variant="warning"
          />
        )}
        {rf.stale_deals_7d === 0 && rf.stuck_montages === 0 && (
          <div className="text-sm text-emerald-600 bg-emerald-50 rounded-lg px-4 py-3">
            Всё чисто — красных флагов нет
          </div>
        )}
      </div>

      {/* Plan-fact */}
      <SectionLabel>План–факт (валовый доход)</SectionLabel>
      <div className="grid grid-cols-3 gap-3 mb-6">
        <MetricCard label="План" value={formatMoney(pf.plan)} />
        <MetricCard
          label="Факт"
          value={formatMoney(pf.fact)}
          sub={`${pf.percent}% от плана`}
          trend={pf.percent >= 80 ? 'up' : pf.percent >= 50 ? null : 'down'}
        />
        <MetricCard label="Дефицит" value={formatMoney(Math.max(0, (pf.plan || 0) - (pf.fact || 0)))} trend="down" />
      </div>
    </PageWrapper>
  )
}

function formatMoney(v) {
  if (!v && v !== 0) return '—'
  if (v >= 1000000) return `${(v / 1000000).toFixed(1)}М`
  if (v >= 1000) return `${Math.round(v / 1000)}К`
  return `${Math.round(v)}`
}

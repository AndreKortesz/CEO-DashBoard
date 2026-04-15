import React, { useState, useEffect } from 'react'
import { getMarketing, getSales, getConversions } from '../api'
import { useDates } from '../App'
import { PageWrapper, MetricCard, SectionLabel, Badge, HBar, Skeleton } from '../components/UI'

const TABS = ['Маркетинг', 'Продажи', 'По направлениям']

export default function Funnel() {
  const [tab, setTab] = useState(0)
  const [marketing, setMarketing] = useState(null)
  const [sales, setSales] = useState(null)
  const [convManager, setConvManager] = useState(null)
  const [convDirection, setConvDirection] = useState(null)
  const [loading, setLoading] = useState(true)
  const { range } = useDates()

  useEffect(() => {
    setLoading(true)
    Promise.all([
      getMarketing(range),
      getSales(range),
      getConversions('manager', range),
      getConversions('direction', range),
    ]).then(([m, s, cm, cd]) => {
      setMarketing(m)
      setSales(s)
      setConvManager(cm)
      setConvDirection(cd)
      setLoading(false)
    })
  }, [range.from, range.to])

  return (
    <PageWrapper title="Воронка">
      <div className="flex gap-1.5 mb-6">
        {TABS.map((t, i) => (
          <button
            key={t}
            onClick={() => setTab(i)}
            className={`px-3.5 py-1.5 rounded-lg text-sm font-medium transition
              ${i === tab ? 'bg-gray-900 text-white' : 'border border-gray-300 text-gray-500 hover:bg-gray-100'}`}
          >
            {t}
          </button>
        ))}
      </div>

      {loading ? (
        <div className="space-y-3">
          {Array(4).fill(0).map((_, i) => <Skeleton key={i} className="h-16" />)}
        </div>
      ) : (
        <>
          {tab === 0 && <MarketingTab data={marketing} />}
          {tab === 1 && <SalesTab sales={sales} convManager={convManager} />}
          {tab === 2 && <DirectionsTab data={convDirection} />}
        </>
      )}
    </PageWrapper>
  )
}

function MarketingTab({ data }) {
  if (!data) return <div className="text-sm text-gray-500">Нет данных. Подключите Roistat API.</div>
  const t = data.totals || {}
  return (
    <>
      <SectionLabel>Маркетинг — {data.period}</SectionLabel>
      <div className="grid grid-cols-4 gap-3 mb-6">
        <MetricCard label="Расход на рекламу" value={formatExact(t.cost)} sub="с НДС" />
        <MetricCard label="Лидов" value={t.leads} />
        <MetricCard label="CPL средний" value={`${Math.round(t.cpl)} р.`} />
        <MetricCard label="ROI маркетинга" value={t.roi != null ? `${t.roi}%` : '—'} trend={t.roi > 0 ? 'up' : 'down'} />
      </div>

      <div className="bg-white border border-gray-200 rounded-xl p-4 mb-4">
        <div className="text-sm font-medium text-gray-900 mb-3">Каналы привлечения</div>
        <div className="overflow-x-auto">
          <table className="w-full text-xs">
            <thead>
              <tr className="border-b border-gray-200">
                <th className="text-left py-1.5 px-2 text-gray-500 font-medium">Канал</th>
                <th className="text-right py-1.5 px-2 text-gray-500 font-medium">Визиты</th>
                <th className="text-right py-1.5 px-2 text-gray-500 font-medium">Лиды</th>
                <th className="text-right py-1.5 px-2 text-gray-500 font-medium">CPL</th>
                <th className="text-right py-1.5 px-2 text-gray-500 font-medium">ROI</th>
              </tr>
            </thead>
            <tbody>
              {(data.channels || []).map(ch => (
                <tr key={ch.name} className="border-b border-gray-100 last:border-0">
                  <td className="py-1.5 px-2 text-gray-900">{ch.name}</td>
                  <td className="text-right py-1.5 px-2">{ch.visits || '—'}</td>
                  <td className="text-right py-1.5 px-2">{ch.leads}</td>
                  <td className="text-right py-1.5 px-2">{ch.cpl ? `${Math.round(ch.cpl)} р.` : '—'}</td>
                  <td className="text-right py-1.5 px-2">
                    {ch.roi != null ? (
                      <Badge variant={ch.roi > 0 ? 'success' : 'danger'}>{ch.roi > 0 ? '+' : ''}{ch.roi}%</Badge>
                    ) : '—'}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </>
  )
}

function SalesTab({ sales, convManager }) {
  const rop = convManager?.rop
  return (
    <>
      <SectionLabel>Конверсия лид → осмотр → монтаж</SectionLabel>

      {/* ROP block */}
      {rop?.metrics && (
        <div className="bg-blue-50 border border-blue-200 rounded-xl p-4 mb-4">
          <div className="flex items-center gap-2 mb-2">
            <div className="text-sm font-medium text-gray-900">{rop.name}</div>
            <Badge variant="info">РОП</Badge>
          </div>
          <div className="text-xs text-gray-600 mb-3">
            Лиды, которые сейчас числятся на РОПе. Распределённые лиды учитываются в таблице менеджеров.
          </div>
          <div className="grid grid-cols-5 gap-3 text-center">
            <div>
              <div className="text-base font-medium text-gray-900">{rop.breakdown?.total ?? rop.metrics.leads}</div>
              <div className="text-xs text-gray-500">Всего лидов</div>
            </div>
            <div>
              <div className="text-base font-medium text-amber-600">{rop.breakdown?.in_work ?? '—'}</div>
              <div className="text-xs text-gray-500">В работе</div>
            </div>
            <div>
              <div className="text-base font-medium text-emerald-600">{rop.breakdown?.converted ?? '—'}</div>
              <div className="text-xs text-gray-500">Конвертировано</div>
            </div>
            <div>
              <div className="text-base font-medium text-red-600">{rop.breakdown?.rejected ?? '—'}</div>
              <div className="text-xs text-gray-500">Отказ</div>
            </div>
            <div>
              <div className="text-base font-medium text-gray-900">
                <Badge variant={rop.metrics.conv_lead_montage >= 5 ? 'success' : 'warning'}>
                  {rop.metrics.conv_lead_montage}%
                </Badge>
              </div>
              <div className="text-xs text-gray-500">Общая конв.</div>
            </div>
          </div>
        </div>
      )}

      {/* Managers table */}
      {convManager?.data && (
        <div className="bg-white border border-gray-200 rounded-xl p-4 mb-4">
          <div className="text-sm font-medium text-gray-900 mb-3">По менеджерам</div>
          <table className="w-full text-xs">
            <thead>
              <tr className="border-b border-gray-200">
                <th className="text-left py-1.5 px-2 text-gray-500 font-medium">Менеджер</th>
                <th className="text-right py-1.5 px-2 text-gray-500 font-medium">Лиды</th>
                <th className="text-right py-1.5 px-2 text-gray-500 font-medium">Лид→Осм.</th>
                <th className="text-right py-1.5 px-2 text-gray-500 font-medium">Осм.→Монт.</th>
                <th className="text-right py-1.5 px-2 text-gray-500 font-medium">Общая</th>
              </tr>
            </thead>
            <tbody>
              {Object.entries(convManager.data).map(([name, d]) => (
                <tr key={name} className="border-b border-gray-100 last:border-0">
                  <td className="py-1.5 px-2 text-gray-900">{name}</td>
                  <td className="text-right py-1.5 px-2">{d.leads}</td>
                  <td className="text-right py-1.5 px-2">
                    <Badge variant={d.conv_lead_inspection >= 38 ? 'success' : d.conv_lead_inspection >= 30 ? 'warning' : 'danger'}>
                      {d.conv_lead_inspection}%
                    </Badge>
                  </td>
                  <td className="text-right py-1.5 px-2">
                    <Badge variant={d.conv_inspection_montage >= 50 ? 'success' : d.conv_inspection_montage >= 40 ? 'warning' : 'danger'}>
                      {d.conv_inspection_montage}%
                    </Badge>
                  </td>
                  <td className="text-right py-1.5 px-2">
                    <Badge variant={d.conv_lead_montage >= 20 ? 'success' : d.conv_lead_montage >= 15 ? 'warning' : 'danger'}>
                      {d.conv_lead_montage}%
                    </Badge>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {/* Deal stages */}
      {sales?.stages && (
        <>
          <SectionLabel>Воронка сделок по стадиям</SectionLabel>
          <div className="grid grid-cols-3 gap-2 mb-4">
            {sales.stages.map(s => (
              <div key={s.stage} className="bg-gray-50 rounded-lg p-3 text-center">
                <div className="text-base font-medium text-gray-900">{s.count}</div>
                <div className="text-xs text-gray-500 mt-0.5">{s.stage}</div>
                <div className="text-xs text-gray-400 mt-0.5">{formatM(s.total)}</div>
              </div>
            ))}
          </div>
        </>
      )}
    </>
  )
}

function DirectionsTab({ data }) {
  if (!data?.data) return <div className="text-sm text-gray-500">Нет данных</div>
  return (
    <>
      <SectionLabel>Конверсии по направлениям</SectionLabel>
      <div className="bg-white border border-gray-200 rounded-xl p-4">
        <table className="w-full text-xs">
          <thead>
            <tr className="border-b border-gray-200">
              <th className="text-left py-1.5 px-2 text-gray-500 font-medium">Направление</th>
              <th className="text-right py-1.5 px-2 text-gray-500 font-medium">Лиды</th>
              <th className="text-right py-1.5 px-2 text-gray-500 font-medium">Осмотры</th>
              <th className="text-right py-1.5 px-2 text-gray-500 font-medium">Монтажи</th>
              <th className="text-right py-1.5 px-2 text-gray-500 font-medium">Общая</th>
            </tr>
          </thead>
          <tbody>
            {Object.entries(data.data).map(([name, d]) => (
              <tr key={name} className="border-b border-gray-100 last:border-0">
                <td className="py-1.5 px-2 text-gray-900">{name}</td>
                <td className="text-right py-1.5 px-2">{d.leads}</td>
                <td className="text-right py-1.5 px-2">{d.inspections}</td>
                <td className="text-right py-1.5 px-2">{d.montages}</td>
                <td className="text-right py-1.5 px-2">
                  <Badge variant={d.conv_lead_montage >= 20 ? 'success' : d.conv_lead_montage >= 15 ? 'warning' : 'danger'}>
                    {d.conv_lead_montage}%
                  </Badge>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </>
  )
}

function formatM(v) {
  if (!v) return '—'
  if (v >= 1000000) return `${(v / 1000000).toFixed(1)}М`
  if (v >= 1000) return `${Math.round(v / 1000)}К`
  return `${Math.round(v)}`
}

function formatExact(v) {
  if (!v && v !== 0) return '—'
  return `${Math.round(v).toLocaleString('ru-RU')} р.`
}

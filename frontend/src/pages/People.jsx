import React, { useState, useEffect } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { getManagers, getManagerDetail, getInstallers } from '../api'
import { PageWrapper, MetricCard, SectionLabel, Badge, HBar, RedFlag, Skeleton } from '../components/UI'

const TABS = ['Менеджеры', 'Монтажники']

export default function People() {
  const { managerName } = useParams()
  const [tab, setTab] = useState(0)

  if (managerName) return <ManagerDetail name={decodeURIComponent(managerName)} />

  return (
    <PageWrapper title="Люди">
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

      {tab === 0 ? <ManagersTab /> : <InstallersTab />}
    </PageWrapper>
  )
}

function ManagersTab() {
  const [data, setData] = useState(null)
  const navigate = useNavigate()

  useEffect(() => { getManagers().then(setData) }, [])

  if (!data) return <Skeleton className="h-40" />

  const dept = data.department_rechka
  return (
    <>
      {dept && (
        <div className="bg-gray-50 rounded-lg p-4 mb-4 text-sm">
          <span className="text-gray-500">Сводная оценка отдела (Речка AI):</span>
          <span className="font-medium text-gray-900 ml-2">{dept.score_total}%</span>
          <span className="text-gray-400 ml-2">неделя {dept.week}</span>
        </div>
      )}

      <SectionLabel>Менеджеры</SectionLabel>
      <div className="grid grid-cols-2 gap-3 mb-4">
        {(data.managers || []).map(m => (
          <div
            key={m.name}
            onClick={() => navigate(`/people/${encodeURIComponent(m.name)}`)}
            className="bg-white border border-gray-200 rounded-xl p-4 cursor-pointer hover:border-gray-400 transition"
          >
            <div className="flex items-center gap-3 mb-3">
              <div className="w-10 h-10 rounded-full bg-blue-50 text-blue-700 flex items-center justify-center text-sm font-medium">
                {m.name.split(' ').map(w => w[0]).join('')}
              </div>
              <div>
                <div className="text-sm font-medium text-gray-900">{m.name}</div>
                <div className="text-xs text-gray-500">Менеджер</div>
              </div>
            </div>
            <div className="grid grid-cols-3 gap-2 text-center">
              <div>
                <div className="text-base font-medium text-gray-900">{m.closed_deals}</div>
                <div className="text-xs text-gray-500">Сделок</div>
              </div>
              <div>
                <div className="text-base font-medium text-gray-900">{m.avg_response_minutes ?? '—'}</div>
                <div className="text-xs text-gray-500">мин. реакц.</div>
              </div>
              <div>
                <div className={`text-base font-medium ${
                  m.rechka?.score_total >= 40 ? 'text-emerald-600'
                    : m.rechka?.score_total >= 30 ? 'text-gray-900'
                    : 'text-red-600'
                }`}>
                  {m.rechka?.score_total != null ? `${m.rechka.score_total}%` : '—'}
                </div>
                <div className="text-xs text-gray-500">Речка</div>
              </div>
            </div>
          </div>
        ))}
      </div>
    </>
  )
}

function ManagerDetail({ name }) {
  const [data, setData] = useState(null)
  const navigate = useNavigate()

  useEffect(() => { getManagerDetail(name).then(setData) }, [name])

  if (!data) return (
    <PageWrapper title="Загрузка...">
      <Skeleton className="h-60" />
    </PageWrapper>
  )

  return (
    <PageWrapper title={data.name}>
      <button
        onClick={() => navigate('/people')}
        className="text-sm text-blue-600 mb-4 hover:underline"
      >
        ← Назад к Люди
      </button>

      {/* Rechka history */}
      {data.rechka_history?.length > 0 && (
        <>
          <SectionLabel>Речка AI — динамика по неделям</SectionLabel>
          <div className="flex gap-1 items-end h-24 mb-4">
            {data.rechka_history.map(w => (
              <div key={w.week} className="flex-1 flex flex-col items-center gap-1">
                <div
                  className="w-full rounded-t"
                  style={{
                    height: `${Math.max(w.score_total, 4)}%`,
                    background: w.score_total >= 40 ? '#059669' : w.score_total >= 30 ? '#d97706' : '#dc2626',
                  }}
                />
                <span className="text-[10px] text-gray-500">{w.week}</span>
              </div>
            ))}
          </div>
        </>
      )}

      {/* Active deals by stage */}
      {data.deals_by_stage?.length > 0 && (
        <>
          <SectionLabel>Воронка</SectionLabel>
          <div className="mb-4">
            {data.deals_by_stage.map(s => (
              <HBar
                key={s.stage}
                label={s.stage}
                value={s.count}
                max={Math.max(...data.deals_by_stage.map(x => x.count))}
                color="#3266ad"
              />
            ))}
          </div>
        </>
      )}

      {/* Stale deals */}
      {data.stale_deals?.length > 0 && (
        <>
          <SectionLabel>Сделки без активности</SectionLabel>
          <div className="space-y-2 mb-4">
            {data.stale_deals.map(d => (
              <div key={d.id} className="flex justify-between items-center bg-white border border-gray-200 rounded-lg p-3">
                <span className="text-sm text-gray-900 flex-1">{d.title}</span>
                <span className="text-sm font-medium text-gray-900 mx-3">
                  {d.amount >= 1000 ? `${Math.round(d.amount / 1000)}К` : d.amount}
                </span>
                <Badge variant={d.days_stale > 14 ? 'danger' : 'warning'}>
                  {d.days_stale} дн.
                </Badge>
              </div>
            ))}
          </div>
        </>
      )}
    </PageWrapper>
  )
}

function InstallersTab() {
  const [data, setData] = useState(null)

  useEffect(() => { getInstallers().then(setData) }, [])

  if (!data) return <Skeleton className="h-40" />

  return (
    <>
      <SectionLabel>Монтажники — загрузка на неделю</SectionLabel>
      <div className="grid grid-cols-3 gap-3">
        {(data.installers || []).map(inst => {
          const color = inst.workload_percent >= 60 ? '#059669'
            : inst.workload_percent >= 20 ? '#d97706'
            : '#dc2626'
          return (
            <div key={inst.name} className="bg-white border border-gray-200 rounded-xl p-3">
              <div className="text-sm font-medium text-gray-900 mb-2">{inst.name}</div>
              <div className="grid grid-cols-2 gap-1 text-center mb-2">
                <div>
                  <div className="text-base font-medium text-gray-900">{inst.montages_week}</div>
                  <div className="text-[10px] text-gray-500">Монтажей</div>
                </div>
                <div>
                  <div className="text-base font-medium text-gray-900">{inst.inspections_week}</div>
                  <div className="text-[10px] text-gray-500">Осмотров</div>
                </div>
              </div>
              <div className="h-1.5 bg-gray-200 rounded-full overflow-hidden">
                <div className="h-full rounded-full" style={{ width: `${inst.workload_percent}%`, background: color }} />
              </div>
              <div className="flex justify-between mt-1">
                <span className="text-[10px] text-gray-500">Загрузка</span>
                <span className="text-[10px] font-medium" style={{ color }}>{inst.workload_percent}%</span>
              </div>
            </div>
          )
        })}
      </div>
    </>
  )
}

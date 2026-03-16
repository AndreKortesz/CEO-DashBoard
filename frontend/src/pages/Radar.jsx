import React from 'react'
import { PageWrapper, SectionLabel } from '../components/UI'

export default function RadarPage() {
  return (
    <PageWrapper title="Радар">
      <div className="bg-gray-50 border border-gray-200 rounded-xl p-6 text-center">
        <div className="text-gray-400 text-4xl mb-3">📡</div>
        <div className="text-sm font-medium text-gray-900 mb-1">Фаза 5 — AI-аналитика + Прогнозы</div>
        <div className="text-sm text-gray-500">
          Этот экран будет доступен после подключения всех источников данных и Claude API.
        </div>
        <div className="mt-4 text-xs text-gray-400 space-y-1">
          <div>AI-саммари — ежедневная аналитика от Claude с рекомендациями</div>
          <div>Прогноз выручки — 14 / 30 / 90 дней на основе пайплайна</div>
          <div>Красные флаги — ранжированные риски с суммами потерь</div>
          <div>Тренды — сравнение с прошлой неделей по всем метрикам</div>
        </div>
      </div>
    </PageWrapper>
  )
}

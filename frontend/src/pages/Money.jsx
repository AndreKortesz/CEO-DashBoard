import React from 'react'
import { PageWrapper, SectionLabel } from '../components/UI'

export default function Money() {
  return (
    <PageWrapper title="Деньги">
      <div className="bg-gray-50 border border-gray-200 rounded-xl p-6 text-center">
        <div className="text-gray-400 text-4xl mb-3">💰</div>
        <div className="text-sm font-medium text-gray-900 mb-1">Фаза 4 — Adesk + 1С</div>
        <div className="text-sm text-gray-500">
          Этот экран будет доступен после подключения Adesk (вебхуки), 1С Бухгалтерии (дебиторка) и 1С УТ (закупки, маржинальность).
        </div>
        <div className="mt-4 text-xs text-gray-400 space-y-1">
          <div>ДДС — поступления, расходы по категориям, балансы счетов (ООО, ИП, наличные)</div>
          <div>Дебиторка — кто должен, сколько, просрочка</div>
          <div>Закупки — привязка к объектам, предоплата, замороженный капитал, дата окупаемости</div>
        </div>
      </div>
    </PageWrapper>
  )
}

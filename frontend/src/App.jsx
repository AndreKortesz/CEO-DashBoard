import React from 'react'
import { BrowserRouter, Routes, Route } from 'react-router-dom'
import Pulse from './pages/Pulse'
import Funnel from './pages/Funnel'
import People from './pages/People'
import Money from './pages/Money'
import RadarPage from './pages/Radar'

export default function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<Pulse />} />
        <Route path="/funnel" element={<Funnel />} />
        <Route path="/people" element={<People />} />
        <Route path="/people/:managerName" element={<People />} />
        <Route path="/money" element={<Money />} />
        <Route path="/radar" element={<RadarPage />} />
      </Routes>
    </BrowserRouter>
  )
}

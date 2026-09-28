import { useEffect, useState } from 'react'
import { Routes, Route } from 'react-router-dom'
import Nav from './components/Nav.jsx'
import Dashboard from './components/Dashboard.jsx'
import Upload from './components/Upload.jsx'
import Training from './components/Training.jsx'
import Report from './components/Report.jsx'
import { api } from './api'

export default function App() {
  const [pendingCount, setPendingCount] = useState(0)

  useEffect(() => {
    api.pendingTraining()
      .then((d) => setPendingCount(d.pending.length))
      .catch(() => {})
  }, [])

  return (
    <>
      <Nav pendingCount={pendingCount} />
      <main>
        <Routes>
          <Route path="/" element={<Dashboard />} />
          <Route path="/upload" element={<Upload />} />
          <Route path="/training" element={<Training />} />
          <Route path="/report/:deviceId" element={<Report />} />
        </Routes>
      </main>
    </>
  )
}

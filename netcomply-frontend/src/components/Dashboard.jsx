import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { api } from '../api'

export default function Dashboard() {
  const [stats, setStats] = useState(null)
  const [error, setError] = useState(null)

  useEffect(() => {
    api.dashboard().then(setStats).catch((e) => setError(e.message))
  }, [])

  if (error) return <div className="panel error">Could not reach the API: {error}</div>
  if (!stats) return <div className="empty">Loading…</div>

  const { total, compliant, severity, devices } = stats

  return (
    <div>
      <h1>Compliance Dashboard</h1>
      <div className="sub">Aggregate results across all scanned devices, all vendors, one baseline.</div>
      <div className="cards">
        <div className="card"><div className="n">{total}</div><div className="l">Devices Scanned</div></div>
        <div className="card"><div className="n" style={{ color: 'var(--pass)' }}>{compliant}</div><div className="l">Fully Compliant</div></div>
        <div className="card"><div className="n" style={{ color: 'var(--fail)' }}>{total - compliant}</div><div className="l">Non-Compliant</div></div>
        <div className="card"><div className="n" style={{ color: 'var(--high)' }}>{severity.HIGH}</div><div className="l">High Findings</div></div>
        <div className="card"><div className="n" style={{ color: 'var(--med)' }}>{severity.MEDIUM}</div><div className="l">Medium Findings</div></div>
        <div className="card"><div className="n" style={{ color: 'var(--low)' }}>{severity.LOW}</div><div className="l">Low Findings</div></div>
      </div>
      <div className="panel">
        <h2 style={{ marginTop: 0 }}>Scanned Devices</h2>
        {devices.length === 0 ? (
          <div className="empty">No devices scanned yet. Go to Upload &amp; Scan.</div>
        ) : (
          <table>
            <thead><tr><th>Device</th><th>Vendor</th><th>OS</th><th>Score</th><th>Status</th><th></th></tr></thead>
            <tbody>
              {devices.map((d) => (
                <tr key={d.id}>
                  <td>{d.hostname}</td>
                  <td style={{ textTransform: 'capitalize' }}>{d.vendor}</td>
                  <td>{d.os}</td>
                  <td>{d.score}%</td>
                  <td><span className={`badge ${d.score === 100 ? 'b-pass' : 'b-fail'}`}>{d.score === 100 ? 'COMPLIANT' : 'NON-COMPLIANT'}</span></td>
                  <td><Link to={`/report/${d.id}`} style={{ color: 'var(--accent2)' }}>View Report</Link></td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>
    </div>
  )
}

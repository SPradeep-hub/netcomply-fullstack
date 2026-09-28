import React, { useEffect, useState } from 'react'
import { useParams } from 'react-router-dom'
import { api } from '../api'

export default function Report() {
  const { deviceId } = useParams()
  const [device, setDevice] = useState(null)
  const [error, setError] = useState(null)

  useEffect(() => {
    setDevice(null)
    api.getDevice(deviceId).then(setDevice).catch((e) => setError(e.message))
  }, [deviceId])

  if (error) return <div className="panel error">Could not load report: {error}</div>
  if (!device) return <div className="empty">Loading…</div>

  const passCount = device.findings.filter((f) => f.passed).length

  return (
    <div>
      <h1>{device.hostname}</h1>
      <div className="sub">
        Vendor: <b style={{ textTransform: 'capitalize' }}>{device.vendor}</b> ·
        {' '}OS: {device.os} · Serial: {device.serial} · File: {device.filename}
      </div>

      <div className="panel">
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 16 }}>
          <div className="cards" style={{ marginBottom: 0 }}>
            <div className="card"><div className="n">{device.score}%</div><div className="l">Compliance Score</div></div>
            <div className="card"><div className="n" style={{ color: 'var(--pass)' }}>{passCount}</div><div className="l">Rules Passed</div></div>
            <div className="card"><div className="n" style={{ color: 'var(--fail)' }}>{device.findings.length - passCount}</div><div className="l">Rules Failed</div></div>
          </div>
          <a className="primary" style={{ textDecoration: 'none', padding: '9px 14px', borderRadius: 8 }}
             href={api.pdfUrl(device.id)} target="_blank" rel="noreferrer">
            ⬇ Download PDF Report
          </a>
        </div>

        <table>
          <thead><tr><th>Rule</th><th>Framework</th><th>Severity</th><th>Result</th></tr></thead>
          <tbody>
            {device.findings.map((f) => (
              <React.Fragment key={f.rule_id}>
                <tr>
                  <td>{f.title}</td>
                  <td>{f.framework}</td>
                  <td className={`sev-${f.severity}`}>{f.severity}</td>
                  <td><span className={`badge ${f.passed ? 'b-pass' : 'b-fail'}`}>{f.passed ? 'PASS' : 'FAIL'}</span></td>
                </tr>
                {!f.passed && (
                  <tr>
                    <td colSpan={4} style={{ paddingTop: 0 }}>
                      <div className="sub" style={{ margin: '0 0 4px' }}>{f.why}</div>
                      <div className="remediation">{f.remediation}</div>
                    </td>
                  </tr>
                )}
              </React.Fragment>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  )
}

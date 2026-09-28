import { useEffect, useState } from 'react'
import { api } from '../api'

export default function Training() {
  const [data, setData] = useState(null)
  const [error, setError] = useState(null)
  const [selections, setSelections] = useState({})
  const [saving, setSaving] = useState(null)

  async function load() {
    setError(null)
    try {
      setData(await api.pendingTraining())
    } catch (e) {
      setError(e.message)
      throw e
    }
  }

  useEffect(() => { load().catch(() => {}) }, [])

  if (error) return <div className="panel error">Could not reach the API: {error}</div>
  if (!data) return <div className="empty">Loading…</div>

  const { pending, categories, learned } = data

  function keyFor(item) {
    return `${item.device_id}::${item.line}`
  }

  async function confirm(item) {
    const field = selections[keyFor(item)]
    if (!field) return
    const category = categories.find((option) => option.field === field)
    const value = category?.value
    setSaving(keyFor(item))
    setError(null)
    try {
      await api.confirmMapping({
        device_id: item.device_id,
        line: item.line,
        field,
        value,
      })
      setSelections((current) => {
        const next = { ...current }
        delete next[keyFor(item)]
        return next
      })
      await load()
    } catch (e) {
      setError(e.message)
    } finally {
      setSaving(null)
    }
  }

  return (
    <div>
      <h1>AI Training Interface</h1>
      <div className="sub">
        NetComply flagged lines it couldn't classify against known vendor syntax.
        Confirm what each one means — the mapping is then learned and reused automatically next time.
      </div>
      {error && <div className="error" role="alert">{error}</div>}

      {pending.length === 0 ? (
        <div className="panel"><div className="empty">
          No unrecognized commands pending. Analyze the "unknown_vendor.txt" sample from Upload &amp; Scan to see this in action.
        </div></div>
      ) : (
        <div className="panel">
          <h2 style={{ marginTop: 0 }}>Unrecognized Command Lines ({pending.length})</h2>
          {pending.map((item) => {
            const k = keyFor(item)
            return (
              <div className="trainrow" key={k}>
                <code>{item.line}</code>
                {item.suggestion && (
                  <div className="sub" style={{ marginBottom: 8 }}>
                    AI suggests: <b style={{ color: 'var(--accent)' }}>{item.suggestion.category}</b>
                  </div>
                )}
                <div style={{ display: 'flex', gap: 10, flexWrap: 'wrap' }}>
                  <select
                    value={selections[k] || ''}
                    onChange={(e) => setSelections((current) => ({ ...current, [k]: e.target.value }))}
                  >
                    <option value="">— choose category —</option>
                    {categories.map((c) => (
                      <option key={c.field} value={c.field}>{c.label}</option>
                    ))}
                    <option value="ignore">Not security-relevant / ignore</option>
                  </select>
                  <button
                    className="primary"
                    disabled={!selections[k] || saving === k}
                    onClick={() => confirm(item)}
                  >
                    {saving === k ? 'Saving…' : 'Confirm & Learn'}
                  </button>
                </div>
              </div>
            )
          })}
        </div>
      )}

      <div className="panel">
        <h2 style={{ marginTop: 0 }}>Learned Mappings ({Object.keys(learned).length})</h2>
        {Object.keys(learned).length === 0 ? (
          <div className="empty">None yet.</div>
        ) : (
          <table>
            <thead><tr><th>Keyword</th><th>Category</th></tr></thead>
            <tbody>
              {Object.entries(learned).map(([kw, v]) => (
                <tr key={kw}><td><code>{kw}</code></td><td>{v.category}</td></tr>
              ))}
            </tbody>
          </table>
        )}
      </div>
    </div>
  )
}

import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { api } from '../api'

export default function Upload() {
  const [samples, setSamples] = useState([])
  const [text, setText] = useState('')
  const [filename, setFilename] = useState('pasted-config.txt')
  const [pendingSample, setPendingSample] = useState(null)
  const [error, setError] = useState(null)
  const [loading, setLoading] = useState(false)
  const navigate = useNavigate()

  useEffect(() => {
    api.listSamples().then(setSamples).catch(() => {})
  }, [])

  function pickSample(name) {
    setPendingSample(name)
    setFilename(name)
    setText(`# Sample selected: ${name}\n# Full contents are analyzed server-side on submit.`)
  }

  function onFileChange(e) {
    const file = e.target.files[0]
    if (!file) return
    setPendingSample(null)
    setFilename(file.name)
    const reader = new FileReader()
    reader.onload = () => setText(reader.result)
    reader.readAsText(file)
  }

  async function analyze() {
    if (!pendingSample && !text.trim()) return
    setLoading(true)
    setError(null)
    try {
      const payload = pendingSample ? { sample: pendingSample } : { config_text: text, filename }
      const device = await api.analyze(payload)
      navigate(`/report/${device.id}`)
    } catch (e) {
      setError(e.message)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div>
      <h1>Upload Configuration</h1>
      <div className="sub">
        Upload a config file, paste text, or try a sample from a different vendor —
        including one NetComply hasn't seen before.
      </div>
      <div className="panel">
        <h2 style={{ marginTop: 0 }}>1. Choose a source</h2>
        <div style={{ marginBottom: 10 }}>
          {samples.map((s) => (
            <span key={s} className="chip" onClick={() => pickSample(s)}>{s}</span>
          ))}
        </div>
        <input
          type="file"
          accept=".txt,.cfg,.conf,.log"
          onChange={onFileChange}
          style={{ marginBottom: 10, display: 'block' }}
        />
        <textarea
          value={text}
          onChange={(e) => { setText(e.target.value); setPendingSample(null) }}
          placeholder="...or paste raw device configuration here"
        />
        <div style={{ marginTop: 12, display: 'flex', gap: 10, alignItems: 'center' }}>
          <button className="primary" onClick={analyze} disabled={loading}>
            {loading ? 'Analyzing…' : 'Analyze Configuration'}
          </button>
        </div>
        {error && <div className="error">{error}</div>}
      </div>
    </div>
  )
}

import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import api from '../services/api'

export default function Disclaimer() {
  const navigate = useNavigate()
  const [disclaimer, setDisclaimer] = useState(null)
  const [agreed, setAgreed] = useState(false)

  useEffect(() => {
    api
      .get('/disclaimer')
      .then((r) => setDisclaimer(r.data))
      .catch(() => setDisclaimer(null))
  }, [])

  return (
    <div className="mx-auto max-w-2xl">
      <div className="card border-2 border-amber-300">
        <h1 className="text-2xl font-bold text-amber-900">⚠️ Medical Disclaimer</h1>
        {disclaimer && (
          <p className="mt-1 text-xs text-slate-400">
            Version {disclaimer.version} · updated {disclaimer.last_updated}
          </p>
        )}
        <div className="mt-4 whitespace-pre-line text-sm leading-relaxed text-slate-700">
          {disclaimer
            ? disclaimer.disclaimer_text
            : 'Loading disclaimer… If this message persists, the backend may be offline.'}
        </div>

        <label className="mt-6 flex items-start gap-2 text-sm font-semibold text-slate-700">
          <input type="checkbox" className="mt-0.5 h-5 w-5" checked={agreed} onChange={(e) => setAgreed(e.target.checked)} />
          <span>I acknowledge and agree: this tool is a screening aid, NOT a diagnosis.</span>
        </label>

        <div className="mt-5 flex flex-wrap gap-3">
          <button
            className="btn-primary"
            disabled={!agreed}
            onClick={() => (window.history.length > 1 ? navigate(-1) : navigate('/'))}
          >
            I Understand — Go Back
          </button>
        </div>
        <p className="mt-3 text-xs text-slate-400">
          Staff must acknowledge this disclaimer before registering or screening patients.
        </p>
      </div>
    </div>
  )
}

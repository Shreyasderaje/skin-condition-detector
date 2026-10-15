import { useEffect, useState } from 'react'
import { useNavigate, useParams } from 'react-router-dom'
import { toast } from 'react-toastify'
import ConfidenceChart from '../components/ConfidenceChart'
import DisclaimerBanner from '../components/DisclaimerBanner'
import RiskBadge from '../components/RiskBadge'
import api, { apiError, fetchImageBlobUrl } from '../services/api'

const REC_STYLES = {
  LOW: 'border-green-300 bg-green-50 text-green-900',
  MEDIUM: 'border-amber-300 bg-amber-50 text-amber-900',
  HIGH: 'border-red-300 bg-red-50 text-red-900',
}

export default function Results() {
  const { consultationId } = useParams()
  const navigate = useNavigate()
  const [data, setData] = useState(null)
  const [image, setImage] = useState(null)
  const [notes, setNotes] = useState('')
  const [savingNotes, setSavingNotes] = useState(false)
  const [downloading, setDownloading] = useState(false)

  useEffect(() => {
    api
      .get(`/consultations/${consultationId}`)
      .then((r) => {
        setData(r.data)
        setNotes(r.data.staff_notes || '')
      })
      .catch((e) => {
        toast.error(apiError(e))
        navigate('/history')
      })
    fetchImageBlobUrl(consultationId)
      .then(setImage)
      .catch(() => setImage(null))
  }, [consultationId, navigate])

  if (!data) {
    return <p className="mt-10 text-center text-slate-500">Loading results…</p>
  }

  const risk = data.risk_level

  const saveNotes = async () => {
    setSavingNotes(true)
    try {
      const r = await api.patch(`/consultations/${consultationId}/notes`, { staff_notes: notes })
      setData(r.data)
      toast.success('Staff notes saved')
    } catch (e) {
      toast.error(apiError(e))
    } finally {
      setSavingNotes(false)
    }
  }

  const setOutcome = async (outcome) => {
    try {
      const r = await api.patch(`/consultations/${consultationId}/outcome`, { outcome })
      setData(r.data)
      toast.success(`Follow-up outcome: ${outcome}`)
    } catch (e) {
      toast.error(apiError(e))
    }
  }

  const downloadReport = async () => {
    setDownloading(true)
    try {
      const { jsPDF } = await import('jspdf')
      const doc = new jsPDF()
      let y = 16
      doc.setFontSize(16)
      doc.text('Skin Screening Report', 14, y)
      y += 8
      doc.setFontSize(10)
      const lines = [
        `Consultation ID: ${data.consultation_id}    Date: ${(data.created_at || '').slice(0, 10)}`,
        `Patient: ${data.patient?.patient_id} · ${data.patient?.age}y ${data.patient?.gender} · ${data.patient?.location}`,
        '',
        `RISK LEVEL: ${risk}`,
        `Detected condition (AI suggestion): ${data.condition_type}`,
        `Confidence: High ${Math.round((data.confidence?.High || 0) * 100)}% · Medium ${Math.round(
          (data.confidence?.Medium || 0) * 100,
        )}% · Low ${Math.round((data.confidence?.Low || 0) * 100)}%`,
        data.vitals_temp ? `Vitals temperature: ${data.vitals_temp} °C` : null,
        data.staff_notes ? `Staff notes: ${data.staff_notes}` : null,
        data.referred_to_specialist
          ? `Referred: yes (${data.referral_urgency || ''} · ${data.referral_specialist || ''}) on ${(data.referred_at || '').slice(0, 10)}`
          : 'Referred: no',
      ].filter(Boolean)
      for (const line of lines) {
        for (const wrapped of doc.splitTextToSize(line, 180)) {
          doc.text(wrapped, 14, y)
          y += 6
        }
      }
      y += 4
      doc.setFontSize(9)
      for (const wrapped of doc.splitTextToSize(
        'DISCLAIMER: This is an AI screening aid, NOT a diagnosis. All HIGH risk cases must be ' +
          'seen by a dermatologist. Consult a qualified physician for final diagnosis and treatment.',
        180,
      )) {
        doc.text(wrapped, 14, y)
        y += 5
      }
      doc.save(`consultation-${data.consultation_id}.pdf`)
      toast.success('Report downloaded')
    } catch (e) {
      toast.error(apiError(e))
    } finally {
      setDownloading(false)
    }
  }

  return (
    <div className="mx-auto max-w-4xl space-y-5">
      <div className="card">
        <div className="flex flex-wrap items-center gap-4">
          <RiskBadge risk={risk} size="lg" />
          <div className="min-w-0">
            <h1 className="text-xl font-bold">Screening Result</h1>
            <p className="text-sm text-slate-500">
              Consultation #{data.consultation_id} · {(data.created_at || '').slice(0, 16).replace('T', ' ')}
            </p>
          </div>
          {data.model_mode === 'demo' && (
            <span
              className="rounded-lg border border-amber-400 bg-amber-100 px-3 py-1.5 text-xs font-semibold text-amber-900"
              title="Trained model weights not installed on this server"
            >
              ⚠ Demo model — not real inference
            </span>
          )}
        </div>
      </div>

      <div className="grid gap-5 md:grid-cols-2">
        <div className="card">
          <h2 className="mb-3 font-semibold">Uploaded image</h2>
          {image ? (
            <img src={image} alt="Uploaded skin lesion" className="w-full rounded-xl border border-slate-200" />
          ) : (
            <div className="flex h-48 items-center justify-center rounded-xl bg-slate-100 text-sm text-slate-400">
              Image unavailable
            </div>
          )}
          <dl className="mt-4 space-y-1 text-sm text-slate-600">
            <div className="flex justify-between">
              <dt>Patient</dt>
              <dd>
                #{data.patient?.patient_id} · {data.patient?.age}y {data.patient?.gender}
              </dd>
            </div>
            <div className="flex justify-between">
              <dt>Location</dt>
              <dd>{data.patient?.location}</dd>
            </div>
            {data.vitals_temp != null && (
              <div className="flex justify-between">
                <dt>Temperature</dt>
                <dd>{data.vitals_temp} °C</dd>
              </div>
            )}
          </dl>
        </div>

        <div className="card space-y-5">
          <div>
            <h2 className="mb-3 font-semibold">Model confidence</h2>
            <ConfidenceChart confidence={data.confidence} />
          </div>
          <div>
            <p className="text-sm font-semibold text-slate-700">Detected condition (suggestion)</p>
            <p className="text-lg font-bold text-slate-800">{data.condition_type}</p>
          </div>
          <div className={`rounded-xl border-2 p-4 text-sm leading-relaxed ${REC_STYLES[risk]}`}>
            <p className="font-bold">Recommendation</p>
            <p className="mt-1">
              {risk === 'LOW' && 'Continue routine care. Schedule a follow-up in 3 months.'}
              {risk === 'MEDIUM' && 'Monitor for changes. Refer to a dermatologist within 2 weeks.'}
              {risk === 'HIGH' && 'Refer to a dermatologist IMMEDIATELY.'}
            </p>
          </div>
        </div>
      </div>

      <div className="card space-y-3">
        <h2 className="font-semibold">Staff notes</h2>
        <textarea
          className="input min-h-[80px]"
          placeholder="Observations, patient complaints, …"
          value={notes}
          onChange={(e) => setNotes(e.target.value)}
        />
        <div className="flex flex-wrap gap-3">
          <button className="btn-primary" onClick={saveNotes} disabled={savingNotes}>
            {savingNotes ? 'Saving…' : 'Save Notes'}
          </button>
          {data.referred_to_specialist && (
            <label className="btn-secondary gap-2">
              Outcome:
              <select
                className="rounded-lg border border-slate-300 px-2 py-1.5"
                value={data.outcome || ''}
                onChange={(e) => e.target.value && setOutcome(e.target.value)}
              >
                <option value="">Select…</option>
                <option value="healed">Healed</option>
                <option value="ongoing">Ongoing</option>
                <option value="escalated">Escalated</option>
              </select>
            </label>
          )}
        </div>
      </div>

      <div className="flex flex-wrap gap-3">
        <button className="btn-primary" onClick={() => navigate(`/referral/${data.consultation_id}`)}>
          Refer to Specialist
        </button>
        <button className="btn-secondary" onClick={downloadReport} disabled={downloading}>
          {downloading ? 'Generating…' : 'Download Report (PDF)'}
        </button>
        <button className="btn-secondary" onClick={() => navigate('/intake')}>
          New Consultation
        </button>
        <button className="btn-secondary" onClick={() => navigate('/history')}>
          View History
        </button>
      </div>

      <DisclaimerBanner />
    </div>
  )
}

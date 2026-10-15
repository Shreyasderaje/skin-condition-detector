import { useState } from 'react'
import { useNavigate, useParams } from 'react-router-dom'
import { toast } from 'react-toastify'
import DisclaimerBanner from '../components/DisclaimerBanner'
import api, { apiError } from '../services/api'

const REASONS = [
  'Suspected malignancy',
  'Lesion growing or changing',
  'Bleeding or non-healing lesion',
  'Severe dermatitis / eczema',
  'Uncertain diagnosis',
  'Patient request',
]
const SPECIALISTS = ['Dermatologist', 'General Physician']
const URGENCIES = ['Routine', 'Urgent', 'Emergency']

export default function ReferralForm() {
  const { consultationId } = useParams()
  const navigate = useNavigate()
  const [reason, setReason] = useState(REASONS[0])
  const [detail, setDetail] = useState('')
  const [specialist, setSpecialist] = useState(SPECIALISTS[0])
  const [urgency, setUrgency] = useState('Routine')
  const [followUp, setFollowUp] = useState('')
  const [busy, setBusy] = useState(false)

  const submit = async (e) => {
    e.preventDefault()
    setBusy(true)
    try {
      const { data } = await api.post(`/consultations/${consultationId}/referral`, {
        referred_to_specialist: true,
        referral_reason: detail.trim() ? `${reason}: ${detail.trim()}` : reason,
        referral_urgency: urgency,
        referral_specialist: specialist,
        follow_up_date: followUp || undefined,
      })
      toast.success(`Referral created (ID: ${data.referral_id})`)
      navigate('/history')
    } catch (error) {
      toast.error(apiError(error))
      setBusy(false)
    }
  }

  return (
    <div className="mx-auto max-w-xl space-y-5">
      <div className="card">
        <h1 className="text-2xl font-bold">Refer to Specialist</h1>
        <p className="mt-1 text-sm text-slate-500">Consultation #{consultationId}</p>

        <form onSubmit={submit} className="mt-5 space-y-4">
          <div>
            <label className="label" htmlFor="reason">Reason for referral</label>
            <select id="reason" className="input" value={reason} onChange={(e) => setReason(e.target.value)}>
              {REASONS.map((r) => <option key={r}>{r}</option>)}
            </select>
          </div>
          <div>
            <label className="label" htmlFor="detail">Additional details (optional)</label>
            <textarea
              id="detail"
              className="input min-h-[70px]"
              value={detail}
              onChange={(e) => setDetail(e.target.value)}
              placeholder="Describe what was observed…"
            />
          </div>
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="label" htmlFor="specialist">Specialist type</label>
              <select
                id="specialist"
                className="input"
                value={specialist}
                onChange={(e) => setSpecialist(e.target.value)}
              >
                {SPECIALISTS.map((s) => <option key={s}>{s}</option>)}
              </select>
            </div>
            <div>
              <label className="label" htmlFor="followup">Follow-up date</label>
              <input
                id="followup"
                type="date"
                className="input"
                value={followUp}
                onChange={(e) => setFollowUp(e.target.value)}
              />
            </div>
          </div>
          <fieldset>
            <legend className="label">Urgency level</legend>
            <div className="grid grid-cols-3 gap-2">
              {URGENCIES.map((u) => (
                <button
                  key={u}
                  type="button"
                  onClick={() => setUrgency(u)}
                  className={`rounded-xl border-2 px-2 py-3 text-sm font-semibold transition ${
                    urgency === u
                      ? u === 'Emergency'
                        ? 'border-red-400 bg-red-50 text-red-800'
                        : u === 'Urgent'
                          ? 'border-amber-400 bg-amber-50 text-amber-900'
                          : 'border-green-400 bg-green-50 text-green-800'
                      : 'border-slate-200 bg-white text-slate-500'
                  }`}
                >
                  {u}
                </button>
              ))}
            </div>
          </fieldset>

          <button type="submit" className="btn-primary w-full" disabled={busy}>
            {busy ? 'Submitting…' : 'Submit Referral'}
          </button>
        </form>
      </div>
      <DisclaimerBanner />
    </div>
  )
}

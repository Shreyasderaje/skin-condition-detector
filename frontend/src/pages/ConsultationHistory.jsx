import { useCallback, useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { toast } from 'react-toastify'
import RiskBadge from '../components/RiskBadge'
import api, { apiError, fetchImageBlobUrl } from '../services/api'

const PAGE_SIZE = 20

export default function ConsultationHistory() {
  const navigate = useNavigate()
  const [items, setItems] = useState([])
  const [total, setTotal] = useState(0)
  const [page, setPage] = useState(1)
  const [risk, setRisk] = useState('')
  const [startDate, setStartDate] = useState('')
  const [endDate, setEndDate] = useState('')
  const [selected, setSelected] = useState(null) // { data, image }

  const load = useCallback(async () => {
    try {
      const params = { page, limit: PAGE_SIZE }
      if (risk) params.risk_level = risk
      if (startDate) params.start_date = startDate
      if (endDate) params.end_date = endDate
      const { data } = await api.get('/consultations', { params })
      setItems(data.items)
      setTotal(data.total)
    } catch (e) {
      toast.error(apiError(e))
    }
  }, [page, risk, startDate, endDate])

  useEffect(() => {
    load()
  }, [load])

  const openDetail = async (id) => {
    try {
      const [detail, image] = await Promise.all([
        api.get(`/consultations/${id}`).then((r) => r.data),
        fetchImageBlobUrl(id).catch(() => null),
      ])
      setSelected({ data: detail, image })
    } catch (e) {
      toast.error(apiError(e))
    }
  }

  const exportCsv = () => {
    const header = [
      'Consultation ID', 'Date', 'Patient ID', 'Age', 'Gender', 'Location',
      'Risk Level', 'Condition', 'Referred', 'Outcome',
    ]
    const rows = items.map((c) => [
      c.consultation_id,
      c.created_at,
      c.patient_id,
      c.patient?.age ?? '',
      c.patient?.gender ?? '',
      c.patient?.location ?? '',
      c.risk_level,
      c.condition_type,
      c.referred_to_specialist ? 'Yes' : 'No',
      c.outcome || '',
    ])
    const csv = [header, ...rows]
      .map((row) => row.map((v) => `"${String(v ?? '').replaceAll('"', '""')}"`).join(','))
      .join('\n')
    const url = URL.createObjectURL(new Blob([csv], { type: 'text/csv' }))
    const a = document.createElement('a')
    a.href = url
    a.download = 'consultation-history.csv'
    a.click()
    URL.revokeObjectURL(url)
  }

  const pages = Math.max(Math.ceil(total / PAGE_SIZE), 1)

  return (
    <div className="space-y-5">
      <div className="flex flex-wrap items-end gap-3">
        <h1 className="mr-auto text-2xl font-bold">Consultation History</h1>
        <div>
          <label className="label" htmlFor="f-risk">Risk</label>
          <select id="f-risk" className="input" value={risk} onChange={(e) => { setPage(1); setRisk(e.target.value) }}>
            <option value="">All</option>
            <option>LOW</option>
            <option>MEDIUM</option>
            <option>HIGH</option>
          </select>
        </div>
        <div>
          <label className="label" htmlFor="f-start">From</label>
          <input id="f-start" type="date" className="input" value={startDate} onChange={(e) => { setPage(1); setStartDate(e.target.value) }} />
        </div>
        <div>
          <label className="label" htmlFor="f-end">To</label>
          <input id="f-end" type="date" className="input" value={endDate} onChange={(e) => { setPage(1); setEndDate(e.target.value) }} />
        </div>
        <button className="btn-secondary" onClick={exportCsv}>Export CSV</button>
      </div>

      <div className="card overflow-x-auto p-0">
        <table className="w-full min-w-[720px] text-left text-sm">
          <thead>
            <tr className="border-b border-slate-200 bg-slate-50 text-xs uppercase tracking-wide text-slate-500">
              <th className="px-4 py-3">Date</th>
              <th className="px-4 py-3">Patient</th>
              <th className="px-4 py-3">Risk</th>
              <th className="px-4 py-3">Condition</th>
              <th className="px-4 py-3">Referred?</th>
              <th className="px-4 py-3">Outcome</th>
            </tr>
          </thead>
          <tbody>
            {items.map((c) => (
              <tr
                key={c.consultation_id}
                onClick={() => openDetail(c.consultation_id)}
                className="cursor-pointer border-b border-slate-100 hover:bg-teal-50"
              >
                <td className="px-4 py-3">{(c.created_at || '').slice(0, 10)}</td>
                <td className="px-4 py-3">#{c.patient_id}</td>
                <td className="px-4 py-3"><RiskBadge risk={c.risk_level} size="sm" /></td>
                <td className="px-4 py-3">{c.condition_type}</td>
                <td className="px-4 py-3">{c.referred_to_specialist ? '✅ Yes' : '—'}</td>
                <td className="px-4 py-3">{c.outcome || 'Pending'}</td>
              </tr>
            ))}
            {items.length === 0 && (
              <tr>
                <td colSpan={6} className="px-4 py-10 text-center text-slate-400">
                  No consultations match the filters.
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>

      <div className="flex items-center justify-between">
        <p className="text-sm text-slate-500">{total} consultation(s)</p>
        <div className="flex gap-2">
          <button className="btn-secondary" disabled={page <= 1} onClick={() => setPage(page - 1)}>
            ← Prev
          </button>
          <span className="btn-secondary pointer-events-none">Page {page}/{pages}</span>
          <button className="btn-secondary" disabled={page >= pages} onClick={() => setPage(page + 1)}>
            Next →
          </button>
        </div>
      </div>

      {selected && (
        <div className="card border-teal-300">
          <div className="flex items-start justify-between">
            <h2 className="text-lg font-bold">Consultation #{selected.data.consultation_id}</h2>
            <button className="text-sm text-slate-500 underline" onClick={() => setSelected(null)}>
              Close
            </button>
          </div>
          <div className="mt-4 grid gap-5 md:grid-cols-2">
            <div>
              {selected.image ? (
                <img src={selected.image} alt="Consultation" className="w-full rounded-xl border border-slate-200" />
              ) : (
                <div className="flex h-40 items-center justify-center rounded-xl bg-slate-100 text-sm text-slate-400">
                  Image unavailable
                </div>
              )}
            </div>
            <dl className="space-y-1.5 text-sm">
              <div className="flex justify-between gap-4"><dt className="text-slate-500">Risk</dt><dd><RiskBadge risk={selected.data.risk_level} size="sm" /></dd></div>
              <div className="flex justify-between gap-4"><dt className="text-slate-500">Condition</dt><dd>{selected.data.condition_type}</dd></div>
              <div className="flex justify-between gap-4"><dt className="text-slate-500">Confidence</dt><dd>{JSON.stringify(selected.data.confidence)}</dd></div>
              <div className="flex justify-between gap-4"><dt className="text-slate-500">Patient</dt><dd>#{selected.data.patient?.patient_id} · {selected.data.patient?.age}y {selected.data.patient?.gender}</dd></div>
              <div className="flex justify-between gap-4"><dt className="text-slate-500">Temperature</dt><dd>{selected.data.vitals_temp != null ? `${selected.data.vitals_temp} °C` : '—'}</dd></div>
              <div className="flex justify-between gap-4"><dt className="text-slate-500">Referred</dt><dd>{selected.data.referred_to_specialist ? `${selected.data.referral_urgency || ''} ${selected.data.referral_specialist || ''}` : 'No'}</dd></div>
              <div className="flex justify-between gap-4"><dt className="text-slate-500">Outcome</dt><dd>{selected.data.outcome || 'Pending'}</dd></div>
              {selected.data.staff_notes && (
                <div className="flex justify-between gap-4"><dt className="text-slate-500">Notes</dt><dd className="text-right">{selected.data.staff_notes}</dd></div>
              )}
              <div className="pt-2">
                <button className="btn-primary w-full" onClick={() => navigate(`/results/${selected.data.consultation_id}`)}>
                  Open Full Results
                </button>
              </div>
            </dl>
          </div>
        </div>
      )}
    </div>
  )
}

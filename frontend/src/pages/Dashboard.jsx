import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { toast } from 'react-toastify'
import {
  Cell,
  Legend,
  Line,
  LineChart,
  Pie,
  PieChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts'
import api, { apiError } from '../services/api'

const RISK_COLORS = { Low: '#22c55e', Medium: '#f59e0b', High: '#ef4444' }

export default function Dashboard() {
  const [summary, setSummary] = useState(null)
  const [points, setPoints] = useState([])
  const [period, setPeriod] = useState('7days')
  const [startDate, setStartDate] = useState('')
  const [endDate, setEndDate] = useState('')

  useEffect(() => {
    const params = {}
    if (startDate) params.start_date = startDate
    if (endDate) params.end_date = endDate
    api
      .get('/analytics/summary', { params })
      .then((r) => setSummary(r.data))
      .catch((e) => toast.error(apiError(e)))
  }, [startDate, endDate])

  useEffect(() => {
    api
      .get('/analytics/trends', { params: { period } })
      .then((r) => setPoints(r.data.points))
      .catch((e) => toast.error(apiError(e)))
  }, [period])

  const pieData = summary
    ? Object.entries(summary.risk_distribution)
        .filter(([, value]) => value > 0)
        .map(([name, value]) => ({ name, value }))
    : []

  return (
    <div className="space-y-5">
      <div className="flex flex-wrap items-end gap-3">
        <h1 className="mr-auto text-2xl font-bold">PHC Dashboard</h1>
        <div>
          <label className="label" htmlFor="d-start">From</label>
          <input id="d-start" type="date" className="input" value={startDate} onChange={(e) => setStartDate(e.target.value)} />
        </div>
        <div>
          <label className="label" htmlFor="d-end">To</label>
          <input id="d-end" type="date" className="input" value={endDate} onChange={(e) => setEndDate(e.target.value)} />
        </div>
        <Link to="/intake" className="btn-primary">+ New Patient</Link>
      </div>

      <div className="grid gap-4 sm:grid-cols-3">
        <div className="card">
          <p className="text-sm font-semibold text-slate-500">Total consultations</p>
          <p className="mt-1 text-3xl font-bold text-teal-800">{summary?.total_consultations ?? '…'}</p>
          <p className="mt-1 text-xs text-slate-400">in selected period</p>
        </div>
        <div className="card">
          <p className="text-sm font-semibold text-slate-500">Referral rate</p>
          <p className="mt-1 text-3xl font-bold text-amber-600">
            {summary ? `${summary.referral_rate}%` : '…'}
          </p>
          <p className="mt-1 text-xs text-slate-400">share of consultations referred</p>
        </div>
        <div className="card">
          <p className="text-sm font-semibold text-slate-500">High-risk cases</p>
          <p className="mt-1 text-3xl font-bold text-red-600">{summary?.risk_distribution?.High ?? '…'}</p>
          <p className="mt-1 text-xs text-slate-400">must be referred immediately</p>
        </div>
      </div>

      <div className="grid gap-5 lg:grid-cols-5">
        <div className="card lg:col-span-3">
          <div className="mb-3 flex flex-wrap items-center justify-between gap-2">
            <h2 className="font-semibold">Consultations over time</h2>
            <div className="flex gap-1 rounded-lg bg-slate-100 p-1">
              {['7days', '30days', '90days'].map((p) => (
                <button
                  key={p}
                  onClick={() => setPeriod(p)}
                  className={`rounded-md px-3 py-1.5 text-xs font-semibold ${
                    period === p ? 'bg-white text-teal-800 shadow' : 'text-slate-500'
                  }`}
                >
                  {p.replace('days', ' days')}
                </button>
              ))}
            </div>
          </div>
          <div className="h-64">
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={points} margin={{ top: 5, right: 10, bottom: 0, left: -20 }}>
                <XAxis dataKey="date" tick={{ fontSize: 11 }} tickFormatter={(d) => d.slice(5)} />
                <YAxis allowDecimals={false} tick={{ fontSize: 11 }} />
                <Tooltip />
                <Legend />
                <Line type="monotone" dataKey="total" name="All" stroke="#0f766e" strokeWidth={2} dot={false} />
                <Line type="monotone" dataKey="High" name="High risk" stroke="#ef4444" strokeWidth={2} dot={false} />
                <Line type="monotone" dataKey="Medium" name="Medium" stroke="#f59e0b" strokeWidth={2} dot={false} />
                <Line type="monotone" dataKey="Low" name="Low" stroke="#22c55e" strokeWidth={2} dot={false} />
              </LineChart>
            </ResponsiveContainer>
          </div>
        </div>

        <div className="card lg:col-span-2">
          <h2 className="mb-3 font-semibold">Risk distribution</h2>
          {pieData.length ? (
            <div className="h-64">
              <ResponsiveContainer width="100%" height="100%">
                <PieChart>
                  <Pie data={pieData} dataKey="value" nameKey="name" innerRadius={50} outerRadius={80} label>
                    {pieData.map((entry) => (
                      <Cell key={entry.name} fill={RISK_COLORS[entry.name]} />
                    ))}
                  </Pie>
                  <Tooltip />
                  <Legend />
                </PieChart>
              </ResponsiveContainer>
            </div>
          ) : (
            <p className="py-16 text-center text-sm text-slate-400">
              No consultations in this period yet.
            </p>
          )}
        </div>
      </div>

      <div className="card">
        <h2 className="mb-3 font-semibold">Top conditions detected</h2>
        {summary && Object.keys(summary.condition_breakdown).length ? (
          <table className="w-full text-left text-sm">
            <thead>
              <tr className="border-b border-slate-200 text-xs uppercase text-slate-500">
                <th className="py-2">Condition</th>
                <th className="py-2 text-right">Cases</th>
              </tr>
            </thead>
            <tbody>
              {Object.entries(summary.condition_breakdown)
                .sort(([, a], [, b]) => b - a)
                .map(([condition, count]) => (
                  <tr key={condition} className="border-b border-slate-100">
                    <td className="py-2">{condition}</td>
                    <td className="py-2 text-right font-semibold">{count}</td>
                  </tr>
                ))}
            </tbody>
          </table>
        ) : (
          <p className="py-6 text-center text-sm text-slate-400">No data yet.</p>
        )}
      </div>
    </div>
  )
}

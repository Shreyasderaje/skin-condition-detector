import { useState } from 'react'
import { Link, useLocation, useNavigate } from 'react-router-dom'
import { toast } from 'react-toastify'
import { useAuth } from '../context/AuthContext'
import { apiError } from '../services/api'

const PHC_SUGGESTIONS = [
  'Mulki PHC', 'Surathkal PHC', 'Mangaluru PHC', 'Bantwal PHC', 'Puttur PHC',
  'Sullia PHC', 'Belthangady PHC', 'Moodabidri PHC', 'Karkala PHC',
  'Udupi PHC', 'Kundapura PHC', 'Brahmavar PHC',
]

export default function Login() {
  const { login, register } = useAuth()
  const navigate = useNavigate()
  const location = useLocation()
  const [mode, setMode] = useState('login')
  const [busy, setBusy] = useState(false)
  const [agreed, setAgreed] = useState(false)
  const [form, setForm] = useState({
    email: '',
    password: '',
    staff_name: '',
    phc_name: '',
    phone: '',
  })
  const set = (key) => (e) => setForm({ ...form, [key]: e.target.value })

  const submit = async (e) => {
    e.preventDefault()
    setBusy(true)
    try {
      if (mode === 'login') {
        await login(form.email, form.password)
        toast.success('Welcome back!')
      } else {
        if (!agreed) {
          toast.error('Please read and acknowledge the medical disclaimer first')
          setBusy(false)
          return
        }
        await register({
          staff_name: form.staff_name,
          phc_name: form.phc_name,
          email: form.email,
          password: form.password,
          phone: form.phone || undefined,
        })
        toast.success('Account created. Welcome!')
      }
      navigate(location.state?.from?.pathname || '/')
    } catch (error) {
      toast.error(apiError(error))
    } finally {
      setBusy(false)
    }
  }

  return (
    <div className="mx-auto max-w-md">
      <div className="card">
        <h1 className="text-2xl font-bold text-slate-800">PHC Staff Login</h1>
        <p className="mt-1 text-sm text-slate-500">
          AI-assisted skin screening for coastal Karnataka PHCs.
        </p>

        <div className="mt-4 grid grid-cols-2 gap-2 rounded-xl bg-slate-100 p-1">
          {['login', 'register'].map((m) => (
            <button
              key={m}
              type="button"
              onClick={() => setMode(m)}
              className={`rounded-lg px-3 py-2 text-sm font-semibold transition ${
                mode === m ? 'bg-white text-teal-800 shadow' : 'text-slate-500'
              }`}
            >
              {m === 'login' ? 'Sign in' : 'Register PHC staff'}
            </button>
          ))}
        </div>

        <form onSubmit={submit} className="mt-5 space-y-4">
          {mode === 'register' && (
            <>
              <div>
                <label className="label" htmlFor="staff_name">Your name</label>
                <input id="staff_name" className="input" value={form.staff_name} onChange={set('staff_name')} required />
              </div>
              <div>
                <label className="label" htmlFor="phc_name">PHC name</label>
                <input
                  id="phc_name"
                  className="input"
                  list="phc-list"
                  value={form.phc_name}
                  onChange={set('phc_name')}
                  placeholder="e.g. Mulki PHC"
                  required
                />
                <datalist id="phc-list">
                  {PHC_SUGGESTIONS.map((p) => <option key={p} value={p} />)}
                </datalist>
              </div>
              <div>
                <label className="label" htmlFor="phone">Phone (optional)</label>
                <input id="phone" className="input" value={form.phone} onChange={set('phone')} placeholder="+919876543210" />
              </div>
            </>
          )}
          <div>
            <label className="label" htmlFor="email">Email</label>
            <input id="email" type="email" className="input" value={form.email} onChange={set('email')} required />
          </div>
          <div>
            <label className="label" htmlFor="password">Password</label>
            <input
              id="password"
              type="password"
              className="input"
              value={form.password}
              onChange={set('password')}
              minLength={8}
              required
            />
            {mode === 'register' && (
              <p className="mt-1 text-xs text-slate-500">Minimum 8 characters.</p>
            )}
          </div>

          {mode === 'register' && (
            <label className="flex items-start gap-2 rounded-lg bg-amber-50 p-3 text-sm text-amber-900">
              <input
                type="checkbox"
                className="mt-1 h-4 w-4"
                checked={agreed}
                onChange={(e) => setAgreed(e.target.checked)}
              />
              <span>
                I have read the{' '}
                <Link to="/disclaimer" className="font-semibold underline" target="_blank">
                  Medical Disclaimer
                </Link>{' '}
                and understand this tool is a screening aid, not a diagnosis.
              </span>
            </label>
          )}

          <button type="submit" className="btn-primary w-full" disabled={busy}>
            {busy ? 'Please wait…' : mode === 'login' ? 'Sign in' : 'Create account'}
          </button>
        </form>
      </div>
    </div>
  )
}

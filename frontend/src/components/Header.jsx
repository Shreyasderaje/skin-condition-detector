import { NavLink, useNavigate } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'

const linkClass = ({ isActive }) =>
  `rounded-lg px-3 py-2 text-sm font-medium transition ${
    isActive ? 'bg-white/20 text-white' : 'text-teal-50 hover:bg-white/10'
  }`

export default function Header() {
  const { staff, logout } = useAuth()
  const navigate = useNavigate()
  if (!staff) return null

  return (
    <header className="bg-teal-800 text-white shadow-md">
      <div className="mx-auto flex max-w-6xl flex-wrap items-center gap-x-4 gap-y-2 px-4 py-3">
        <NavLink to="/" className="mr-2 text-lg font-bold tracking-tight">
          🩺 SkinScreen
        </NavLink>
        <nav className="flex flex-wrap gap-1">
          <NavLink to="/" end className={linkClass}>
            Dashboard
          </NavLink>
          <NavLink to="/intake" className={linkClass}>
            New Patient
          </NavLink>
          <NavLink to="/history" className={linkClass}>
            History
          </NavLink>
          <NavLink to="/disclaimer" className={linkClass}>
            Disclaimer
          </NavLink>
        </nav>
        <div className="ml-auto flex items-center gap-3">
          <span className="text-sm text-teal-100">
            {staff.staff?.staff_name || 'Staff'} · {staff.phc_name}
          </span>
          <button
            onClick={() => {
              logout()
              navigate('/login')
            }}
            className="rounded-lg border border-teal-500 px-3 py-1.5 text-sm font-semibold hover:bg-teal-700"
          >
            Logout
          </button>
        </div>
      </div>
    </header>
  )
}

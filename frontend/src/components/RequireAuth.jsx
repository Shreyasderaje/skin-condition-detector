import { Navigate, Outlet, useLocation } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'

export default function RequireAuth() {
  const { staff } = useAuth()
  const location = useLocation()
  if (!staff) return <Navigate to="/login" state={{ from: location }} replace />
  return <Outlet />
}

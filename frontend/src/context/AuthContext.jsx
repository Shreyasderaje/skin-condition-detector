import { createContext, useContext, useState } from 'react'
import api, { setAuthToken } from '../services/api'

const AuthContext = createContext(null)

export function AuthProvider({ children }) {
  const [staff, setStaff] = useState(() => {
    try {
      return JSON.parse(localStorage.getItem('staff') || 'null')
    } catch {
      return null
    }
  })

  const persist = (data) => {
    setAuthToken(data.access_token)
    localStorage.setItem('staff', JSON.stringify(data))
    setStaff(data)
  }

  const login = async (email, password) => {
    const { data } = await api.post('/auth/login', { email, password })
    persist(data)
    return data
  }

  const register = async (payload) => {
    const { data } = await api.post('/auth/register', payload)
    persist(data)
    return data
  }

  const logout = () => {
    api.post('/auth/logout').catch(() => {})
    setAuthToken(null)
    localStorage.removeItem('staff')
    setStaff(null)
  }

  return (
    <AuthContext.Provider value={{ staff, login, register, logout }}>
      {children}
    </AuthContext.Provider>
  )
}

export const useAuth = () => useContext(AuthContext)

import axios from 'axios'

// Unset during development -> Vite dev proxy handles /api -> backend:5000.
// Unset in production (docker) -> nginx proxy handles /api -> backend:5000.
export const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || '/api'

export function getAuthToken() {
  return localStorage.getItem('token')
}

export function setAuthToken(token) {
  if (token) localStorage.setItem('token', token)
  else localStorage.removeItem('token')
}

const api = axios.create({ baseURL: API_BASE_URL, timeout: 30000 })

api.interceptors.request.use((config) => {
  const token = getAuthToken()
  if (token) config.headers.Authorization = `Bearer ${token}`
  return config
})

api.interceptors.response.use(
  (res) => res,
  (error) => {
    if (error.response?.status === 401 && window.location.pathname !== '/login') {
      setAuthToken(null)
      localStorage.removeItem('staff')
      window.location.href = '/login'
    }
    return Promise.reject(error)
  },
)

export function apiError(error) {
  return error?.response?.data?.error || error?.message || 'Something went wrong'
}

// <img> tags can't send Authorization headers, so consultations images are
// fetched as authenticated blobs and displayed via an object URL.
export async function fetchImageBlobUrl(consultationId) {
  const res = await api.get(`/consultations/${consultationId}/image`, { responseType: 'blob' })
  return URL.createObjectURL(res.data)
}

export default api

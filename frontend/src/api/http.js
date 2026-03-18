import axios from 'axios'
import { clearStoredAuth, getAuthToken } from '../utils/auth'

const http = axios.create({
  baseURL: import.meta.env.VITE_API_BASE || 'http://127.0.0.1:8000',
  timeout: 15000,
})

http.interceptors.request.use((config) => {
  const token = getAuthToken()
  if (token) config.headers.Authorization = `Bearer ${token}`
  return config
})

http.interceptors.response.use(
  (res) => res,
  (err) => {
    if (err?.response?.status === 401) clearStoredAuth()
    return Promise.reject(err)
  }
)

export default http

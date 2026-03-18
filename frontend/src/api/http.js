import axios from 'axios'

const http = axios.create({
  baseURL: import.meta.env.VITE_API_BASE || 'http://127.0.0.1:8000',
  timeout: 15000,
})

http.interceptors.request.use((config) => {
  const username = localStorage.getItem('shop:auth_user')
  if (username) config.headers['X-Auth-User'] = username
  return config
})

http.interceptors.response.use(
  (res) => res,
  (err) => {
    if (err?.response?.status === 401) {
      localStorage.removeItem('shop:auth_user')
      localStorage.removeItem('shop:auth_display_name')
    }
    return Promise.reject(err)
  }
)

export default http

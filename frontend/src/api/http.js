import axios from 'axios'

const http = axios.create({
  baseURL: import.meta.env.VITE_API_BASE || 'http://127.0.0.1:8000',
  timeout: 15000,
})

http.interceptors.response.use(
  (res) => res,
  (err) => Promise.reject(err)
)

export default http

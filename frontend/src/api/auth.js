import http from './http'

export function login(data) {
  return http.post('/api/auth/login', data).then((r) => r.data)
}

export function getCurrentUser() {
  return http.get('/api/auth/me').then((r) => r.data)
}

export function logout() {
  return http.post('/api/auth/logout').then((r) => r.data)
}

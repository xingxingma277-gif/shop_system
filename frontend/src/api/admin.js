import http from './http'

export function listUsers(params) {
  return http.get('/api/admin/users', { params }).then((r) => r.data)
}

export function createUser(data) {
  return http.post('/api/admin/users', data).then((r) => r.data)
}

export function updateUser(id, data) {
  return http.put(`/api/admin/users/${id}`, data).then((r) => r.data)
}

export function listRoles(params) {
  return http.get('/api/admin/roles', { params }).then((r) => r.data)
}

export function createRole(data) {
  return http.post('/api/admin/roles', data).then((r) => r.data)
}

export function updateRole(id, data) {
  return http.put(`/api/admin/roles/${id}`, data).then((r) => r.data)
}

export function listPermissions() {
  return http.get('/api/admin/permissions').then((r) => r.data)
}

export function createPermission(data) {
  return http.post('/api/admin/permissions', data).then((r) => r.data)
}

export function listAuditLogs(params) {
  return http.get('/api/admin/audit-logs', { params }).then((r) => r.data)
}

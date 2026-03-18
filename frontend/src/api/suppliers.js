import http from './http'

export function listSuppliers(params) {
  return http.get('/api/suppliers', { params }).then((r) => r.data)
}

export function createSupplier(data) {
  return http.post('/api/suppliers', data).then((r) => r.data)
}

export function updateSupplier(id, data) {
  return http.put(`/api/suppliers/${id}`, data).then((r) => r.data)
}

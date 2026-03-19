import http from './http'

export function listWarehouses(params) {
  return http.get('/api/warehouses', { params }).then((r) => r.data)
}

export function createWarehouse(data) {
  return http.post('/api/warehouses', data).then((r) => r.data)
}

export function updateWarehouse(id, data) {
  return http.put(`/api/warehouses/${id}`, data).then((r) => r.data)
}

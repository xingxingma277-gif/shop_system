import http from './http'

export function listInventoryAdjustments(params) {
  return http.get('/api/inventory/adjustments', { params }).then((r) => r.data)
}

export function createInventoryAdjustment(data) {
  return http.post('/api/inventory/adjustments', data).then((r) => r.data)
}

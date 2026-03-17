import http from './http'

export function getApSummary(params) {
  return http.get('/api/reports/ap-summary', { params }).then((r) => r.data)
}

export function getInventorySummary(params) {
  return http.get('/api/reports/inventory-summary', { params }).then((r) => r.data)
}

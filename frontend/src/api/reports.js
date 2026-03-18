import http from './http'

export function getApSummary(params) {
  return http.get('/api/reports/ap-summary', { params }).then((r) => r.data)
}

export function getApAging(params) {
  return http.get('/api/reports/ap-aging', { params }).then((r) => r.data)
}

export function getInventorySummary(params) {
  return http.get('/api/reports/inventory-summary', { params }).then((r) => r.data)
}

export function getDashboardSummary(params) {
  return http.get('/api/reports/dashboard-summary', { params }).then((r) => r.data)
}

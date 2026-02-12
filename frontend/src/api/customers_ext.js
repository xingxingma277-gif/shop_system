import http from './http'

export function getCustomerStatement(customerId, params) {
  return http.get(`/api/customers/${customerId}/statement`, { params }).then((r) => r.data)
}

export function getCustomerArSummary(customerId) {
  return http.get(`/api/customers/${customerId}/ar_summary`).then((r) => r.data)
}

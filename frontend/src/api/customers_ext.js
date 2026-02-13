import http from './http'

export function getCustomerStatement(customerId, params) {
  return http.get(`/api/customers/${customerId}/statement`, { params }).then((r) => r.data)
}

export function getCustomerArSummary(customerId) {
  return http.get(`/api/customers/${customerId}/ar_summary`).then((r) => r.data)
}

export function createCustomerReceipt(customerId, payload) {
  return http.post(`/api/customers/${customerId}/receipts`, payload).then((r) => r.data)
}

export function listCustomerPayments(customerId, params) {
  return http.get(`/api/customers/${customerId}/payments`, { params }).then((r) => r.data)
}

export function exportCustomerStatementUrl(customerId, params = {}) {
  const query = new URLSearchParams(params)
  return `${http.defaults.baseURL}/api/customers/${customerId}/statement/export?${query.toString()}`
}


export function listCustomerOpenSales(customerId, params) {
  return http.get(`/api/customers/${customerId}/open_sales`, { params }).then((r) => r.data)
}

export function allocateCustomerPayment(customerId, payload) {
  return http.post(`/api/customers/${customerId}/payments/allocate`, payload).then((r) => r.data)
}

export function getCustomerPaymentAllocations(customerId, paymentId) {
  return http.get(`/api/customers/${customerId}/payments/${paymentId}/allocations`).then((r) => r.data)
}

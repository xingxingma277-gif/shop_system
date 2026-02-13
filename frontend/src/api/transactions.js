import http from './http'

export function listTransactionSales(params) {
  return http.get('/api/transactions/sales', { params }).then((r) => r.data)
}

export function listTransactionPayments(params) {
  return http.get('/api/transactions/payments', { params }).then((r) => r.data)
}

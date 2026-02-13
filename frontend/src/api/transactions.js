import http from './http'

export function listTransactions(params) {
  return http.get('/api/transactions', { params }).then((r) => r.data)
}

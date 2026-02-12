import http from './http'

export function createPayment(payload) {
  return http.post('/api/payments', payload).then((r) => r.data)
}

export function batchApplyPayments(payload) {
  return http.post('/api/payments/batch_apply', payload).then((r) => r.data)
}

export function listPayments(params) {
  return http.get('/api/payments', { params }).then((r) => r.data)
}

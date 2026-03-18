import http from './http'

export function listPurchases(params) {
  return http.get('/api/purchases', { params }).then((r) => r.data)
}

export function getPurchase(id) {
  return http.get(`/api/purchases/${id}`).then((r) => r.data)
}

export function createPurchase(data) {
  return http.post('/api/purchases', data).then((r) => r.data)
}

export function confirmPurchase(id) {
  return http.post(`/api/purchases/${id}/confirm`).then((r) => r.data)
}

export function receivePurchase(id, data) {
  return http.post(`/api/purchases/${id}/receive`, data).then((r) => r.data)
}

export function returnPurchase(id, data) {
  return http.post(`/api/purchases/${id}/return`, data).then((r) => r.data)
}

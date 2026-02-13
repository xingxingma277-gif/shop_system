import http from './http'

export function createSale(data) {
  return http.post('/api/sales', data).then((r) => r.data)
}

export function listSalesApi(params) {
  return http.get('/api/sales', { params }).then((r) => r.data)
}

export function getSaleApi(id) {
  return http.get(`/api/sales/${id}`).then((r) => r.data)
}

export function submitSalePayment(saleId, payload) {
  return http.post(`/api/sales/${saleId}/payments`, payload).then((r) => r.data)
}

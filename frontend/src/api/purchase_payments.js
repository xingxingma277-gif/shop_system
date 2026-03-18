import http from './http'

export function createSupplierPayment(data) {
  return http.post('/api/purchase-payments', data).then((r) => r.data)
}

export function allocateSupplierPayment(paymentId, data) {
  return http.post(`/api/purchase-payments/${paymentId}/allocate`, data).then((r) => r.data)
}

export function listSupplierOpenPurchases(supplierId) {
  return http.get(`/api/purchase-payments/supplier/${supplierId}/open-purchases`).then((r) => r.data)
}

export function listSupplierPaymentRecords(supplierId) {
  return http.get(`/api/purchase-payments/supplier/${supplierId}/records`).then((r) => r.data)
}

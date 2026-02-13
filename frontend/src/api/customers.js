import http from './http'

export function listCustomers(params) {
  return http.get('/api/customers', { params }).then((r) => r.data)
}

export function createCustomer(data) {
  return http.post('/api/customers', data).then((r) => r.data)
}

export function updateCustomer(id, data) {
  return http.put(`/api/customers/${id}`, data).then((r) => r.data)
}

export function getCustomer(id) {
  return http.get(`/api/customers/${id}`).then((r) => r.data)
}

export function deleteCustomer(id) {
  return http.delete(`/api/customers/${id}`).then((r) => r.data)
}

export function listBuyers(customerId) {
  return http.get(`/api/customers/${customerId}/buyers`).then((r) => r.data)
}

export function createBuyer(customerId, payload) {
  return http.post(`/api/customers/${customerId}/buyers`, payload).then((r) => r.data)
}

export function getCustomerProductPriceHistory(customerId, productId, params = {}) {
  return http
    .get(`/api/customers/${customerId}/products/${productId}/price_history`, { params })
    .then((r) => r.data)
}

export function searchCustomersApi(keyword) {
  return http
    .get('/api/customers', {
      params: { page: 1, page_size: 50, active_only: true, q: keyword },
    })
    .then((r) => r.data)
}

export const listCustomersApi = listCustomers
export const getCustomerApi = getCustomer

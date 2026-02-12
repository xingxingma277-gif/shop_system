import http from './http'

// Customers.vue 用
export function listCustomers(params) {
  return http.get('/api/customers', { params }).then((r) => r.data)
}

export function createCustomer(data) {
  return http.post('/api/customers', data).then((r) => r.data)
}

export function updateCustomer(id, data) {
  return http.put(`/api/customers/${id}`, data).then((r) => r.data)
}

// NewSale.vue 常用：搜索客户（后端支持 q / active_only）
export function searchCustomersApi(keyword) {
  return http
    .get('/api/customers', {
      params: { page: 1, page_size: 50, active_only: true, q: keyword },
    })
    .then((r) => r.data)
}

// 兼容旧命名（如果你别处用到）
export const listCustomersApi = listCustomers
export const getCustomerApi = (id) => http.get(`/api/customers/${id}`).then((r) => r.data)

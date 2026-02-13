import http from './http'

export function listProducts(params) {
  return http.get('/api/products', { params }).then((r) => r.data)
}

export function createProduct(data) {
  return http.post('/api/products', data).then((r) => r.data)
}

export function updateProduct(id, data) {
  return http.put(`/api/products/${id}`, data).then((r) => r.data)
}

export function deleteProduct(id) {
  return http.delete(`/api/products/${id}`).then((r) => r.data)
}

export async function toggleProductActive(id, active) {
  try {
    const r = await http.patch(`/api/products/${id}/active`, { active })
    return r.data
  } catch (_) {}

  try {
    const r = await http.put(`/api/products/${id}`, { is_active: active })
    return r.data
  } catch (_) {}

  const r = await http.post(`/api/products/${id}/toggle_active`)
  return r.data
}

export function searchProductsApi(keyword) {
  return http
    .get('/api/products', {
      params: { page: 1, page_size: 50, active_only: true, q: keyword },
    })
    .then((r) => r.data)
}

export const listProductsApi = listProducts
export const getProductApi = (id) => http.get(`/api/products/${id}`).then((r) => r.data)

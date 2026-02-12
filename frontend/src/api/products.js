import http from './http'

// 列表（分页）
export function listProducts(params) {
  return http.get('/api/products', { params }).then((r) => r.data)
}

// 新增
export function createProduct(data) {
  return http.post('/api/products', data).then((r) => r.data)
}

// 更新
export function updateProduct(id, data) {
  return http.put(`/api/products/${id}`, data).then((r) => r.data)
}

/**
 * 启用/停用（多写法兼容）
 * 你页面如果传 (id, true/false) 都可以。
 */
export async function toggleProductActive(id, active) {
  // 1) PATCH /api/products/{id}/active  { active }
  try {
    const r = await http.patch(`/api/products/${id}/active`, { active })
    return r.data
  } catch (_) {}

  // 2) PUT /api/products/{id}  { is_active }
  try {
    const r = await http.put(`/api/products/${id}`, { is_active: active })
    return r.data
  } catch (_) {}

  // 3) POST /api/products/{id}/toggle_active
  const r = await http.post(`/api/products/${id}/toggle_active`)
  return r.data
}

// NewSale.vue：搜索商品
export function searchProductsApi(keyword) {
  return http
    .get('/api/products', {
      params: { page: 1, page_size: 50, active_only: true, q: keyword },
    })
    .then((r) => r.data)
}

// 兼容旧命名
export const listProductsApi = listProducts
export const getProductApi = (id) => http.get(`/api/products/${id}`).then((r) => r.data)

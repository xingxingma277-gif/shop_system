import http from './http'

export async function getLastPricing(params) {
  const res = await http.get('/api/pricing/last', { params })
  return res.data
}

export async function getLastPrice(params) {
  const res = await http.get('/api/pricing/last', { params })
  return res.data
}

export async function getPricingHistory(params) {
  const { customer_id, product_id, page = 1, page_size = 20, start_date, end_date } = params || {}
  if (!customer_id || !product_id) return { items: [], meta: { total: 0, page: 1, page_size: 20, pages: 0 } }
  try {
    const res = await http.get(`/api/customers/${customer_id}/products/${product_id}/price_history`, {
      params: { page, page_size, start_date, end_date },
    })
    return res.data
  } catch (e) {
    console.error('[getPricingHistory] failed:', e)
    return { items: [], meta: { total: 0, page: 1, page_size: 20, pages: 0 } }
  }
}

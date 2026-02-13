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
  const { customer_id, product_id, limit = 20 } = params || {}
  if (!customer_id || !product_id) return []
  try {
    const res = await http.get(`/api/customers/${customer_id}/products/${product_id}/price_history`, {
      params: { limit },
    })
    return res.data?.items || []
  } catch (e) {
    console.error('[getPricingHistory] failed:', e)
    return []
  }
}

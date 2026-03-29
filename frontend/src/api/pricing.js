import http from './http'

export async function getLatestDealPrice(params) {
  const { customer_id, product_id } = params || {}
  if (!customer_id || !product_id) return null

  try {
    const res = await http.get('/api/pricing/last-price', { params: { customer_id, product_id } })
    return res.data || null
  } catch (error) {
    return null
  }
}

export async function getPricingHistory(params) {
  const { customer_id, product_id, page = 1, page_size = 20, start_date, end_date } = params || {}
  if (!customer_id || !product_id) return { items: [], meta: { total: 0, page: 1, page_size: 20, pages: 0 } }

  try {
    const res = await http.get('/api/pricing/history', {
      params: { customer_id, product_id, page, page_size, start_date, end_date }
    })
    return res.data
  } catch (error) {
    return { items: [], meta: { total: 0, page: 1, page_size: 20, pages: 0 } }
  }
}

export const getLastPricing = getLatestDealPrice
export const getLastPrice = getLatestDealPrice

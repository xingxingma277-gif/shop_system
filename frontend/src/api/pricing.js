import http from './http'

/**
 * 获取某个客户+商品的“最近成交价/最新报价”
 * 后端若不是这个路由，请按 Swagger 实际路径改这里
 */
export async function getLastPricing(params) {
  const res = await http.get('/api/pricing/last', { params })
  return res.data
}

/**
 * 兼容旧命名：NewSale.vue 之前也可能用过 getLastPrice
 */
export async function getLastPrice(params) {
  const res = await http.get('/api/pricing/last', { params })
  return res.data
}

/**
 * ✅ 关键：NewSale.vue 需要的导出
 * 获取定价历史（成交/报价历史）
 *
 * NewSale.vue 里调用方式是：
 *   getPricingHistory(customerId, productId)
 * 所以这里按这个签名实现。
 *
 * 返回值：必须是数组（NewSale.vue 里直接 history.map / v-for）
 */
export async function getPricingHistory(customerId, productId, limit = 20) {
  try {
    const res = await http.get('/api/pricing/history', {
      params: {
        customer_id: customerId,
        product_id: productId,
        limit,
      },
    })

    // 兼容多种后端返回结构
    const data = res.data
    if (Array.isArray(data)) return data
    if (data && Array.isArray(data.items)) return data.items
    if (data && Array.isArray(data.history)) return data.history

    return []
  } catch (e) {
    // 关键：不让前端因异常直接白屏
    console.error('[getPricingHistory] failed:', e)
    return []
  }
}

import dayjs from 'dayjs'

/** 本地时间 ISO（不带 Z），用于后端录入/显示更直观 */
export function nowIsoLocal() {
  return dayjs().format('YYYY-MM-DDTHH:mm:ss')
}

/** 日期格式化：NewSale.vue 需要的 d */
export function d(value, fmt = 'YYYY-MM-DD') {
  if (!value) return ''
  return dayjs(value).format(fmt)
}

/** 金额格式化：Products.vue / NewSale.vue 常用 */
export function money(value, digits = 2) {
  const n = Number(value)
  if (Number.isNaN(n)) return '0.00'
  return n.toFixed(digits)
}

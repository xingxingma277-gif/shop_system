import dayjs from 'dayjs'

export function nowIsoLocal() {
  return dayjs().format('YYYY-MM-DDTHH:mm:ss')
}

export function d(value, fmt = 'YYYY-MM-DD') {
  if (!value) return ''
  return dayjs(value).format(fmt)
}

export function money(value, digits = 2) {
  const n = Number(value)
  if (Number.isNaN(n)) return '0.00'
  return n.toFixed(digits)
}

export function formatDateTime(value, fmt = 'YYYY-MM-DD HH:mm') {
  if (!value) return '-'
  return dayjs(value).format(fmt)
}

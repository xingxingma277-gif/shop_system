import dayjs from 'dayjs'
import utc from 'dayjs/plugin/utc'

dayjs.extend(utc)

function parseBizDateTime(value) {
  if (!value) return null
  if (typeof value === 'string') {
    const hasTimezone = /([zZ]|[+-]\d{2}:?\d{2})$/.test(value)
    if (hasTimezone) return dayjs(value)
    // backend SQLite may return UTC naive string, treat as UTC then convert local
    return dayjs.utc(value).local()
  }
  return dayjs(value)
}

export function nowIsoLocal() {
  return dayjs().format('YYYY-MM-DDTHH:mm:ss')
}

export function d(value, fmt = 'YYYY-MM-DD') {
  const dt = parseBizDateTime(value)
  if (!dt || !dt.isValid()) return ''
  return dt.format(fmt)
}

export function money(value, digits = 2) {
  const n = Number(value)
  if (Number.isNaN(n)) return '0.00'
  return n.toFixed(digits)
}

export function formatDateTime(value, fmt = 'YYYY-MM-DD HH:mm') {
  const dt = parseBizDateTime(value)
  if (!dt || !dt.isValid()) return '-'
  return dt.format(fmt)
}

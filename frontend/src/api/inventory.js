import http from './http'

export function listInventoryLedger(params) {
  return http.get('/api/inventory/ledger', { params }).then((r) => r.data)
}

export function listInventoryChecks(params) {
  return http.get('/api/inventory/checks', { params }).then((r) => r.data)
}

export function createInventoryCheck(data) {
  return http.post('/api/inventory/checks', data).then((r) => r.data)
}

export function postInventoryCheck(id) {
  return http.post(`/api/inventory/checks/${id}/post`).then((r) => r.data)
}

export function listInventoryTransfers(params) {
  return http.get('/api/inventory/transfers', { params }).then((r) => r.data)
}

export function createInventoryTransfer(data) {
  return http.post('/api/inventory/transfers', data).then((r) => r.data)
}

export function postInventoryTransfer(id) {
  return http.post(`/api/inventory/transfers/${id}/post`).then((r) => r.data)
}

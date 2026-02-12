import http from './http'

export function listContacts(customerId, { page = 1, page_size = 20 } = {}) {
  return http.get(`/api/customers/${customerId}/contacts`, { params: { page, page_size } }).then((r) => r.data)
}

export function createContact(customerId, payload) {
  return http.post(`/api/customers/${customerId}/contacts`, payload).then((r) => r.data)
}

export function updateContact(contactId, payload) {
  return http.patch(`/api/contacts/${contactId}`, payload).then((r) => r.data)
}

export function toggleContact(contactId) {
  return http.post(`/api/contacts/${contactId}/toggle_active`).then((r) => r.data)
}

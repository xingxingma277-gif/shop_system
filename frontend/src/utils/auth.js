const TOKEN_KEY = 'shop:auth_token'
const AUTH_USER_KEY = 'shop:auth_user'
const DISPLAY_NAME_KEY = 'shop:auth_display_name'
const AUTH_INFO_KEY = 'shop:auth_info'

export function getAuthToken() {
  return localStorage.getItem(TOKEN_KEY)
}

export function getStoredAuth() {
  const raw = localStorage.getItem(AUTH_INFO_KEY)
  if (!raw) return null
  try {
    return JSON.parse(raw)
  } catch (err) {
    return null
  }
}

export function setStoredAuth(token, user) {
  localStorage.setItem(TOKEN_KEY, token)
  localStorage.setItem(AUTH_USER_KEY, user?.username || '')
  localStorage.setItem(DISPLAY_NAME_KEY, user?.display_name || '')
  localStorage.setItem(AUTH_INFO_KEY, JSON.stringify(user || null))
}

export function clearStoredAuth() {
  localStorage.removeItem(TOKEN_KEY)
  localStorage.removeItem(AUTH_USER_KEY)
  localStorage.removeItem(DISPLAY_NAME_KEY)
  localStorage.removeItem(AUTH_INFO_KEY)
}

export function hasPermission(code) {
  if (!code) return true
  const auth = getStoredAuth()
  if (!auth) return false
  if (auth.is_superuser) return true
  return (auth.permission_codes || []).includes(code)
}

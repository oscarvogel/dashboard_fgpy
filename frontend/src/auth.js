import { reactive } from 'vue'

// Simple auth state and helpers. Uses session-based auth (cookies).
// Expects backend endpoints:
// POST /api/login/    -> body: { username, password } (sets session cookie)
// POST /api/logout/   -> signs out
// GET  /api/user/     -> returns current user or 401 when not authenticated

// The base URL for API requests can be configured with Vite env var VITE_API_BASE.
// - In development we typically proxy `/api` to the backend (so default is '/api').
// - In production set VITE_API_BASE to the full backend base (for example
//   'https://api.example.com/api') so requests are sent to the correct host.
const RAW_API_BASE = import.meta.env?.VITE_API_BASE
const API_BASE = (RAW_API_BASE || '/api').replace(/\/$/, '')

const state = reactive({ user: null })
let csrfTokenCache = ''

export function getCookie(name) {
  const value = `; ${document.cookie}`
  const parts = value.split(`; ${name}=`)
  if (parts.length === 2) return decodeURIComponent(parts.pop().split(';').shift())
  return ''
}

export async function ensureCsrfToken(forceRefresh = false) {
  let token = csrfTokenCache || getCookie('csrftoken')
  if (!token || forceRefresh) {
    const res = await fetch(`${API_BASE}/csrf/`, { credentials: 'include', cache: 'no-store' })
    const data = await res.json().catch(() => ({}))
    token = data.csrfToken || getCookie('csrftoken') || ''
    csrfTokenCache = token
  }
  return token
}

export async function csrfFetch(url, options = {}) {
  const method = (options.method || 'GET').toUpperCase()
  const buildRequest = async (forceRefresh = false) => {
    const headers = new Headers(options.headers || {})

    if (!['GET', 'HEAD', 'OPTIONS', 'TRACE'].includes(method)) {
      const token = await ensureCsrfToken(forceRefresh)
      if (token) headers.set('X-CSRFToken', token)
    }

    return fetch(url, {
      ...options,
      credentials: options.credentials || 'include',
      headers,
      cache: options.cache || 'no-store',
    })
  }

  let res = await buildRequest(!['GET', 'HEAD', 'OPTIONS', 'TRACE'].includes(method))
  if (res.status === 403 && !['GET', 'HEAD', 'OPTIONS', 'TRACE'].includes(method)) {
    res = await buildRequest(true)
  }
  return res
}

export function isAuthenticated() {
  return !!state.user
}

export async function fetchCurrentUser() {
  try {
  const res = await fetch(`${API_BASE}/user/`, { credentials: 'include' })
    if (!res.ok) {
      state.user = null
      throw new Error('Not authenticated')
    }
    state.user = await res.json()
    return state.user
  } catch (err) {
    state.user = null
    throw err
  }
}

export async function login(username, password) {
  const res = await csrfFetch(`${API_BASE}/login/`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ username, password }),
  })
  if (!res.ok) {
    const data = await res.json().catch(() => ({}))
    throw {
      ...data,
      status: res.status,
      statusText: res.statusText,
    }
  }
  return fetchCurrentUser()
}

export async function logout() {
  try {
  await csrfFetch(`${API_BASE}/logout/`, { method: 'POST' })
  } finally {
    state.user = null
  }
}

export function useAuth() {
  return { state, isAuthenticated, fetchCurrentUser, login, logout }
}

export default { state, isAuthenticated, fetchCurrentUser, login, logout }

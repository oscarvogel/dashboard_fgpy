import assert from 'node:assert/strict'
import { afterEach, test } from 'node:test'

import { csrfFetch, ensureCsrfToken, fetchCurrentUser, getCookie, useAuth } from '../src/auth.js'

const originalDocument = globalThis.document
const originalFetch = globalThis.fetch

afterEach(() => {
  globalThis.document = originalDocument
  globalThis.fetch = originalFetch
})

function setCookie(value) {
  globalThis.document = { cookie: value }
}

test('getCookie returns decoded cookie value by name', () => {
  setCookie('sessionid=abc; csrftoken=token%20123; theme=dark')

  assert.equal(getCookie('csrftoken'), 'token 123')
})

test('getCookie returns an empty string when cookie is missing', () => {
  setCookie('sessionid=abc')

  assert.equal(getCookie('csrftoken'), '')
})

test('ensureCsrfToken reuses an existing csrf cookie', async () => {
  setCookie('csrftoken=existing-token')
  let calls = 0
  globalThis.fetch = async () => {
    calls += 1
    return { ok: true }
  }

  const token = await ensureCsrfToken()

  assert.equal(token, 'existing-token')
  assert.equal(calls, 0)
})

test('ensureCsrfToken fetches csrf endpoint when cookie is missing', async () => {
  setCookie('')
  globalThis.fetch = async (url, options) => {
    assert.equal(url, '/api/csrf/')
    assert.deepEqual(options, { credentials: 'include', cache: 'no-store' })
    setCookie('csrftoken=fetched-token')
    return { ok: true, json: async () => ({ csrfToken: 'fetched-token' }) }
  }

  const token = await ensureCsrfToken()

  assert.equal(token, 'fetched-token')
})

test('csrfFetch adds X-CSRFToken to mutating requests', async () => {
  setCookie('csrftoken=post-token')
  let calls = 0
  globalThis.fetch = async (url, options) => {
    calls += 1
    if (calls === 1) {
      assert.equal(url, '/api/csrf/')
      assert.deepEqual(options, { credentials: 'include', cache: 'no-store' })
      return { ok: true, json: async () => ({ csrfToken: 'post-token' }) }
    }

    assert.equal(url, '/api/login/')
    assert.equal(options.method, 'POST')
    assert.equal(options.credentials, 'include')
    assert.equal(options.cache, 'no-store')
    assert.equal(options.headers.get('X-CSRFToken'), 'post-token')
    assert.equal(options.headers.get('Content-Type'), 'application/json')
    return { ok: true }
  }

  await csrfFetch('/api/login/', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: '{}',
  })
  assert.equal(calls, 2)
})

test('csrfFetch adds X-CSRFToken to delete requests', async () => {
  setCookie('csrftoken=delete-token')
  let calls = 0
  globalThis.fetch = async (url, options) => {
    calls += 1
    if (calls === 1) {
      assert.equal(url, '/api/csrf/')
      return { ok: true, json: async () => ({ csrfToken: 'delete-token' }) }
    }

    assert.equal(url, '/api/produccion/42/')
    assert.equal(options.method, 'DELETE')
    assert.equal(options.credentials, 'include')
    assert.equal(options.cache, 'no-store')
    assert.equal(options.headers.get('X-CSRFToken'), 'delete-token')
    return { ok: true }
  }

  await csrfFetch('/api/produccion/42/', { method: 'DELETE' })
  assert.equal(calls, 2)
})

test('csrfFetch does not add X-CSRFToken to safe requests', async () => {
  setCookie('csrftoken=get-token')
  globalThis.fetch = async (url, options) => {
    assert.equal(url, '/api/user/')
    assert.equal(options.credentials, 'include')
    assert.equal(options.headers.has('X-CSRFToken'), false)
    return { ok: true }
  }

  await csrfFetch('/api/user/')
})

test('fetchCurrentUser stores the authenticated user', async () => {
  setCookie('')
  globalThis.fetch = async (url, options) => {
    assert.equal(url, '/api/user/')
    assert.deepEqual(options, { credentials: 'include' })
    return {
      ok: true,
      json: async () => ({ username: 'fgpy' }),
    }
  }

  const user = await fetchCurrentUser()

  assert.deepEqual(user, { username: 'fgpy' })
  assert.deepEqual(useAuth().state.user, { username: 'fgpy' })
})

test('fetchCurrentUser clears user when session is not authenticated', async () => {
  useAuth().state.user = { username: 'fgpy' }
  globalThis.fetch = async () => ({ ok: false })

  await assert.rejects(fetchCurrentUser(), /Not authenticated/)

  assert.equal(useAuth().state.user, null)
})

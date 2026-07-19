const state = {
  activeRequests: 0,
  activeScopes: new Set(),
  installed: false,
  baseline: new Map(),
}

const CONTROL_SELECTOR = 'input, select, textarea, [contenteditable="true"]'
const COMMIT_BUTTON_TEXT = /consultar|aplicar|guardar|entrar|enviar|limpiar|cancelar|cambiar|exportar/i

function emitBusyChange() {
  window.dispatchEvent(new CustomEvent('fgpy:update-activity-change', {
    detail: getUpdateActivityState(),
  }))
}

function getControlKey(control, index) {
  return control.id || control.name || control.getAttribute('aria-label') || `${control.tagName.toLowerCase()}-${index}`
}

function getControlValue(control) {
  if (control.type === 'checkbox' || control.type === 'radio') {
    return control.checked ? '1' : '0'
  }
  return control.value ?? control.textContent ?? ''
}

function snapshotControls() {
  state.baseline.clear()
  document.querySelectorAll(CONTROL_SELECTOR).forEach((control, index) => {
    state.baseline.set(getControlKey(control, index), getControlValue(control))
  })
}

function hasDirtyControl() {
  let dirty = false
  document.querySelectorAll(CONTROL_SELECTOR).forEach((control, index) => {
    if (dirty) return
    const key = getControlKey(control, index)
    if (!state.baseline.has(key)) return
    dirty = state.baseline.get(key) !== getControlValue(control)
  })
  return dirty
}

function hasFocusedEditor() {
  const active = document.activeElement
  return !!active && active !== document.body && active.matches?.(CONTROL_SELECTOR)
}

function hasVisibleModal() {
  return !!document.querySelector('[role="dialog"], .fixed.inset-0')
}

function hasActiveTripMarker() {
  if (state.activeScopes.has('trip') || state.activeScopes.has('viaje')) return true

  for (const storage of [window.localStorage, window.sessionStorage]) {
    try {
      for (let index = 0; index < storage.length; index += 1) {
        const key = storage.key(index) || ''
        if (!/(viaje|trip)/i.test(key)) continue
        const value = storage.getItem(key) || ''
        if (/^(1|true|active|activo|en_curso)$/i.test(value)) return true
      }
    } catch {
      return false
    }
  }
  return false
}

export function getUpdateActivityState() {
  const loading = state.activeRequests > 0
  const editing = hasFocusedEditor() || hasDirtyControl()
  const modal = hasVisibleModal()
  const trip = hasActiveTripMarker()

  return {
    loading,
    editing,
    modal,
    trip,
    busy: loading || editing || modal || trip,
  }
}

export function setUpdateActivityScope(scope, active = true) {
  if (active) {
    state.activeScopes.add(scope)
  } else {
    state.activeScopes.delete(scope)
  }
  emitBusyChange()
}

export function installUpdateActivityTracker() {
  if (state.installed || typeof window === 'undefined') return
  state.installed = true

  const originalFetch = window.fetch?.bind(window)
  if (originalFetch) {
    window.fetch = async (...args) => {
      state.activeRequests += 1
      emitBusyChange()
      try {
        return await originalFetch(...args)
      } finally {
        state.activeRequests = Math.max(0, state.activeRequests - 1)
        emitBusyChange()
      }
    }
  }

  window.fgpyUpdateActivity = {
    set: setUpdateActivityScope,
    snapshot: snapshotControls,
    state: getUpdateActivityState,
  }

  window.addEventListener('load', () => {
    window.setTimeout(snapshotControls, 0)
  })
  window.addEventListener('focusin', emitBusyChange)
  window.addEventListener('focusout', () => window.setTimeout(emitBusyChange, 0))
  window.addEventListener('input', emitBusyChange, true)
  window.addEventListener('change', emitBusyChange, true)
  window.addEventListener('submit', () => window.setTimeout(snapshotControls, 1200), true)
  window.addEventListener('click', (event) => {
    const button = event.target?.closest?.('button')
    if (!button || !COMMIT_BUTTON_TEXT.test(button.textContent || '')) return
    window.setTimeout(snapshotControls, 1200)
  }, true)

  snapshotControls()
}

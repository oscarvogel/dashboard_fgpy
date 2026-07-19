<template>
  <div
    v-if="visible"
    class="fixed inset-x-0 bottom-0 z-[70] px-3 pb-3 sm:px-5 sm:pb-5"
    role="status"
    aria-live="polite"
  >
    <div class="mx-auto max-w-4xl overflow-hidden rounded-md border border-slate-200 bg-white shadow-xl shadow-slate-900/15">
      <div class="flex flex-col gap-3 border-l-4 px-4 py-3 sm:flex-row sm:items-center sm:justify-between sm:px-5" :class="borderClass">
        <div class="min-w-0">
          <p class="text-sm font-semibold text-slate-900">{{ title }}</p>
          <p class="mt-0.5 text-sm text-slate-600">{{ message }}</p>
        </div>

        <div class="flex shrink-0 items-center gap-2">
          <button
            v-if="mode === 'manual'"
            type="button"
            class="fg-btn-secondary fg-btn-sm"
            @click="snooze"
          >
            Mas tarde
          </button>
          <button
            type="button"
            class="fg-btn-primary fg-btn-sm"
            @click="reloadNow"
          >
            Actualizar
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import { computed, onBeforeUnmount, onMounted, ref } from 'vue'
import { getUpdateActivityState } from '../updateActivity'

const CHECK_INTERVAL_MS = 30 * 60 * 1000
const SNOOZE_MS = 30 * 60 * 1000
const COUNTDOWN_SECONDS = 30

function getIndexUrl() {
  const base = (import.meta.env.BASE_URL || '/').replace(/\/?$/, '/')
  return new URL(`${base}index.html`, window.location.origin).toString()
}

function extractVersionFingerprint(html) {
  const assets = [...html.matchAll(/(?:src|href)="([^"]*\/assets\/[^"]+\.(?:js|css))"/g)]
    .map(match => match[1])
    .sort()

  return assets.length ? assets.join('|') : html.replace(/\s+/g, ' ').trim()
}

export default {
  name: 'AppUpdatePrompt',
  setup() {
    const enabled = import.meta.env.PROD || import.meta.env.VITE_ENABLE_UPDATE_CHECK === 'true'
    const baseline = ref('')
    const updateFound = ref(false)
    const visible = ref(false)
    const mode = ref('')
    const countdown = ref(COUNTDOWN_SECONDS)
    const snoozedUntil = ref(0)

    let checkTimer = null
    let countdownTimer = null

    const title = computed(() => {
      if (mode.value === 'auto') return `Nueva version lista en ${countdown.value}s`
      return 'Hay una nueva version disponible'
    })

    const message = computed(() => {
      if (mode.value === 'auto') return 'No detectamos carga, edicion, modal ni viaje activo. La app se actualizara sola.'
      return 'Detectamos trabajo en pantalla. Podes actualizar ahora o dejarlo para mas tarde.'
    })

    const borderClass = computed(() => mode.value === 'auto' ? 'border-l-green-500' : 'border-l-amber-500')

    async function fetchFingerprint() {
      const response = await fetch(`${getIndexUrl()}?fgpy_update=${Date.now()}`, {
        cache: 'no-store',
        headers: {
          'Cache-Control': 'no-cache',
          Pragma: 'no-cache',
        },
      })
      if (!response.ok) throw new Error('No se pudo chequear la version de la app.')
      return extractVersionFingerprint(await response.text())
    }

    function clearCountdown() {
      if (countdownTimer) {
        window.clearInterval(countdownTimer)
        countdownTimer = null
      }
    }

    function reloadNow() {
      clearCountdown()
      window.location.reload()
    }

    function showManual() {
      clearCountdown()
      mode.value = 'manual'
      visible.value = true
    }

    function showCountdown() {
      if (mode.value === 'auto' && visible.value) return

      clearCountdown()
      mode.value = 'auto'
      visible.value = true
      countdown.value = COUNTDOWN_SECONDS
      countdownTimer = window.setInterval(() => {
        if (getUpdateActivityState().busy) {
          showManual()
          return
        }

        countdown.value -= 1
        if (countdown.value <= 0) reloadNow()
      }, 1000)
    }

    function presentUpdate() {
      if (!updateFound.value || document.visibilityState !== 'visible') return
      if (Date.now() < snoozedUntil.value) return

      if (getUpdateActivityState().busy) {
        showManual()
      } else {
        showCountdown()
      }
    }

    async function checkForUpdate() {
      if (!enabled || !navigator.onLine) return

      try {
        const fingerprint = await fetchFingerprint()
        if (!baseline.value) {
          baseline.value = fingerprint
          return
        }

        if (fingerprint !== baseline.value) {
          updateFound.value = true
          presentUpdate()
        }
      } catch (error) {
        console.debug('Chequeo de actualizacion pendiente:', error)
      }
    }

    function snooze() {
      visible.value = false
      mode.value = ''
      snoozedUntil.value = Date.now() + SNOOZE_MS
      clearCountdown()
    }

    function handleVisibility() {
      if (document.visibilityState !== 'visible') return
      if (updateFound.value) {
        presentUpdate()
      } else {
        checkForUpdate()
      }
    }

    function handleActivityChange() {
      if (!updateFound.value || !visible.value || Date.now() < snoozedUntil.value) return
      presentUpdate()
    }

    onMounted(() => {
      if (!enabled) return

      checkForUpdate()
      checkTimer = window.setInterval(checkForUpdate, CHECK_INTERVAL_MS)
      window.addEventListener('online', checkForUpdate)
      window.addEventListener('focus', handleVisibility)
      window.addEventListener('pageshow', handleVisibility)
      document.addEventListener('visibilitychange', handleVisibility)
      window.addEventListener('fgpy:update-activity-change', handleActivityChange)
    })

    onBeforeUnmount(() => {
      if (checkTimer) window.clearInterval(checkTimer)
      clearCountdown()
      window.removeEventListener('online', checkForUpdate)
      window.removeEventListener('focus', handleVisibility)
      window.removeEventListener('pageshow', handleVisibility)
      document.removeEventListener('visibilitychange', handleVisibility)
      window.removeEventListener('fgpy:update-activity-change', handleActivityChange)
    })

    return {
      visible,
      mode,
      title,
      message,
      borderClass,
      reloadNow,
      snooze,
    }
  },
}
</script>

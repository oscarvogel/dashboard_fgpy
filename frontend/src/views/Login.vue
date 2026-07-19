<template>
  <div class="min-h-screen flex items-center justify-center bg-gray-100">
    <div class="fg-card w-full max-w-md p-8">
      <div class="flex justify-center mb-6">
        <img src="@/assets/imagenes/fgpy.png" alt="FGPY Logo" class="h-24 w-auto" />
      </div>
      <h2 class="text-xl font-bold mb-4 text-center">Iniciar sesión</h2>
      <form @submit.prevent="onSubmit" class="space-y-4">
        <div>
          <label for="login-username" class="block text-sm font-medium text-gray-700">Usuario</label>
          <input
            id="login-username"
            name="username"
            v-model="username"
            type="text"
            required
            autocomplete="username"
            class="fg-input mt-1 block w-full"
          />
        </div>
        <div>
          <label for="login-password" class="block text-sm font-medium text-gray-700">Contraseña</label>
          <div class="relative mt-1">
            <input
              id="login-password"
              name="password"
              v-model="password"
              :type="showPassword ? 'text' : 'password'"
              required
              autocomplete="current-password"
              class="fg-input block w-full pr-10"
            />
            <button
              type="button"
              class="absolute inset-y-0 right-0 flex items-center px-3 text-gray-500 hover:text-gray-700 focus:outline-none focus:ring-2 focus:ring-green-200"
              :aria-label="showPassword ? 'Ocultar contraseña' : 'Mostrar contraseña'"
              @click="showPassword = !showPassword"
            >
              <svg v-if="!showPassword" xmlns="http://www.w3.org/2000/svg" class="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M2.25 12s3.75-6.75 9.75-6.75S21.75 12 21.75 12 18 18.75 12 18.75 2.25 12 2.25 12z" />
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 15a3 3 0 100-6 3 3 0 000 6z" />
              </svg>
              <svg v-else xmlns="http://www.w3.org/2000/svg" class="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M3 3l18 18" />
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M10.58 10.58A2 2 0 0012 14a2 2 0 001.42-3.42" />
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9.88 5.55A8.77 8.77 0 0112 5.25c6 0 9.75 6.75 9.75 6.75a17.7 17.7 0 01-2.46 3.22" />
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6.15 6.67C3.72 8.37 2.25 12 2.25 12s3.75 6.75 9.75 6.75a8.8 8.8 0 004.08-.98" />
              </svg>
            </button>
          </div>
        </div>
        <div>
          <button type="submit" class="fg-btn-primary w-full">Entrar</button>
        </div>
        <p v-if="error" role="alert" class="text-red-600 text-sm">{{ error }}</p>
      </form>
    </div>
  </div>
</template>

<script>
import { ref } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { login } from '../auth'

export default {
  name: 'Login',
  setup() {
    const router = useRouter()
    const route = useRoute()
    const username = ref('')
    const password = ref('')
    const showPassword = ref(false)
    const error = ref(null)

    async function onSubmit(event) {
      error.value = null
      try {
        const form = event?.target
        const formUsername = form?.elements?.username?.value ?? username.value
        const formPassword = form?.elements?.password?.value ?? password.value
        await login(formUsername, formPassword)
        const next = route.query.next || '/'
        router.push(next)
      } catch (err) {
        error.value = getLoginError(err)
      }
    }

    function getLoginError(err) {
      const detail = (err && (err.detail || err.message || err.error)) || ''
      if (err?.status === 403) {
        return 'No se pudo validar la sesión local (CSRF). Actualizá con Ctrl+F5 e intentá nuevamente.'
      }
      if (err?.status) {
        return `No pudimos iniciar sesión. Respuesta del servidor: ${err.status}${detail ? ` - ${detail}` : ''}`
      }
      const technicalMessages = ['Method Not Allowed', 'Not Found', 'Internal Server Error']
      if (!detail || technicalMessages.includes(detail)) {
        return 'No pudimos iniciar sesión. Revisá usuario y contraseña.'
      }
      return detail
    }

    return { username, password, showPassword, onSubmit, error }
  }
}
</script>

<style scoped>
/* Pequeño ajuste visual */
</style>

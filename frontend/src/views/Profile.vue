<template>
  <div class="min-h-screen bg-gray-50">
    <NavBar />
    <main class="mx-auto max-w-3xl px-4 py-4 sm:px-6 sm:py-6 lg:px-8">
      <div class="fg-card p-4 sm:p-6">
        <h2 class="text-xl font-semibold mb-4">Perfil de Usuario</h2>

        <div v-if="loading" class="text-gray-500">Cargando...</div>

        <form v-else @submit.prevent="onSave" class="space-y-4">
          <div>
            <label for="profile-username" class="block text-sm font-medium text-gray-700">Nombre de usuario</label>
            <input id="profile-username" v-model="form.username" class="fg-input mt-1 block w-full" />
          </div>

          <div>
            <label for="profile-email" class="block text-sm font-medium text-gray-700">Email</label>
            <input id="profile-email" v-model="form.email" type="email" class="fg-input mt-1 block w-full" />
          </div>

          <div class="flex flex-col gap-3 sm:flex-row sm:flex-wrap sm:items-center">
            <button :disabled="saving" type="submit" class="fg-btn-primary w-full sm:w-auto">Guardar</button>
            <button type="button" @click="onCancel" class="fg-btn-secondary w-full sm:w-auto">Cancelar</button>
            <span v-if="message" role="status" :class="messageClass">{{ message }}</span>
          </div>
        </form>
        <!-- Cambiar contraseña -->
        <div class="mt-6 rounded-md border border-gray-200 bg-gray-50 p-4">
          <h3 class="text-lg font-medium mb-3">Cambiar contraseña</h3>
          <form @submit.prevent="onChangePassword" class="space-y-3">
            <div>
              <label for="profile-current-password" class="block text-sm font-medium text-gray-700">Contraseña actual</label>
              <div class="relative mt-1">
                <input id="profile-current-password" v-model="pwd.current" :type="showCurrentPassword ? 'text' : 'password'" class="fg-input block w-full pr-10" />
                <button type="button" class="absolute inset-y-0 right-0 flex items-center px-3 text-gray-500 hover:text-gray-700 focus:outline-none focus:ring-2 focus:ring-green-200" :aria-label="showCurrentPassword ? 'Ocultar contraseña actual' : 'Mostrar contraseña actual'" @click="showCurrentPassword = !showCurrentPassword">
                  <svg v-if="!showCurrentPassword" xmlns="http://www.w3.org/2000/svg" class="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
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
              <label for="profile-new-password" class="block text-sm font-medium text-gray-700">Nueva contraseña</label>
              <div class="relative mt-1">
                <input id="profile-new-password" v-model="pwd.new" :type="showNewPassword ? 'text' : 'password'" class="fg-input block w-full pr-10" />
                <button type="button" class="absolute inset-y-0 right-0 flex items-center px-3 text-gray-500 hover:text-gray-700 focus:outline-none focus:ring-2 focus:ring-green-200" :aria-label="showNewPassword ? 'Ocultar nueva contraseña' : 'Mostrar nueva contraseña'" @click="showNewPassword = !showNewPassword">
                  <svg v-if="!showNewPassword" xmlns="http://www.w3.org/2000/svg" class="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
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
              <label for="profile-confirm-password" class="block text-sm font-medium text-gray-700">Confirmar nueva contraseña</label>
              <div class="relative mt-1">
                <input id="profile-confirm-password" v-model="pwd.confirm" :type="showConfirmPassword ? 'text' : 'password'" class="fg-input block w-full pr-10" />
                <button type="button" class="absolute inset-y-0 right-0 flex items-center px-3 text-gray-500 hover:text-gray-700 focus:outline-none focus:ring-2 focus:ring-green-200" :aria-label="showConfirmPassword ? 'Ocultar confirmación de contraseña' : 'Mostrar confirmación de contraseña'" @click="showConfirmPassword = !showConfirmPassword">
                  <svg v-if="!showConfirmPassword" xmlns="http://www.w3.org/2000/svg" class="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
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
            <div class="flex flex-col gap-3 sm:flex-row sm:flex-wrap sm:items-center">
              <button :disabled="pwdSaving" type="submit" class="fg-btn-amber w-full sm:w-auto">Cambiar contraseña</button>
              <button type="button" @click="onCancelPassword" class="fg-btn-secondary w-full sm:w-auto">Cancelar</button>
              <span v-if="pwdMessage" role="status" :class="pwdMessageClass">{{ pwdMessage }}</span>
            </div>
          </form>
        </div>
      </div>
    </main>
  </div>
</template>

<script>
import { ref, onMounted } from 'vue'
import NavBar from '../components/NavBar.vue'
import { csrfFetch, fetchCurrentUser } from '../auth'

const RAW_API_BASE = import.meta.env.VITE_API_BASE
const API_BASE = (RAW_API_BASE || '/api').replace(/\/$/, '')

export default {
  name: 'Profile',
  components: { NavBar },
  setup() {
    const loading = ref(true)
    const saving = ref(false)
    const form = ref({ username: '', email: '' })
    const message = ref('')
    const messageClass = ref('text-sm text-green-700')
    const pwd = ref({ current: '', new: '', confirm: '' })
    const showCurrentPassword = ref(false)
    const showNewPassword = ref(false)
    const showConfirmPassword = ref(false)
    const pwdSaving = ref(false)
    const pwdMessage = ref('')
    const pwdMessageClass = ref('text-sm text-green-700')

    async function load() {
      loading.value = true
      message.value = ''
      try {
        const res = await fetch(`${API_BASE}/user/`, { credentials: 'include' })
        if (!res.ok) throw new Error('No autenticado')
        const data = await res.json()
        form.value.username = data.username || ''
        form.value.email = data.email || ''
      } catch (err) {
        message.value = 'No se pudo cargar el perfil.'
        messageClass.value = 'text-sm text-red-600'
      } finally {
        loading.value = false
      }
    }

    async function onSave() {
      saving.value = true
      message.value = ''
      try {
        const res = await csrfFetch(`${API_BASE}/user/`, {
          method: 'PUT',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ username: form.value.username, email: form.value.email }),
        })
        if (!res.ok) {
          const err = await res.json().catch(() => ({}))
          throw err
        }
        // refresh auth state
        await fetchCurrentUser().catch(() => {})
        message.value = 'Perfil actualizado correctamente.'
        messageClass.value = 'text-sm text-green-700'
      } catch (err) {
        message.value = 'Error al guardar el perfil.'
        messageClass.value = 'text-sm text-red-600'
      } finally {
        saving.value = false
      }
    }

    function onCancel() {
      load()
    }

    async function onChangePassword() {
      pwdSaving.value = true
      pwdMessage.value = ''
      try {
        if (!pwd.value.current || !pwd.value.new || !pwd.value.confirm) {
          throw new Error('Complete todos los campos')
        }
        if (pwd.value.new !== pwd.value.confirm) {
          throw new Error('Las nuevas contraseñas no coinciden')
        }

        const res = await csrfFetch(`${API_BASE}/user/password/`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ current_password: pwd.value.current, new_password: pwd.value.new, new_password_confirm: pwd.value.confirm }),
        })

        if (!res.ok) {
          const data = await res.json().catch(() => ({}))
          throw new Error((data && data.detail) || 'Error al cambiar la contraseña')
        }

        // keep auth state in sync
        await fetchCurrentUser().catch(() => {})
        pwdMessage.value = 'Contraseña cambiada correctamente.'
        pwdMessageClass.value = 'text-sm text-green-700'
        pwd.value.current = ''
        pwd.value.new = ''
        pwd.value.confirm = ''
      } catch (err) {
        pwdMessage.value = err && err.message ? err.message : 'Error al cambiar la contraseña.'
        pwdMessageClass.value = 'text-sm text-red-600'
      } finally {
        pwdSaving.value = false
      }
    }

    function onCancelPassword() {
      pwd.value.current = ''
      pwd.value.new = ''
      pwd.value.confirm = ''
      pwdMessage.value = ''
    }

    onMounted(load)

    return {
      loading,
      saving,
      form,
      onSave,
      onCancel,
      message,
      messageClass,
      // password change bindings
      pwd,
      pwdSaving,
      showCurrentPassword,
      showNewPassword,
      showConfirmPassword,
      pwdMessage,
      pwdMessageClass,
      onChangePassword,
      onCancelPassword,
    }
  },
}
</script>

<style scoped>
/* small spacing tweaks if needed */
</style>


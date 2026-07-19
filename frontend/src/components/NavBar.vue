<template>
  <nav class="bg-green-700 shadow-lg">
    <div class="mx-auto max-w-7xl px-4 py-3 sm:px-6 lg:px-8">
      <div class="flex items-center justify-between gap-3 md:hidden">
        <router-link to="/" class="flex min-w-0 items-center space-x-2">
          <img src="@/assets/imagenes/fgpy.png" alt="FGPY" class="h-8 w-auto shrink-0" />
          <span class="truncate text-lg font-semibold text-white">FGPY</span>
        </router-link>
        <button
          type="button"
          class="fg-btn bg-green-800 px-3 text-white hover:bg-green-900 focus:ring-green-300"
          :aria-expanded="menuOpen"
          aria-controls="mobile-nav-menu"
          aria-label="Abrir navegación"
          @click="menuOpen = !menuOpen"
        >
          <svg class="h-5 w-5" viewBox="0 0 24 24" fill="none" stroke="currentColor" aria-hidden="true">
            <path v-if="!menuOpen" stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 7h16M4 12h16M4 17h16" />
            <path v-else stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 6l12 12M18 6L6 18" />
          </svg>
        </button>
      </div>

      <div
        id="mobile-nav-menu"
        :class="[menuOpen ? 'flex' : 'hidden', 'mt-3 flex-col gap-3 md:mt-0 md:flex md:flex-row md:items-center md:justify-between']"
      >
        <div class="flex flex-col gap-2 md:flex-row md:flex-wrap md:items-center md:gap-x-6 md:gap-y-3">
          <router-link to="/" class="hidden items-center space-x-2 md:flex">
            <img src="@/assets/imagenes/fgpy.png" alt="FGPY" class="h-8 w-auto" />
            <span class="text-lg font-semibold text-white">FGPY</span>
          </router-link>
          <router-link
            v-for="item in links"
            :key="item.to"
            :to="item.to"
            class="rounded-md px-2 py-2 text-sm text-green-100 transition-colors hover:bg-green-800 hover:text-white md:px-0 md:py-0 md:hover:bg-transparent"
            exact-active-class="font-semibold text-white underline underline-offset-4"
            @click="closeMenu"
          >
            {{ item.label }}
          </router-link>
        </div>

        <div class="flex flex-col gap-2 border-t border-green-600 pt-3 md:flex-row md:items-center md:justify-end md:border-t-0 md:pt-0">
          <span v-if="user" class="truncate text-sm text-green-100 md:max-w-40">{{ userDisplay }}</span>
          <button
            type="button"
            class="fg-btn w-full bg-green-800 text-white hover:bg-green-900 focus:ring-green-300 md:w-auto"
            :aria-pressed="isDarkMode"
            :aria-label="isDarkMode ? 'Cambiar a modo claro' : 'Cambiar a modo oscuro'"
            @click="toggleTheme"
          >
            {{ isDarkMode ? 'Modo claro' : 'Modo oscuro' }}
          </button>
          <button
            type="button"
            class="fg-btn w-full bg-green-800 text-white hover:bg-green-900 focus:ring-green-300 md:w-auto"
            @click="onLogout"
          >
            Cerrar sesión
          </button>
        </div>
      </div>
    </div>
  </nav>
</template>

<script>
import { computed, ref } from 'vue'
import { useRouter } from 'vue-router'
import { useAuth } from '../auth'

export default {
  name: 'NavBar',
  props: {
    user: { type: Object, required: false },
  },
  setup(props) {
    const router = useRouter()
    const { state, logout } = useAuth()
    const user = computed(() => props.user || state.user)
    const userDisplay = computed(() => (user.value ? user.value.username || user.value.email || 'Usuario' : ''))
    const isDarkMode = ref(document.documentElement.classList.contains('dark'))
    const menuOpen = ref(false)
    const links = [
      { to: '/', label: 'Producción' },
      { to: '/resumen', label: 'Resumen' },
      { to: '/combustible', label: 'Combustible' },
      { to: '/profile', label: 'Perfil' },
    ]

    function closeMenu() {
      menuOpen.value = false
    }

    function toggleTheme() {
      isDarkMode.value = !isDarkMode.value
      document.documentElement.classList.toggle('dark', isDarkMode.value)
      localStorage.setItem('fgpy-theme', isDarkMode.value ? 'dark' : 'light')
    }

    async function onLogout() {
      await logout()
      router.push('/login')
    }

    return { user, userDisplay, isDarkMode, menuOpen, links, closeMenu, toggleTheme, onLogout }
  },
}
</script>

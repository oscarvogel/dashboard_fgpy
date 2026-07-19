<template>
  <aside class="fg-panel-accent p-4 sm:p-5">
    <h3 class="text-lg font-semibold mb-4 text-green-700">Filtros</h3>
    <p class="mb-4 text-xs text-gray-600">Los cambios se aplican al presionar Aplicar Filtros.</p>

    <div class="space-y-4">
      <div>
        <label for="filter-fecha-desde" class="block text-sm font-medium text-gray-700 mb-1">Fecha Desde</label>
        <input
          id="filter-fecha-desde"
          v-model="filters.fecha_desde"
          type="date"
          class="fg-input w-full"
          @change="onDateChange"
        />
      </div>

      <div>
        <label for="filter-fecha-hasta" class="block text-sm font-medium text-gray-700 mb-1">Fecha Hasta</label>
        <input
          id="filter-fecha-hasta"
          v-model="filters.fecha_hasta"
          type="date"
          class="fg-input w-full"
          @change="onDateChange"
        />
      </div>

      <div>
        <label for="filter-unidad" class="block text-sm font-medium text-gray-700 mb-1">Unidad de Negocio</label>
        <select
          id="filter-unidad"
          v-model="filters.unidad_negocio_id"
          class="fg-input w-full"
          @change="onUnidadChange"
        >
          <option value="">Todas</option>
          <option v-for="unidad in unidades" :key="unidad.id" :value="unidad.id">
            {{ unidad.descripcion }}
          </option>
        </select>
      </div>

      <div>
        <label for="filter-tipo-operacion" class="block text-sm font-medium text-gray-700 mb-1">Tipo de Operación</label>
        <select
          id="filter-tipo-operacion"
          v-model="filters.tipo_operacion_id"
          class="fg-input w-full"
          @change="handleFilterChange"
          :disabled="!filters.unidad_negocio_id"
        >
          <option value="">{{ filters.unidad_negocio_id ? 'Todos' : 'Seleccione una unidad primero' }}</option>
          <option v-for="tipo in tiposOperacion" :key="tipo.id" :value="tipo.id">
            {{ tipo.descripcion }}
          </option>
        </select>
      </div>

      <div>
        <label for="filter-operador" class="block text-sm font-medium text-gray-700 mb-1">Operador</label>
        <div class="relative">
          <select
            id="filter-operador"
            v-model="filters.empleado_id"
            class="fg-input w-full"
            @change="handleFilterChange"
            :disabled="!filters.unidad_negocio_id || loadingOperadores"
          >
            <option value="">{{ operadorPlaceholder }}</option>
            <option v-for="op in operadores" :key="op.id" :value="op.id">{{ op.nombre }}</option>
          </select>
          <span v-if="loadingOperadores" class="absolute right-8 top-1/2 -translate-y-1/2">
            <svg class="animate-spin h-4 w-4 text-green-600" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
              <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
              <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z"></path>
            </svg>
          </span>
        </div>
      </div>

      <div>
        <label for="filter-equipo" class="block text-sm font-medium text-gray-700 mb-1">Equipo</label>
        <select
          id="filter-equipo"
          v-model="filters.equipo_id"
          class="fg-input w-full"
          @change="handleFilterChange"
          :disabled="!filters.unidad_negocio_id"
        >
          <option value="">{{ filters.unidad_negocio_id ? 'Todos' : 'Seleccione una unidad primero' }}</option>
          <option v-for="equipo in equipos" :key="equipo.id" :value="equipo.id">
            {{ equipo.descripcion }} {{ equipo.patente ? `(${equipo.patente})` : '' }}
          </option>
        </select>
      </div>

      <p v-if="filterError" role="alert" class="text-sm text-red-600">{{ filterError }}</p>

      <button
        @click="applyFilters"
        class="fg-btn-primary w-full"
      >
        Aplicar Filtros
      </button>

      <button
        @click="clearFilters"
        class="fg-btn-secondary w-full"
      >
        Limpiar
      </button>

      <button
        @click="showEmailModal = true"
        class="fg-btn-blue w-full"
      >
        <svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M3 8l7.89 5.26a2 2 0 002.22 0L21 8M5 19h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z" />
        </svg>
        Enviar por Email
      </button>
    </div>

    <div v-if="showEmailModal" class="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 px-3">
      <div class="fg-card w-full max-w-md p-4 sm:p-6">
        <div class="flex items-center justify-between mb-4">
          <h3 class="text-lg font-semibold text-gray-800">Enviar Informe por Email</h3>
          <button
            @click="closeEmailModal"
            class="text-gray-500 hover:text-gray-700 focus:outline-none focus:ring-2 focus:ring-blue-300"
            aria-label="Cerrar modal de email"
          >
            <svg xmlns="http://www.w3.org/2000/svg" class="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>

        <p class="text-sm text-gray-700 mb-4">
          Se generará un informe HTML con los datos de producción y combustible según los filtros aplicados y se enviará al email indicado.
        </p>

        <div class="mb-4">
          <label for="email-destino" class="block text-sm font-medium text-gray-700 mb-1">Correo electrónico</label>
          <input
            id="email-destino"
            v-model="emailDestino"
            type="email"
            placeholder="ejemplo@correo.com"
            class="fg-input w-full focus:border-blue-500 focus:ring-blue-500"
            :disabled="sendingEmail"
            @keyup.enter="enviarInformeEmail"
          />
        </div>

        <div v-if="emailError" role="alert" class="mb-4 p-3 bg-red-50 border border-red-200 rounded text-red-700 text-sm">
          {{ emailError }}
        </div>

        <div v-if="emailSuccess" role="status" class="mb-4 p-3 bg-green-50 border border-green-200 rounded text-green-700 text-sm">
          {{ emailSuccess }}
        </div>

        <div class="flex flex-col gap-3 sm:flex-row">
          <button
            @click="closeEmailModal"
            class="fg-btn-secondary w-full sm:flex-1"
            :disabled="sendingEmail"
          >
            Cancelar
          </button>
          <button
            @click="enviarInformeEmail"
            class="fg-btn-blue w-full sm:flex-1"
            :disabled="sendingEmail || !emailDestino"
          >
            <svg v-if="sendingEmail" class="animate-spin h-4 w-4" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
              <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
              <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z"></path>
            </svg>
            {{ sendingEmail ? 'Enviando...' : 'Enviar' }}
          </button>
        </div>
      </div>
    </div>
  </aside>
</template>

<script>
import { computed, ref, onMounted } from 'vue'
import { csrfFetch } from '../auth'

export default {
  name: 'FilterSidebar',
  emits: ['filter-change'],
  setup(_, { emit }) {
    const today = new Date()
    const thirtyDaysAgo = new Date()
    thirtyDaysAgo.setDate(today.getDate() - 30)

    const formatDate = (date) => date.toISOString().split('T')[0]

    const filters = ref({
      fecha_desde: formatDate(thirtyDaysAgo),
      fecha_hasta: formatDate(today),
      unidad_negocio_id: '',
      tipo_operacion_id: '',
      equipo_id: '',
      empleado_id: ''
    })
    const unidades = ref([])
    const tiposOperacion = ref([])
    const equipos = ref([])
    const operadores = ref([])
    const loadingOperadores = ref(false)
    const filterError = ref('')

    const showEmailModal = ref(false)
    const emailDestino = ref('')
    const sendingEmail = ref(false)
    const emailError = ref('')
    const emailSuccess = ref('')

    const operadorPlaceholder = computed(() => {
      if (!filters.value.unidad_negocio_id) return 'Seleccione una unidad primero'
      return loadingOperadores.value ? 'Cargando...' : 'Todos'
    })

    async function loadUnidades() {
      try {
        const API_BASE = import.meta.env.VITE_API_BASE || '/api'
        const params = new URLSearchParams()
        if (filters.value.fecha_desde) params.append('fecha_desde', filters.value.fecha_desde)
        if (filters.value.fecha_hasta) params.append('fecha_hasta', filters.value.fecha_hasta)

        const res = await fetch(`${API_BASE}/produccion/unidades/?${params}`, { credentials: 'include' })
        if (res.ok) {
          const data = await res.json()
          unidades.value = data.unidades || []
        }
      } catch (err) {
        console.error('Error cargando unidades:', err)
      }
    }

    async function loadTiposOperacion() {
      if (!filters.value.unidad_negocio_id) {
        tiposOperacion.value = []
        return
      }

      try {
        const API_BASE = import.meta.env.VITE_API_BASE || '/api'
        const params = new URLSearchParams()
        params.append('unidad_negocio_id', filters.value.unidad_negocio_id)
        if (filters.value.fecha_desde) params.append('fecha_desde', filters.value.fecha_desde)
        if (filters.value.fecha_hasta) params.append('fecha_hasta', filters.value.fecha_hasta)

        const res = await fetch(`${API_BASE}/produccion/tipos-operacion/?${params}`, { credentials: 'include' })
        if (res.ok) {
          const data = await res.json()
          tiposOperacion.value = data.tipos_operacion || []
        }
      } catch (err) {
        console.error('Error cargando tipos de operación:', err)
      }
    }

    async function loadEquipos() {
      if (!filters.value.unidad_negocio_id) {
        equipos.value = []
        return
      }

      try {
        const API_BASE = import.meta.env.VITE_API_BASE || '/api'
        const params = new URLSearchParams()
        params.append('unidad_negocio_id', filters.value.unidad_negocio_id)
        if (filters.value.fecha_desde) params.append('fecha_desde', filters.value.fecha_desde)
        if (filters.value.fecha_hasta) params.append('fecha_hasta', filters.value.fecha_hasta)

        const res = await fetch(`${API_BASE}/produccion/equipos/?${params}`, { credentials: 'include' })
        if (res.ok) {
          const data = await res.json()
          equipos.value = data.equipos || []
        }
      } catch (err) {
        console.error('Error cargando equipos:', err)
      }
    }

    async function loadOperadores() {
      if (!filters.value.unidad_negocio_id) {
        operadores.value = []
        return
      }

      loadingOperadores.value = true
      try {
        const API_BASE = import.meta.env.VITE_API_BASE || '/api'
        const params = new URLSearchParams()
        params.append('unidad_negocio_id', filters.value.unidad_negocio_id)
        if (filters.value.fecha_desde) params.append('fecha_desde', filters.value.fecha_desde)
        if (filters.value.fecha_hasta) params.append('fecha_hasta', filters.value.fecha_hasta)

        const res = await fetch(`${API_BASE}/produccion/operadores/?${params}`, { credentials: 'include' })
        if (res.ok) {
          const data = await res.json()
          operadores.value = data.operadores || []
        }
      } catch (err) {
        console.error('Error cargando operadores:', err)
      } finally {
        loadingOperadores.value = false
      }
    }

    async function onDateChange() {
      filterError.value = ''
      await loadUnidades()

      if (filters.value.unidad_negocio_id) {
        const unidadExiste = unidades.value.some(u => u.id == filters.value.unidad_negocio_id)

        if (!unidadExiste) {
          filters.value.unidad_negocio_id = ''
          await onUnidadChange()
        } else {
          await loadTiposOperacion()
          await loadEquipos()
          await loadOperadores()
        }
      }

      handleFilterChange()
    }

    async function onUnidadChange() {
      filters.value.tipo_operacion_id = ''
      filters.value.equipo_id = ''
      filters.value.empleado_id = ''
      await loadTiposOperacion()
      await loadEquipos()
      await loadOperadores()
      handleFilterChange()
    }

    function handleFilterChange() {
      filterError.value = ''
    }

    function validateFilters() {
      if (filters.value.fecha_desde && filters.value.fecha_hasta && filters.value.fecha_desde > filters.value.fecha_hasta) {
        filterError.value = 'Fecha Desde no puede ser posterior a Fecha Hasta.'
        return false
      }
      filterError.value = ''
      return true
    }

    function applyFilters() {
      if (!validateFilters()) return
      emit('filter-change', { ...filters.value })
    }

    function clearFilters() {
      const today = new Date()
      const thirtyDaysAgo = new Date()
      thirtyDaysAgo.setDate(today.getDate() - 30)

      filters.value = {
        fecha_desde: formatDate(thirtyDaysAgo),
        fecha_hasta: formatDate(today),
        unidad_negocio_id: '',
        tipo_operacion_id: '',
        equipo_id: '',
        empleado_id: ''
      }
      filterError.value = ''
      tiposOperacion.value = []
      equipos.value = []
      operadores.value = []
      emit('filter-change', { ...filters.value })
    }

    function closeEmailModal() {
      showEmailModal.value = false
      emailDestino.value = ''
      emailError.value = ''
      emailSuccess.value = ''
    }

    async function enviarInformeEmail() {
      if (!emailDestino.value) {
        emailError.value = 'Por favor ingrese un correo electrónico'
        return
      }

      const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/
      if (!emailRegex.test(emailDestino.value)) {
        emailError.value = 'El formato del correo electrónico no es válido'
        return
      }

      sendingEmail.value = true
      emailError.value = ''
      emailSuccess.value = ''

      try {
        const API_BASE = import.meta.env.VITE_API_BASE || '/api'
        const res = await csrfFetch(`${API_BASE}/enviar-informe-email/`, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({
            email: emailDestino.value,
            filters: { ...filters.value }
          })
        })

        const data = await res.json()

        if (res.ok && data.success) {
          emailSuccess.value = data.message || 'El informe se está generando y será enviado pronto'
          setTimeout(() => {
            closeEmailModal()
          }, 3000)
        } else {
          emailError.value = data.error || 'Error al enviar el informe'
        }
      } catch (err) {
        console.error('Error enviando informe:', err)
        emailError.value = 'Error de conexión. Por favor intente nuevamente.'
      } finally {
        sendingEmail.value = false
      }
    }

    onMounted(() => {
      loadUnidades()
      emit('filter-change', { ...filters.value })
    })

    return {
      filters,
      unidades,
      tiposOperacion,
      equipos,
      operadores,
      loadingOperadores,
      operadorPlaceholder,
      filterError,
      handleFilterChange,
      applyFilters,
      clearFilters,
      onUnidadChange,
      onDateChange,
      showEmailModal,
      emailDestino,
      sendingEmail,
      emailError,
      emailSuccess,
      closeEmailModal,
      enviarInformeEmail
    }
  }
}
</script>

<style scoped>
</style>



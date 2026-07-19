<template>
  <div class="min-h-screen bg-gray-50">
    <NavBar />
    <main class="py-4 sm:py-6">
      <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 space-y-6">
        <div class="fg-panel-accent p-4 sm:p-5">
          <h1 class="text-xl font-semibold text-green-700 mb-4">Producción</h1>

          <div class="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
            <div>
              <label for="produccion-mes" class="block text-sm font-medium text-gray-700 mb-1">Mes</label>
              <input
                id="produccion-mes"
                v-model="filters.mes"
                type="month"
                class="fg-input w-full"
                @change="onMesChange"
              />
            </div>

            <div>
              <label for="produccion-fecha-corte" class="block text-sm font-medium text-gray-700 mb-1">Hasta qué día</label>
              <input
                id="produccion-fecha-corte"
                v-model="filters.fecha_corte"
                type="date"
                class="fg-input w-full"
              />
            </div>

            <div>
              <label for="produccion-unidad" class="block text-sm font-medium text-gray-700 mb-1">Unidad de Negocio</label>
              <select id="produccion-unidad" v-model="filters.unidad_negocio_id" class="fg-input w-full">
                <option value="">Seleccione una unidad</option>
                <option v-for="unidad in unidades" :key="unidad.id" :value="String(unidad.id)">
                  {{ unidad.descripcion }}
                </option>
              </select>
            </div>

            <div class="flex flex-col gap-2 sm:col-span-2 sm:flex-row sm:items-end lg:col-span-1">
              <button
                class="fg-btn-primary w-full"
                @click="consultar"
                :disabled="loading"
              >
                {{ loading ? 'Consultando...' : 'Consultar' }}
              </button>
              <button
                class="fg-btn-primary w-full bg-emerald-700 hover:bg-emerald-800 focus:ring-emerald-300"
                @click="exportarExcel"
                :disabled="loading || !hasData"
              >
                Exportar Excel
              </button>
            </div>
          </div>

          <p v-if="error" role="alert" class="mt-3 text-sm text-red-600">{{ error }}</p>
          <div class="mt-4 flex flex-wrap gap-2 text-xs text-gray-600">
            <span class="rounded bg-gray-100 px-2 py-1">Mes: {{ filters.mes || '-' }}</span>
            <span class="rounded bg-gray-100 px-2 py-1">Corte: {{ filters.fecha_corte || '-' }}</span>
            <span class="rounded bg-gray-100 px-2 py-1">Unidad: {{ selectedUnidadLabel }}</span>
          </div>
        </div>

        <div v-if="!loading && !hasData" class="fg-card p-6 text-center text-gray-500 sm:p-8">
          No hay datos para los filtros seleccionados.
        </div>

        <div v-if="hasData" class="fg-card p-4 sm:p-0">
          <div class="space-y-3 md:hidden">
            <div v-for="row in rows" :key="`card-${row.un}-${row.movil}`" class="rounded-md border border-gray-200 bg-white p-3">
              <div class="mb-3">
                <p class="text-sm font-semibold text-gray-900">{{ row.movil }}</p>
                <p class="text-xs text-gray-600">{{ row.un }}</p>
              </div>
              <div class="grid grid-cols-2 gap-2 text-sm">
                <div>
                  <p class="text-xs text-gray-500">Consumo dia</p>
                  <p class="font-semibold text-gray-900">{{ fmt(row.consumo_dia) }}</p>
                </div>
                <div>
                  <p class="text-xs text-gray-500">Consumo acum.</p>
                  <p class="font-semibold text-gray-900">{{ fmt(row.consumo_acumulado) }}</p>
                </div>
                <div>
                  <p class="text-xs text-gray-500">Prod. dia</p>
                  <p class="font-semibold text-gray-900">{{ fmt(row.prod_dia) }}</p>
                </div>
                <div>
                  <p class="text-xs text-gray-500">Prod. acum.</p>
                  <p class="font-semibold text-gray-900">{{ fmt(row.prod_acumulada) }}</p>
                </div>
                <div>
                  <p class="text-xs text-gray-500">Litros</p>
                  <p class="font-semibold text-gray-900">{{ fmt(row.total_litros) }}</p>
                </div>
                <div>
                  <p class="text-xs text-gray-500">Produccion</p>
                  <p class="font-semibold text-gray-900">{{ fmt(row.total_produccion) }}</p>
                </div>
              </div>
              <div class="mt-3 grid grid-cols-2 gap-2">
                <button class="fg-btn-amber fg-btn-sm" :disabled="detailLoading" @click="openDetail(row, 'combustible')">
                  Combustible
                </button>
                <button class="fg-btn-primary fg-btn-sm" :disabled="detailLoading" @click="openDetail(row, 'produccion')">
                  Produccion
                </button>
              </div>
            </div>
            <div v-for="sub in subtotales" :key="`sub-card-${sub.un}`" class="rounded-md border border-amber-200 bg-amber-50 p-3">
              <p class="mb-2 text-sm font-semibold text-gray-900">{{ sub.movil }} · {{ sub.un }}</p>
              <div class="grid grid-cols-2 gap-2 text-sm">
                <p>Consumo: <strong>{{ fmt(sub.consumo_acumulado) }}</strong></p>
                <p>Produccion: <strong>{{ fmt(sub.prod_acumulada) }}</strong></p>
                <p>Litros: <strong>{{ fmt(sub.total_litros) }}</strong></p>
                <p>Total prod.: <strong>{{ fmt(sub.total_produccion) }}</strong></p>
              </div>
            </div>
            <div class="rounded-md border border-green-200 bg-green-100 p-3">
              <p class="mb-2 text-sm font-bold text-gray-900">{{ totalGeneral.movil }}</p>
              <div class="grid grid-cols-2 gap-2 text-sm">
                <p>Consumo: <strong>{{ fmt(totalGeneral.consumo_acumulado) }}</strong></p>
                <p>Produccion: <strong>{{ fmt(totalGeneral.prod_acumulada) }}</strong></p>
                <p>Litros: <strong>{{ fmt(totalGeneral.total_litros) }}</strong></p>
                <p>Total prod.: <strong>{{ fmt(totalGeneral.total_produccion) }}</strong></p>
              </div>
            </div>
          </div>
          <div class="hidden overflow-x-auto md:block">
          <table class="min-w-full divide-y divide-gray-200 text-sm">
            <thead class="bg-gray-50">
              <tr>
                <th class="px-4 py-3 text-left text-xs font-medium text-gray-700 uppercase">Móvil</th>
                <th class="px-4 py-3 text-left text-xs font-medium text-gray-700 uppercase">UN</th>
                <th class="px-4 py-3 text-right text-xs font-medium text-gray-700 uppercase">Consumo Día</th>
                <th class="px-4 py-3 text-right text-xs font-medium text-gray-700 uppercase">Consumo Acumulado</th>
                <th class="px-4 py-3 text-right text-xs font-medium text-gray-700 uppercase">Prod. Día</th>
                <th class="px-4 py-3 text-right text-xs font-medium text-gray-700 uppercase">Prod. Acumulada</th>
                <th class="px-4 py-3 text-right text-xs font-medium text-gray-700 uppercase">Total Litros</th>
                <th class="px-4 py-3 text-right text-xs font-medium text-gray-700 uppercase">Total Producción</th>
                <th class="px-4 py-3 text-center text-xs font-medium text-gray-700 uppercase">Registros</th>
              </tr>
            </thead>
            <tbody class="bg-white divide-y divide-gray-100">
              <tr v-for="row in rows" :key="`${row.un}-${row.movil}`" class="hover:bg-gray-50">
                <td class="px-4 py-2 text-gray-900">{{ row.movil }}</td>
                <td class="px-4 py-2 text-gray-700">{{ row.un }}</td>
                <td class="px-4 py-2 text-right">{{ fmt(row.consumo_dia) }}</td>
                <td class="px-4 py-2 text-right">{{ fmt(row.consumo_acumulado) }}</td>
                <td class="px-4 py-2 text-right">{{ fmt(row.prod_dia) }}</td>
                <td class="px-4 py-2 text-right">{{ fmt(row.prod_acumulada) }}</td>
                <td class="px-4 py-2 text-right">{{ fmt(row.total_litros) }}</td>
                <td class="px-4 py-2 text-right">{{ fmt(row.total_produccion) }}</td>
                <td class="px-4 py-2">
                  <div class="flex flex-col justify-center gap-2 sm:flex-row">
                    <button
                      class="fg-btn-amber fg-btn-sm"
                      :disabled="detailLoading"
                      @click="openDetail(row, 'combustible')"
                    >
                      Combustible
                    </button>
                    <button
                      class="fg-btn-primary fg-btn-sm"
                      :disabled="detailLoading"
                      @click="openDetail(row, 'produccion')"
                    >
                      Producción
                    </button>
                  </div>
                </td>
              </tr>

              <tr v-for="sub in subtotales" :key="`sub-${sub.un}`" class="bg-amber-50 font-semibold">
                <td class="px-4 py-2">{{ sub.movil }}</td>
                <td class="px-4 py-2">{{ sub.un }}</td>
                <td class="px-4 py-2 text-right">{{ fmt(sub.consumo_dia) }}</td>
                <td class="px-4 py-2 text-right">{{ fmt(sub.consumo_acumulado) }}</td>
                <td class="px-4 py-2 text-right">{{ fmt(sub.prod_dia) }}</td>
                <td class="px-4 py-2 text-right">{{ fmt(sub.prod_acumulada) }}</td>
                <td class="px-4 py-2 text-right">{{ fmt(sub.total_litros) }}</td>
                <td class="px-4 py-2 text-right">{{ fmt(sub.total_produccion) }}</td>
                <td class="px-4 py-2"></td>
              </tr>

              <tr class="bg-green-100 font-bold">
                <td class="px-4 py-2">{{ totalGeneral.movil }}</td>
                <td class="px-4 py-2">{{ totalGeneral.un }}</td>
                <td class="px-4 py-2 text-right">{{ fmt(totalGeneral.consumo_dia) }}</td>
                <td class="px-4 py-2 text-right">{{ fmt(totalGeneral.consumo_acumulado) }}</td>
                <td class="px-4 py-2 text-right">{{ fmt(totalGeneral.prod_dia) }}</td>
                <td class="px-4 py-2 text-right">{{ fmt(totalGeneral.prod_acumulada) }}</td>
                <td class="px-4 py-2 text-right">{{ fmt(totalGeneral.total_litros) }}</td>
                <td class="px-4 py-2 text-right">{{ fmt(totalGeneral.total_produccion) }}</td>
                <td class="px-4 py-2"></td>
              </tr>
            </tbody>
          </table>
          </div>
        </div>
      </div>
    </main>

    <div
      v-if="detailModal.open"
      class="fixed inset-0 z-50 flex items-center justify-center bg-black bg-opacity-40 px-2 sm:px-4"
      @click.self="closeDetail"
    >
      <div class="fg-card flex max-h-[90vh] w-full max-w-6xl flex-col">
        <div class="flex items-start justify-between gap-4 border-b px-4 py-3 sm:px-5 sm:py-4">
          <div>
            <h2 class="text-lg font-semibold text-gray-900">{{ detailModal.title }}</h2>
            <p class="text-sm text-gray-500">{{ detailModal.subtitle }}</p>
          </div>
          <button
            class="text-gray-500 hover:text-gray-800 text-2xl leading-none focus:outline-none focus:ring-2 focus:ring-green-300"
            @click="closeDetail"
            aria-label="Cerrar detalle"
          >
            &times;
          </button>
        </div>

        <div class="overflow-auto px-4 py-4 sm:px-5">
          <p v-if="detailError" role="alert" class="text-sm text-red-600 mb-3">{{ detailError }}</p>
          <div v-if="detailLoading" class="py-10 text-center text-gray-500">Cargando registros...</div>

          <div v-if="!detailLoading && detailModal.type === 'combustible'" class="space-y-2 md:hidden">
            <div v-for="item in detailRows" :key="`comb-card-${item.id}`" class="rounded-md border border-gray-200 bg-white p-3">
              <div class="mb-2">
                <p class="text-sm font-semibold text-gray-900">{{ item.equipo }}</p>
                <p class="text-xs text-gray-600">{{ item.fecha }} · {{ item.tipo_combustible }}</p>
              </div>
              <div class="grid grid-cols-2 gap-2 text-sm">
                <p>Litros: <strong>{{ fmt(item.egreso) }}</strong></p>
                <p>Km/Hora: <strong>{{ fmt(item.km_hora) }}</strong></p>
                <p>Precio/L: <strong>{{ fmt(item.precio_litro) }}</strong></p>
                <p>Remito: <strong>{{ item.remito || '-' }}</strong></p>
              </div>
              <p v-if="item.observaciones" class="mt-2 text-xs text-gray-600">{{ item.observaciones }}</p>
            </div>
            <p v-if="detailRows.length === 0" class="py-8 text-center text-gray-500">No hay registros de combustible.</p>
          </div>

          <table v-if="!detailLoading && detailModal.type === 'combustible'" class="hidden min-w-full divide-y divide-gray-200 text-sm md:table">
            <thead class="bg-amber-50">
              <tr>
                <th class="px-3 py-2 text-left text-xs font-medium text-gray-700 uppercase">Fecha</th>
                <th class="px-3 py-2 text-left text-xs font-medium text-gray-700 uppercase">Equipo</th>
                <th class="px-3 py-2 text-left text-xs font-medium text-gray-700 uppercase">Tipo</th>
                <th class="px-3 py-2 text-right text-xs font-medium text-gray-700 uppercase">Litros</th>
                <th class="px-3 py-2 text-right text-xs font-medium text-gray-700 uppercase">Km/Hora</th>
                <th class="px-3 py-2 text-right text-xs font-medium text-gray-700 uppercase">Precio/L</th>
                <th class="px-3 py-2 text-left text-xs font-medium text-gray-700 uppercase">Remito</th>
                <th class="px-3 py-2 text-left text-xs font-medium text-gray-700 uppercase">Obs.</th>
              </tr>
            </thead>
            <tbody class="divide-y divide-gray-100">
              <tr v-for="item in detailRows" :key="`comb-${item.id}`">
                <td class="px-3 py-2 whitespace-nowrap">{{ item.fecha }}</td>
                <td class="px-3 py-2 whitespace-nowrap">{{ item.equipo }}</td>
                <td class="px-3 py-2 whitespace-nowrap">{{ item.tipo_combustible }}</td>
                <td class="px-3 py-2 text-right">{{ fmt(item.egreso) }}</td>
                <td class="px-3 py-2 text-right">{{ fmt(item.km_hora) }}</td>
                <td class="px-3 py-2 text-right">{{ fmt(item.precio_litro) }}</td>
                <td class="px-3 py-2 whitespace-nowrap">{{ item.remito }}</td>
                <td class="px-3 py-2">{{ item.observaciones }}</td>
              </tr>
              <tr v-if="detailRows.length === 0">
                <td colspan="8" class="px-3 py-8 text-center text-gray-500">No hay registros de combustible.</td>
              </tr>
            </tbody>
          </table>

          <div v-if="!detailLoading && detailModal.type !== 'combustible'" class="space-y-2 md:hidden">
            <div v-for="item in detailRows" :key="`prod-card-${item.id}`" class="rounded-md border border-gray-200 bg-white p-3">
              <div class="mb-2">
                <p class="text-sm font-semibold text-gray-900">{{ item.equipo }}</p>
                <p class="text-xs text-gray-600">{{ item.fecha }} · {{ item.unidad_produccion }} · {{ item.turno }}</p>
              </div>
              <div class="grid grid-cols-2 gap-2 text-sm">
                <p>Hr inicio: <strong>{{ fmt(item.hr_inicio) }}</strong></p>
                <p>Hr fin: <strong>{{ fmt(item.hr_fin) }}</strong></p>
                <p>Horas: <strong>{{ fmt(item.horas_trabajadas) }}</strong></p>
                <p>Produccion: <strong>{{ fmt(item.produccion) }}</strong></p>
              </div>
              <p v-if="item.observaciones" class="mt-2 text-xs text-gray-600">{{ item.observaciones }}</p>
              <button
                class="mt-3 rounded bg-red-600 px-3 py-1.5 text-xs font-semibold text-white hover:bg-red-700 disabled:cursor-not-allowed disabled:opacity-60"
                type="button"
                :disabled="deletingId === item.id"
                @click="deleteProduccion(item)"
              >
                {{ deletingId === item.id ? 'Borrando...' : 'Borrar movimiento' }}
              </button>
            </div>
            <p v-if="detailRows.length === 0" class="py-8 text-center text-gray-500">No hay registros de producción.</p>
          </div>

          <table v-if="!detailLoading && detailModal.type !== 'combustible'" class="hidden min-w-full divide-y divide-gray-200 text-sm md:table">
            <thead class="bg-green-50">
              <tr>
                <th class="px-3 py-2 text-left text-xs font-medium text-gray-700 uppercase">Fecha</th>
                <th class="px-3 py-2 text-left text-xs font-medium text-gray-700 uppercase">Equipo</th>
                <th class="px-3 py-2 text-right text-xs font-medium text-gray-700 uppercase">Hr Inicio</th>
                <th class="px-3 py-2 text-right text-xs font-medium text-gray-700 uppercase">Hr Fin</th>
                <th class="px-3 py-2 text-right text-xs font-medium text-gray-700 uppercase">Horas</th>
                <th class="px-3 py-2 text-right text-xs font-medium text-gray-700 uppercase">Producción</th>
                <th class="px-3 py-2 text-left text-xs font-medium text-gray-700 uppercase">Unidad</th>
                <th class="px-3 py-2 text-left text-xs font-medium text-gray-700 uppercase">Turno</th>
                <th class="px-3 py-2 text-left text-xs font-medium text-gray-700 uppercase">Obs.</th>
                <th class="px-3 py-2 text-right text-xs font-medium text-gray-700 uppercase">Acciones</th>
              </tr>
            </thead>
            <tbody class="divide-y divide-gray-100">
              <tr v-for="item in detailRows" :key="`prod-${item.id}`">
                <td class="px-3 py-2 whitespace-nowrap">{{ item.fecha }}</td>
                <td class="px-3 py-2 whitespace-nowrap">{{ item.equipo }}</td>
                <td class="px-3 py-2 text-right">{{ fmt(item.hr_inicio) }}</td>
                <td class="px-3 py-2 text-right">{{ fmt(item.hr_fin) }}</td>
                <td class="px-3 py-2 text-right">{{ fmt(item.horas_trabajadas) }}</td>
                <td class="px-3 py-2 text-right">{{ fmt(item.produccion) }}</td>
                <td class="px-3 py-2 whitespace-nowrap">{{ item.unidad_produccion }}</td>
                <td class="px-3 py-2 whitespace-nowrap">{{ item.turno }}</td>
                <td class="px-3 py-2">{{ item.observaciones }}</td>
                <td class="px-3 py-2 text-right">
                  <button
                    class="rounded bg-red-600 px-2.5 py-1 text-xs font-semibold text-white hover:bg-red-700 disabled:cursor-not-allowed disabled:opacity-60"
                    type="button"
                    :disabled="deletingId === item.id"
                    @click="deleteProduccion(item)"
                  >
                    {{ deletingId === item.id ? 'Borrando...' : 'Borrar' }}
                  </button>
                </td>
              </tr>
              <tr v-if="detailRows.length === 0">
                <td colspan="10" class="px-3 py-8 text-center text-gray-500">No hay registros de producción.</td>
              </tr>
            </tbody>
          </table>
        </div>

        <div class="border-t px-4 py-3 text-sm text-gray-500 sm:px-5">
          {{ detailRows.length }} de {{ detailTotalItems }} registros
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import { computed, onMounted, ref } from 'vue'
import NavBar from '../components/NavBar.vue'
import { csrfFetch } from '../auth'

export default {
  name: 'ProduccionView',
  components: { NavBar },
  setup() {
    const API_BASE = import.meta.env.VITE_API_BASE || '/api'

    const now = new Date()
    const currentMonth = `${now.getFullYear()}-${String(now.getMonth() + 1).padStart(2, '0')}`
    const currentDate = now.toISOString().split('T')[0]

    const filters = ref({
      mes: currentMonth,
      fecha_corte: currentDate,
      unidad_negocio_id: '',
    })

    const unidades = ref([])
    const rows = ref([])
    const subtotales = ref([])
    const totalGeneral = ref({
      movil: 'Total General',
      un: '-',
      consumo_dia: 0,
      consumo_acumulado: 0,
      prod_dia: 0,
      prod_acumulada: 0,
      total_litros: 0,
      total_produccion: 0,
    })
    const loading = ref(false)
    const error = ref('')
    const detailLoading = ref(false)
    const detailError = ref('')
    const detailRows = ref([])
    const detailTotalItems = ref(0)
    const deletingId = ref(null)
    const detailModal = ref({
      open: false,
      type: '',
      title: '',
      subtitle: '',
    })

    const hasData = computed(() => rows.value.length > 0)
    const selectedUnidadLabel = computed(() => {
      const selected = unidades.value.find(unidad => String(unidad.id) === String(filters.value.unidad_negocio_id))
      return selected ? selected.descripcion : 'Sin seleccionar'
    })

    function fmt(value) {
      const num = Number(value || 0)
      return num.toFixed(2)
    }

    function getMonthStart() {
      const [year, month] = (filters.value.mes || '').split('-')
      return `${year}-${month}-01`
    }

    function onMesChange() {
      const [year, month] = (filters.value.mes || '').split('-').map(Number)
      if (!year || !month) return

      const cutoff = new Date(filters.value.fecha_corte)
      const sameMonth = cutoff.getFullYear() === year && cutoff.getMonth() + 1 === month
      if (sameMonth) return

      const lastDay = new Date(year, month, 0).getDate()
      const day = Math.min(now.getDate(), lastDay)
      filters.value.fecha_corte = `${filters.value.mes}-${String(day).padStart(2, '0')}`
    }

    async function loadUnidades() {
      try {
        const [year, month] = (filters.value.mes || '').split('-')
        const firstDay = `${year}-${month}-01`
        const params = new URLSearchParams({
          fecha_desde: firstDay,
          fecha_hasta: filters.value.fecha_corte,
        })
        const res = await fetch(`${API_BASE}/produccion/unidades/?${params.toString()}`, { credentials: 'include' })
        if (!res.ok) return
        const json = await res.json()
        unidades.value = json.unidades || []
      } catch (err) {
        console.error('Error cargando unidades:', err)
      }
    }

    function validateFilters() {
      if (!filters.value.mes || !filters.value.fecha_corte || !filters.value.unidad_negocio_id) {
        error.value = 'Mes, fecha de corte y unidad de negocio son obligatorios.'
        return false
      }

      const monthPrefix = `${filters.value.mes}-`
      if (!filters.value.fecha_corte.startsWith(monthPrefix)) {
        error.value = 'La fecha de corte debe pertenecer al mes seleccionado.'
        return false
      }

      return true
    }

    async function consultar() {
      error.value = ''
      if (!validateFilters()) return

      loading.value = true
      try {
        const params = new URLSearchParams({
          mes: filters.value.mes,
          fecha_corte: filters.value.fecha_corte,
          unidad_negocio_id: filters.value.unidad_negocio_id,
        })

        const res = await fetch(`${API_BASE}/produccion/reporte/?${params.toString()}`, {
          credentials: 'include',
        })

        const json = await res.json().catch(() => ({}))
        if (!res.ok) {
          error.value = json.detail || 'No se pudo consultar el reporte.'
          rows.value = []
          subtotales.value = []
          return
        }

        rows.value = json.rows || []
        subtotales.value = json.subtotales_un || []
        totalGeneral.value = json.total_general || totalGeneral.value
      } catch (err) {
        console.error('Error consultando reporte:', err)
        error.value = 'Error de conexión al consultar el reporte.'
      } finally {
        loading.value = false
      }
    }

    async function exportarExcel() {
      error.value = ''
      if (!validateFilters()) return

      try {
        const params = new URLSearchParams({
          mes: filters.value.mes,
          fecha_corte: filters.value.fecha_corte,
          unidad_negocio_id: filters.value.unidad_negocio_id,
        })

        const res = await fetch(`${API_BASE}/produccion/reporte/export-excel/?${params.toString()}`, {
          credentials: 'include',
        })

        if (!res.ok) {
          const json = await res.json().catch(() => ({}))
          error.value = json.detail || 'No se pudo exportar el archivo.'
          return
        }

        const blob = await res.blob()
        const contentDisposition = res.headers.get('Content-Disposition') || ''
        const match = contentDisposition.match(/filename=([^;]+)/i)
        const filename = match ? match[1].replace(/"/g, '') : 'produccion_yyyy_mm_dd.xlsx'

        const url = window.URL.createObjectURL(blob)
        const a = document.createElement('a')
        a.href = url
        a.download = filename
        document.body.appendChild(a)
        a.click()
        a.remove()
        window.URL.revokeObjectURL(url)
      } catch (err) {
        console.error('Error exportando excel:', err)
        error.value = 'Error de conexión al exportar.'
      }
    }

    function closeDetail() {
      detailModal.value.open = false
      detailRows.value = []
      detailError.value = ''
      detailTotalItems.value = 0
    }

    async function openDetail(row, type) {
      detailError.value = ''
      detailRows.value = []
      detailTotalItems.value = 0
      detailLoading.value = true
      detailModal.value = {
        open: true,
        type,
        title: type === 'combustible' ? 'Registros de combustible' : 'Registros de producción',
        subtitle: `${row.movil} - ${row.un} - ${getMonthStart()} al ${filters.value.fecha_corte}`,
      }

      try {
        const params = new URLSearchParams({
          fecha_desde: getMonthStart(),
          fecha_hasta: filters.value.fecha_corte,
          unidad_negocio_id: String(row.unidad_negocio_id || filters.value.unidad_negocio_id),
          equipo_id: String(row.equipo_id),
          page: '1',
          page_size: '500',
        })

        const endpoint = type === 'combustible' ? 'combustible/detalle' : 'produccion/detalle'
        const res = await fetch(`${API_BASE}/${endpoint}/?${params.toString()}`, { credentials: 'include' })
        const json = await res.json().catch(() => ({}))
        if (!res.ok) {
          detailError.value = json.detail || 'No se pudieron cargar los registros.'
          return
        }

        detailRows.value = json.detalle || []
        detailTotalItems.value = json.total_items || detailRows.value.length
      } catch (err) {
        console.error('Error cargando registros:', err)
        detailError.value = 'Error de conexión al cargar los registros.'
      } finally {
        detailLoading.value = false
      }
    }

    async function deleteProduccion(item) {
      if (!item?.id || detailModal.value.type === 'combustible') return

      const confirmed = window.confirm(
        `¿Borrar el movimiento de producción del ${item.fecha}? Si tiene combustible asociado, también se borrará.`
      )
      if (!confirmed) return

      detailError.value = ''
      deletingId.value = item.id
      try {
        const res = await csrfFetch(`${API_BASE}/produccion/${item.id}/`, { method: 'DELETE' })
        const json = await res.json().catch(() => ({}))
        if (!res.ok) {
          detailError.value = json.detail || 'No se pudo borrar el movimiento.'
          return
        }

        detailRows.value = detailRows.value.filter(row => row.id !== item.id)
        detailTotalItems.value = Math.max(0, detailTotalItems.value - 1)
        await consultar()
      } catch (err) {
        console.error('Error borrando movimiento:', err)
        detailError.value = 'Error de conexión al borrar el movimiento.'
      } finally {
        deletingId.value = null
      }
    }

    onMounted(async () => {
      await loadUnidades()
    })

    return {
      filters,
      unidades,
      rows,
      subtotales,
      totalGeneral,
      loading,
      error,
      detailLoading,
      detailError,
      detailRows,
      detailTotalItems,
      deletingId,
      detailModal,
      hasData,
      selectedUnidadLabel,
      fmt,
      onMesChange,
      consultar,
      exportarExcel,
      openDetail,
      deleteProduccion,
      closeDetail,
    }
  },
}
</script>

<style scoped>
</style>


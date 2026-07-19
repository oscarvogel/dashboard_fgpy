<template>
  <div class="min-h-screen bg-gray-50">
    <NavBar />
    <main class="py-4 sm:py-6">
      <div class="max-w-7xl mx-auto px-3 sm:px-6 lg:px-8">
        <div class="grid grid-cols-1 gap-4 lg:grid-cols-4 lg:gap-6">
          <!-- Sidebar -->
          <div class="lg:col-span-1">
            <FilterSidebar @filter-change="onFilterChange" />
          </div>

          <!-- Content -->
          <div class="lg:col-span-3 space-y-6">
            <div v-if="error" role="alert" class="bg-red-50 border border-red-200 text-red-700 rounded p-4 text-sm">
              {{ error }}
            </div>

            <div class="grid grid-cols-1 gap-3 sm:grid-cols-2 lg:grid-cols-3 lg:gap-4 mb-4">
              <div class="fg-card-accent-green p-4">
                <div>
                  <div class="text-sm text-gray-600">Horas Totales</div>
                  <div class="text-2xl font-bold text-green-700">{{ kpis.total_horas ?? '-' }}</div>
                </div>
              </div>

              <div class="fg-card-accent-amber p-4">
                <div>
                  <div class="text-sm text-gray-600">Combustible Total (L)</div>
                  <div class="text-2xl font-bold text-amber-700">{{ kpis.total_combustible ?? '-' }}</div>
                </div>
              </div>

              <div class="fg-card-accent-amber p-4">
                <div>
                  <div class="text-sm text-gray-600">Consumo / Hora (L/h)</div>
                  <div class="text-2xl font-bold text-amber-700">{{ kpis.horas_por_litro ?? '-' }}</div>
                </div>
              </div>
            </div>

            <div class="fg-card">
              <div class="p-4 sm:p-6">
                <h3 class="text-lg font-semibold mb-4">Consumo de Combustible por Fecha</h3>
                <apexchart v-if="chartSeries.length" type="area" height="340" :options="chartOptions" :series="chartSeries" />
                <p v-else class="text-gray-500 text-center py-8">{{ loading ? 'Cargando datos...' : 'No hay datos' }}</p>
              </div>
            </div>

            <div class="fg-card p-4 sm:p-6">
              <h3 class="text-lg font-semibold mb-4">Detalle por Fecha</h3>
              <div class="space-y-2 md:hidden">
                <div v-for="row in data" :key="`fecha-card-${row.fecha}`" class="rounded-md border border-gray-200 bg-white p-3">
                  <div class="flex items-center justify-between gap-3">
                    <p class="text-sm font-semibold text-gray-900">{{ row.fecha }}</p>
                    <div class="text-right">
                      <p class="text-xs text-gray-500">Consumo</p>
                      <p class="font-semibold text-amber-700">{{ row.total_consumo }} L</p>
                    </div>
                  </div>
                </div>
                <p v-if="!data.length" class="py-8 text-center text-sm text-gray-500">{{ loading ? 'Cargando datos...' : 'No hay datos' }}</p>
              </div>
              <div class="hidden overflow-x-auto md:block">
                <table class="min-w-full divide-y divide-gray-200 text-sm">
                  <thead class="bg-green-50">
                    <tr>
                      <th class="px-4 py-3 text-left text-xs font-medium text-green-700 uppercase tracking-wider">Fecha</th>
                      <th class="px-4 py-3 text-right text-xs font-medium text-green-700 uppercase tracking-wider">Consumo (L)</th>
                    </tr>
                  </thead>
                  <tbody class="bg-white divide-y divide-gray-200">
                    <tr v-for="row in data" :key="row.fecha" class="hover:bg-gray-50">
                      <td class="px-4 py-2 whitespace-nowrap text-sm text-gray-900">{{ row.fecha }}</td>
                      <td class="px-4 py-2 whitespace-nowrap text-sm text-gray-900 text-right">{{ row.total_consumo }}</td>
                    </tr>
                    <tr v-if="!data.length">
                      <td colspan="2" class="px-4 py-8 text-center text-gray-500">{{ loading ? 'Cargando datos...' : 'No hay datos' }}</td>
                    </tr>
                  </tbody>
                </table>
              </div>
            </div>

            <div class="fg-card p-4 sm:p-6">
              <h3 class="text-lg font-semibold mb-4">Consumo Medio por Equipo</h3>
              <div class="space-y-3 md:hidden">
                <div v-for="row in consumoPorEquipo" :key="`equipo-card-${row.equipo_id}`" class="rounded-md border border-gray-200 bg-white p-3">
                  <p class="mb-3 text-sm font-semibold text-gray-900">{{ row.equipo }}</p>
                  <div class="grid grid-cols-3 gap-2 text-sm">
                    <div>
                      <p class="text-xs text-gray-500">Horas</p>
                      <p class="font-semibold text-gray-900">{{ row.horas_trabajadas }}</p>
                    </div>
                    <div>
                      <p class="text-xs text-gray-500">Litros</p>
                      <p class="font-semibold text-gray-900">{{ row.litros }}</p>
                    </div>
                    <div>
                      <p class="text-xs text-gray-500">L/H</p>
                      <p class="font-semibold text-gray-900">{{ row.litros_por_hora }}</p>
                    </div>
                  </div>
                </div>
                <p v-if="!consumoPorEquipo.length" class="py-8 text-center text-sm text-gray-500">{{ loading ? 'Cargando datos...' : 'No hay datos' }}</p>
              </div>
              <div class="hidden overflow-x-auto md:block">
                <table class="min-w-full divide-y divide-gray-200 text-sm">
                  <thead class="bg-green-50">
                    <tr>
                      <th class="px-4 py-3 text-left text-xs font-medium text-green-700 uppercase tracking-wider">Equipo</th>
                      <th class="px-4 py-3 text-right text-xs font-medium text-green-700 uppercase tracking-wider">Horas Trabajadas</th>
                      <th class="px-4 py-3 text-right text-xs font-medium text-green-700 uppercase tracking-wider">Litros</th>
                      <th class="px-4 py-3 text-right text-xs font-medium text-green-700 uppercase tracking-wider">Litros / Hora</th>
                    </tr>
                  </thead>
                  <tbody class="bg-white divide-y divide-gray-200">
                    <tr v-for="row in consumoPorEquipo" :key="row.equipo_id" class="hover:bg-gray-50">
                      <td class="px-4 py-2 whitespace-nowrap text-sm text-gray-900">{{ row.equipo }}</td>
                      <td class="px-4 py-2 whitespace-nowrap text-sm text-gray-900 text-right">{{ row.horas_trabajadas }}</td>
                      <td class="px-4 py-2 whitespace-nowrap text-sm text-gray-900 text-right">{{ row.litros }}</td>
                      <td class="px-4 py-2 whitespace-nowrap text-sm text-gray-900 text-right">{{ row.litros_por_hora }}</td>
                    </tr>
                    <tr v-if="!consumoPorEquipo.length">
                      <td colspan="4" class="px-4 py-8 text-center text-gray-500">{{ loading ? 'Cargando datos...' : 'No hay datos' }}</td>
                    </tr>
                  </tbody>
                </table>
              </div>
            </div>
          </div>
        </div>
      </div>
    </main>
  </div>
</template>

<script>
import { ref } from 'vue'
import NavBar from '../components/NavBar.vue'
import FilterSidebar from '../components/FilterSidebar.vue'
import ApexChart from 'vue3-apexcharts'

export default {
  name: 'CombustibleView',
  components: { NavBar, FilterSidebar, apexchart: ApexChart },
  setup() {
    const data = ref([])
    const kpis = ref({})
    const consumoPorEquipo = ref([])
    const loading = ref(false)
    const error = ref('')

    const chartSeries = ref([])
    const chartOptions = ref({
      chart: { toolbar: { show: true }, zoom: { enabled: false } },
      xaxis: { categories: [] },
      colors: ['#f59e0b'],
      stroke: { curve: 'smooth' },
    })

    async function loadData(filters) {
      loading.value = true
      error.value = ''
      const API_BASE = import.meta.env.VITE_API_BASE || '/api'
      const params = new URLSearchParams()
      if (filters.fecha_desde) params.append('fecha_desde', filters.fecha_desde)
      if (filters.fecha_hasta) params.append('fecha_hasta', filters.fecha_hasta)
      if (filters.unidad_negocio_id) params.append('unidad_negocio_id', filters.unidad_negocio_id)
      if (filters.tipo_operacion_id) params.append('tipo_operacion_id', filters.tipo_operacion_id)
      if (filters.equipo_id) params.append('equipo_id', filters.equipo_id)
      if (filters.empleado_id) params.append('empleado_id', filters.empleado_id)

      try {
        const res = await fetch(`${API_BASE}/combustible/data/?${params}`, { credentials: 'include' })
        if (!res.ok) throw new Error('No se pudieron cargar los datos de combustible.')

        const json = await res.json()
        data.value = json.data || []

        const labels = data.value.map(d => d.fecha)
        const values = data.value.map(d => d.total_consumo)
        chartOptions.value.xaxis.categories = labels
        chartSeries.value = values.length ? [{ name: 'Consumo (L)', data: values }] : []

        const resK = await fetch(`${API_BASE}/combustible/kpis/?${params}`, { credentials: 'include' })
        if (resK.ok) {
          const jk = await resK.json()
          kpis.value = jk.kpis || {}
        }

        // cargar consumo por equipo
        const resE = await fetch(`${API_BASE}/combustible/por-equipo/?${params}`, { credentials: 'include' })
        if (resE.ok) {
          const je = await resE.json()
          consumoPorEquipo.value = je.data || []
        }
      } catch (err) {
        console.error('Error cargando datos de combustible:', err)
        error.value = err.message || 'Error de conexión al cargar combustible.'
        data.value = []
        consumoPorEquipo.value = []
        chartSeries.value = []
      } finally {
        loading.value = false
      }
    }

    function onFilterChange(filters) {
      loadData(filters)
    }

    return { data, kpis, consumoPorEquipo, loading, error, chartSeries, chartOptions, onFilterChange }
  }
}
</script>

<style scoped>
</style>


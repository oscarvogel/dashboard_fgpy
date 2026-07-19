<template>
  <div class="min-h-screen bg-gray-50">
    <NavBar />
    <main class="py-4 sm:py-6">
      <div class="max-w-7xl mx-auto px-3 sm:px-6 lg:px-8">
        <div class="grid grid-cols-1 gap-4 lg:grid-cols-4 lg:gap-6">
          <div class="lg:col-span-1">
            <FilterSidebar @filter-change="onFilterChange" />
          </div>

          <div class="lg:col-span-3 space-y-6">
            <div v-if="error" role="alert" class="bg-red-50 border border-red-200 text-red-700 rounded p-4 text-sm">
              {{ error }}
            </div>
            <div v-else-if="loading" role="status" class="fg-card p-4 text-sm text-gray-700">
              Cargando dashboard ejecutivo...
            </div>
            <div v-else-if="isEmpty" role="status" class="bg-amber-50 border border-amber-200 text-amber-800 rounded p-4 text-sm">
              No hay datos para los filtros seleccionados. Probá ampliar el período o limpiar filtros.
            </div>

            <section class="fg-panel-accent p-4 sm:p-5">
              <div class="flex flex-col gap-4 xl:flex-row xl:items-center xl:justify-between">
                <div>
                  <p class="text-sm font-medium text-gray-600">Dashboard Ejecutivo</p>
                  <h1 class="text-2xl font-semibold text-gray-900">Control por segmento operativo</h1>
                  <p class="mt-1 text-sm text-gray-600">
                    {{ periodoLabel }}
                  </p>
                </div>
                <div :class="['inline-flex items-center rounded-md px-4 py-2 text-sm font-semibold', statusClass(resumen.estado_general)]">
                  {{ statusLabel(resumen.estado_general) }}
                </div>
              </div>
            </section>

            <section class="grid grid-cols-1 gap-3 sm:grid-cols-2 xl:grid-cols-4">
              <div class="fg-card-accent-amber p-4">
                <p class="text-sm text-gray-600">Combustible Total</p>
                <p class="text-2xl font-bold text-amber-700">{{ fmt(resumen.combustible_total) }} L</p>
              </div>
              <div class="fg-card-accent-green p-4">
                <p class="text-sm text-gray-600">Horas Operativas</p>
                <p class="text-2xl font-bold text-green-700">{{ fmt(resumen.horas_operativas) }}</p>
              </div>
              <div class="fg-card-accent-red p-4">
                <p class="text-sm text-gray-600">Horas No Operativas</p>
                <p class="text-2xl font-bold text-red-700">{{ fmt(resumen.horas_no_operativas) }}</p>
              </div>
              <div class="fg-card p-4 border-t-4 border-t-blue-500">
                <p class="text-sm text-gray-600">Alertas / Equipos</p>
                <p class="text-2xl font-bold text-blue-700">{{ resumen.alertas_total || 0 }} / {{ resumen.equipos_activos || 0 }}</p>
              </div>
            </section>

            <section class="grid grid-cols-1 gap-6 xl:grid-cols-2">
              <div class="fg-card p-4 sm:p-5">
                <div class="mb-4 flex items-center justify-between gap-3">
                  <h2 class="text-lg font-semibold text-gray-900">Producción por Unidad</h2>
                  <span class="text-xs text-gray-600">No se mezclan unidades incompatibles</span>
                </div>
                <div class="space-y-3">
                  <div v-for="item in produccionPorUnidad" :key="item.unidad_produccion_id || item.unidad_produccion" class="border-b border-gray-100 pb-3 last:border-b-0 last:pb-0">
                    <div class="flex items-center justify-between gap-3">
                      <div>
                        <p class="font-medium text-gray-900">{{ item.unidad_produccion }}</p>
                        <p class="text-xs text-gray-600">{{ item.registros }} registros · {{ fmt(item.horas) }} horas</p>
                      </div>
                      <p class="text-right text-lg font-semibold text-green-700">{{ fmt(item.produccion) }}</p>
                    </div>
                  </div>
                  <p v-if="!produccionPorUnidad.length" class="py-8 text-center text-sm text-gray-500">No hay producción para mostrar.</p>
                </div>
              </div>

              <div class="fg-card p-4 sm:p-5">
                <h2 class="mb-4 text-lg font-semibold text-gray-900">Tendencia del Período</h2>
                <apexchart v-if="trendSeries.length" type="line" height="300" :options="trendOptions" :series="trendSeries" />
                <p v-else class="py-8 text-center text-sm text-gray-500">No hay datos suficientes para graficar.</p>
              </div>
            </section>

            <section class="fg-card p-4 sm:p-5">
              <div class="mb-4 flex flex-col gap-3 md:flex-row md:items-center md:justify-between">
                <div>
                  <h2 class="text-lg font-semibold text-gray-900">Avance Mensual vs Historico</h2>
                  <p class="text-sm text-gray-600">Mes actual contra el promedio de meses anteriores al mismo dia del mes.</p>
                </div>
                <span class="text-xs text-gray-600">Unidad de negocio + operacion + presentacion</span>
              </div>
              <div class="space-y-3 md:hidden">
                <div v-for="item in avanceMensualTop" :key="avanceKey(item)" class="rounded-md border border-gray-200 bg-white p-3">
                  <div class="mb-3 flex items-start justify-between gap-3">
                    <div>
                      <p class="text-sm font-semibold text-gray-900">{{ item.unidad_negocio }}</p>
                      <p class="text-xs text-gray-600">{{ item.tipo_operacion }} · {{ item.unidad_produccion }}</p>
                    </div>
                    <span :class="['shrink-0 rounded px-2 py-1 text-xs font-semibold', statusClass(item.estado)]">{{ statusLabel(item.estado) }}</span>
                  </div>
                  <div class="grid grid-cols-3 gap-2 text-sm">
                    <div>
                      <p class="text-xs text-gray-500">Actual</p>
                      <p class="font-semibold text-gray-900">{{ fmt(item.valor_actual) }}</p>
                    </div>
                    <div>
                      <p class="text-xs text-gray-500">Esperado</p>
                      <p class="font-semibold text-gray-900">{{ fmt(item.valor_esperado) }}</p>
                    </div>
                    <div>
                      <p class="text-xs text-gray-500">Desvio</p>
                      <p class="font-semibold text-gray-900">{{ avanceDiffLabel(item) }}</p>
                    </div>
                  </div>
                </div>
                <p v-if="!avanceMensualTop.length" class="py-8 text-center text-sm text-gray-500">No hay avance mensual para mostrar.</p>
              </div>
              <div class="hidden overflow-x-auto md:block">
                <table class="min-w-full divide-y divide-gray-200 text-sm">
                  <thead class="bg-blue-50">
                    <tr>
                      <th class="px-3 py-3 text-left text-xs font-medium uppercase text-blue-700">Unidad</th>
                      <th class="px-3 py-3 text-left text-xs font-medium uppercase text-blue-700">Operacion</th>
                      <th class="px-3 py-3 text-left text-xs font-medium uppercase text-blue-700">Presentacion</th>
                      <th class="px-3 py-3 text-right text-xs font-medium uppercase text-blue-700">Actual MTD</th>
                      <th class="px-3 py-3 text-right text-xs font-medium uppercase text-blue-700">Esperado MTD</th>
                      <th class="px-3 py-3 text-right text-xs font-medium uppercase text-blue-700">Desvio</th>
                      <th class="px-3 py-3 text-center text-xs font-medium uppercase text-blue-700">Estado</th>
                    </tr>
                  </thead>
                  <tbody class="divide-y divide-gray-100 bg-white">
                    <tr v-for="item in avanceMensualTop" :key="avanceKey(item)" class="hover:bg-gray-50">
                      <td class="px-3 py-2 text-gray-900">{{ item.unidad_negocio }}</td>
                      <td class="px-3 py-2 text-gray-700">{{ item.tipo_operacion }}</td>
                      <td class="px-3 py-2 text-gray-700">{{ item.unidad_produccion }}</td>
                      <td class="px-3 py-2 text-right text-gray-900">{{ fmt(item.valor_actual) }}</td>
                      <td class="px-3 py-2 text-right text-gray-900">{{ fmt(item.valor_esperado) }}</td>
                      <td class="px-3 py-2 text-right text-gray-900">{{ avanceDiffLabel(item) }}</td>
                      <td class="px-3 py-2 text-center">
                        <span :class="['rounded px-2 py-1 text-xs font-semibold', statusClass(item.estado)]">{{ statusLabel(item.estado) }}</span>
                      </td>
                    </tr>
                    <tr v-if="!avanceMensualTop.length">
                      <td colspan="7" class="px-3 py-8 text-center text-gray-500">No hay avance mensual para mostrar.</td>
                    </tr>
                  </tbody>
                </table>
              </div>
            </section>

            <section class="fg-card p-4 sm:p-5">
              <div class="mb-4 flex flex-col gap-3 md:flex-row md:items-center md:justify-between">
                <div>
                  <h2 class="text-lg font-semibold text-gray-900">Alertas Ejecutivas</h2>
                  <p class="text-sm text-gray-600">Combustible alto, baja producción y datos a revisar.</p>
                </div>
                <div class="flex flex-wrap gap-2 text-xs">
                  <span class="rounded bg-red-100 px-2 py-1 text-red-700">Rojas: {{ resumen.alertas_rojas || 0 }}</span>
                  <span class="rounded bg-amber-100 px-2 py-1 text-amber-800">Amarillas: {{ resumen.alertas_amarillas || 0 }}</span>
                </div>
              </div>
              <div class="space-y-2">
                <button
                  v-for="alerta in alertasTop"
                  :key="`${alerta.tipo}-${alerta.entidad}-${alerta.diferencia_pct}`"
                  class="w-full rounded-md border px-3 py-3 text-left transition hover:bg-gray-50"
                  :class="alertBorderClass(alerta.severidad)"
                  @click="openSegmentDetail(alerta.segmento)"
                >
                  <div class="flex flex-col gap-2 md:flex-row md:items-center md:justify-between">
                    <p class="text-sm font-medium text-gray-900">{{ alerta.mensaje }}</p>
                    <span :class="['self-start rounded px-2 py-1 text-xs font-semibold md:self-auto', statusClass(alerta.severidad)]">
                      {{ statusLabel(alerta.severidad) }}
                    </span>
                  </div>
                </button>
                <p v-if="!alertasTop.length" class="py-8 text-center text-sm text-gray-500">No hay alertas para los filtros seleccionados.</p>
              </div>
            </section>

            <section class="fg-card p-4 sm:p-5">
              <div class="mb-4 flex flex-col gap-3 md:flex-row md:items-center md:justify-between">
                <div>
                  <h2 class="text-lg font-semibold text-gray-900">Matriz de Segmentos</h2>
                  <p class="text-sm text-gray-600">Unidad de negocio + operación + unidad de producción + equipo.</p>
                </div>
                <input
                  v-model="segmentSearch"
                  type="search"
                  class="fg-input w-full md:w-72"
                  placeholder="Buscar segmento"
                />
              </div>
              <div class="space-y-3 md:hidden">
                <div v-for="segmento in filteredSegmentos" :key="segmentKey(segmento)" class="rounded-md border border-gray-200 bg-white p-3">
                  <div class="mb-3 flex items-start justify-between gap-3">
                    <div>
                      <p class="text-sm font-semibold text-gray-900">{{ segmento.equipo }}</p>
                      <p class="text-xs text-gray-600">{{ segmento.unidad_negocio }}</p>
                      <p class="text-xs text-gray-600">{{ segmento.tipo_operacion }} · {{ segmento.unidad_produccion }}</p>
                    </div>
                    <span :class="['shrink-0 rounded px-2 py-1 text-xs font-semibold', statusClass(segmento.estado)]">{{ statusLabel(segmento.estado) }}</span>
                  </div>
                  <div class="grid grid-cols-2 gap-2 text-sm">
                    <div>
                      <p class="text-xs text-gray-500">Produccion</p>
                      <p class="font-semibold text-gray-900">{{ fmt(segmento.produccion) }}</p>
                    </div>
                    <div>
                      <p class="text-xs text-gray-500">Horas</p>
                      <p class="font-semibold text-gray-900">{{ fmt(segmento.horas) }}</p>
                    </div>
                    <div>
                      <p class="text-xs text-gray-500">Comb.</p>
                      <p class="font-semibold text-gray-900">{{ fmt(segmento.combustible) }}</p>
                    </div>
                    <div>
                      <p class="text-xs text-gray-500">Ratio</p>
                      <p class="font-semibold text-gray-900">{{ ratioLabel(segmento) }}</p>
                    </div>
                  </div>
                  <button class="mt-3 text-sm font-medium text-green-700 hover:text-green-900" @click="openSegmentDetail(segmento)">
                    Ver detalle
                  </button>
                </div>
                <p v-if="!filteredSegmentos.length" class="py-8 text-center text-sm text-gray-500">No hay segmentos para mostrar.</p>
              </div>
              <div class="hidden overflow-x-auto md:block">
                <table class="min-w-full divide-y divide-gray-200 text-sm">
                  <thead class="bg-green-50">
                    <tr>
                      <th class="px-3 py-3 text-left text-xs font-medium uppercase text-green-700">Unidad</th>
                      <th class="px-3 py-3 text-left text-xs font-medium uppercase text-green-700">Operación</th>
                      <th class="px-3 py-3 text-left text-xs font-medium uppercase text-green-700">Presentación</th>
                      <th class="px-3 py-3 text-left text-xs font-medium uppercase text-green-700">Equipo</th>
                      <th class="px-3 py-3 text-right text-xs font-medium uppercase text-green-700">Producción</th>
                      <th class="px-3 py-3 text-right text-xs font-medium uppercase text-green-700">Horas</th>
                      <th class="px-3 py-3 text-right text-xs font-medium uppercase text-green-700">Comb.</th>
                      <th class="px-3 py-3 text-right text-xs font-medium uppercase text-green-700">Ratio</th>
                      <th class="px-3 py-3 text-center text-xs font-medium uppercase text-green-700">Estado</th>
                    </tr>
                  </thead>
                  <tbody class="divide-y divide-gray-100 bg-white">
                    <tr v-for="segmento in filteredSegmentos" :key="segmentKey(segmento)" class="hover:bg-gray-50">
                      <td class="px-3 py-2 text-gray-900">{{ segmento.unidad_negocio }}</td>
                      <td class="px-3 py-2 text-gray-700">{{ segmento.tipo_operacion }}</td>
                      <td class="px-3 py-2 text-gray-700">{{ segmento.unidad_produccion }}</td>
                      <td class="px-3 py-2 text-gray-700">
                        <button class="text-left font-medium text-green-700 hover:text-green-900" @click="openSegmentDetail(segmento)">
                          {{ segmento.equipo }}
                        </button>
                      </td>
                      <td class="px-3 py-2 text-right text-gray-900">{{ fmt(segmento.produccion) }}</td>
                      <td class="px-3 py-2 text-right text-gray-900">{{ fmt(segmento.horas) }}</td>
                      <td class="px-3 py-2 text-right text-gray-900">{{ fmt(segmento.combustible) }}</td>
                      <td class="px-3 py-2 text-right text-gray-900">{{ ratioLabel(segmento) }}</td>
                      <td class="px-3 py-2 text-center">
                        <span :class="['rounded px-2 py-1 text-xs font-semibold', statusClass(segmento.estado)]">{{ statusLabel(segmento.estado) }}</span>
                      </td>
                    </tr>
                    <tr v-if="!filteredSegmentos.length">
                      <td colspan="9" class="px-3 py-8 text-center text-gray-500">No hay segmentos para mostrar.</td>
                    </tr>
                  </tbody>
                </table>
              </div>
            </section>

            <section class="grid grid-cols-1 gap-6 xl:grid-cols-2">
              <RankingList title="Mayor desvío de combustible" :items="rankings.combustible" metric="combustible" @select="openSegmentDetail" />
              <RankingList title="Baja producción" :items="rankings.baja_produccion" metric="produccion" @select="openSegmentDetail" />
              <RankingList title="Avance mensual bajo" :items="rankings.avance_mensual" metric="avance" @select="openSegmentDetail" />
              <RankingList title="Horas no operativas" :items="rankings.horas_no_operativas" metric="no-operativas" @select="openSegmentDetail" />
              <RankingList title="Datos a revisar" :items="rankings.datos_a_revisar" metric="datos" @select="openSegmentDetail" />
            </section>
          </div>
        </div>
      </div>
    </main>

    <div v-if="detail.open" class="fixed inset-0 z-50 flex items-center justify-center bg-black bg-opacity-40 px-2 sm:px-4" @click.self="closeDetail">
      <div class="fg-card flex max-h-[90vh] w-full max-w-6xl flex-col">
        <div class="flex items-start justify-between gap-4 border-b px-4 py-3 sm:px-5 sm:py-4">
          <div>
            <h2 class="text-lg font-semibold text-gray-900">{{ detail.title }}</h2>
            <p class="text-sm text-gray-500">{{ detail.subtitle }}</p>
          </div>
          <button class="text-gray-500 hover:text-gray-800 text-2xl leading-none focus:outline-none focus:ring-2 focus:ring-green-300" aria-label="Cerrar detalle" @click="closeDetail">
            &times;
          </button>
        </div>
        <div class="overflow-auto px-4 py-4 sm:px-5">
          <p v-if="detail.error" role="alert" class="mb-3 text-sm text-red-600">{{ detail.error }}</p>
          <div v-if="detail.loading" class="py-10 text-center text-gray-500">Cargando registros...</div>
          <div v-else class="grid grid-cols-1 gap-6 xl:grid-cols-2">
            <DetailTable title="Producción" :rows="detail.produccion" type="produccion" />
            <DetailTable title="Combustible" :rows="detail.combustible" type="combustible" />
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import { computed, ref } from 'vue'
import NavBar from '../components/NavBar.vue'
import FilterSidebar from '../components/FilterSidebar.vue'
import ApexChart from 'vue3-apexcharts'

const RankingList = {
  props: {
    title: String,
    items: { type: Array, default: () => [] },
    metric: String,
  },
  emits: ['select'],
  methods: {
    fmt(value) {
      return Number(value || 0).toFixed(2)
    },
    metricValue(item) {
      if (this.metric === 'combustible') return `+${this.fmt(item.desvio_combustible_pct)}%`
      if (this.metric === 'produccion') return `-${this.fmt(item.desvio_produccion_pct)}%`
      if (this.metric === 'avance') return `-${this.fmt(item.diferencia_pct)}%`
      if (this.metric === 'no-operativas') return `${this.fmt(item.horas_no_operativas)} h`
      if (this.metric === 'datos') return item.estado === 'sin_historico' ? 'Sin histórico' : 'Revisar'
      return ''
    },
    itemTitle(item) {
      return item.equipo || item.unidad_negocio || 'Segmento'
    },
  },
  template: `
    <div class="fg-card p-4 sm:p-5">
      <h2 class="mb-4 text-lg font-semibold text-gray-900">{{ title }}</h2>
      <div class="space-y-2">
        <button
          v-for="item in items"
          :key="\`\${item.unidad_negocio_id}-\${item.tipo_operacion_id}-\${item.unidad_produccion_id}-\${item.equipo_id}-\${metric}\`"
          class="w-full rounded-md border border-gray-200 px-3 py-2 text-left transition hover:bg-gray-50"
          @click="$emit('select', item)"
        >
          <div class="flex items-center justify-between gap-3">
            <div>
              <p class="text-sm font-medium text-gray-900">{{ itemTitle(item) }}</p>
              <p class="text-xs text-gray-600">{{ item.unidad_negocio }} · {{ item.tipo_operacion }} · {{ item.unidad_produccion }}</p>
            </div>
            <p class="text-sm font-semibold text-gray-900">{{ metricValue(item) }}</p>
          </div>
        </button>
        <p v-if="!items.length" class="py-8 text-center text-sm text-gray-500">Sin datos.</p>
      </div>
    </div>
  `,
}

const DetailTable = {
  props: {
    title: String,
    rows: { type: Array, default: () => [] },
    type: String,
  },
  methods: {
    fmt(value) {
      return Number(value || 0).toFixed(2)
    },
  },
  template: `
    <div>
      <h3 class="mb-3 text-base font-semibold text-gray-900">{{ title }}</h3>
      <div class="space-y-2 md:hidden">
        <div v-for="row in rows" :key="\`card-\${type}-\${row.id}\`" class="rounded-md border border-gray-200 bg-white p-3">
          <template v-if="type === 'produccion'">
            <div class="mb-2 flex items-start justify-between gap-3">
              <p class="text-sm font-semibold text-gray-900">{{ row.fecha }}</p>
              <span class="rounded bg-green-100 px-2 py-1 text-xs font-semibold text-green-700">{{ row.turno || '-' }}</span>
            </div>
            <div class="grid grid-cols-2 gap-2 text-sm">
              <div>
                <p class="text-xs text-gray-500">Horas</p>
                <p class="font-semibold text-gray-900">{{ fmt(row.horas_trabajadas) }}</p>
              </div>
              <div>
                <p class="text-xs text-gray-500">Produccion</p>
                <p class="font-semibold text-gray-900">{{ fmt(row.produccion) }}</p>
              </div>
            </div>
          </template>
          <template v-else>
            <div class="mb-2 flex items-start justify-between gap-3">
              <p class="text-sm font-semibold text-gray-900">{{ row.fecha }}</p>
              <span class="rounded bg-amber-100 px-2 py-1 text-xs font-semibold text-amber-800">{{ row.remito || '-' }}</span>
            </div>
            <div class="grid grid-cols-2 gap-2 text-sm">
              <div>
                <p class="text-xs text-gray-500">Litros</p>
                <p class="font-semibold text-gray-900">{{ fmt(row.egreso) }}</p>
              </div>
              <div>
                <p class="text-xs text-gray-500">Km/Hora</p>
                <p class="font-semibold text-gray-900">{{ fmt(row.km_hora) }}</p>
              </div>
            </div>
          </template>
        </div>
        <p v-if="!rows.length" class="py-8 text-center text-gray-500">Sin registros.</p>
      </div>
      <div class="hidden overflow-x-auto md:block">
        <table class="min-w-full divide-y divide-gray-200 text-sm">
          <thead class="bg-gray-50">
            <tr v-if="type === 'produccion'">
              <th class="px-3 py-2 text-left text-xs font-medium uppercase text-gray-700">Fecha</th>
              <th class="px-3 py-2 text-right text-xs font-medium uppercase text-gray-700">Horas</th>
              <th class="px-3 py-2 text-right text-xs font-medium uppercase text-gray-700">Producción</th>
              <th class="px-3 py-2 text-left text-xs font-medium uppercase text-gray-700">Turno</th>
            </tr>
            <tr v-else>
              <th class="px-3 py-2 text-left text-xs font-medium uppercase text-gray-700">Fecha</th>
              <th class="px-3 py-2 text-right text-xs font-medium uppercase text-gray-700">Litros</th>
              <th class="px-3 py-2 text-right text-xs font-medium uppercase text-gray-700">Km/Hora</th>
              <th class="px-3 py-2 text-left text-xs font-medium uppercase text-gray-700">Remito</th>
            </tr>
          </thead>
          <tbody class="divide-y divide-gray-100 bg-white">
            <tr v-for="row in rows" :key="\`\${type}-\${row.id}\`">
              <template v-if="type === 'produccion'">
                <td class="px-3 py-2 whitespace-nowrap">{{ row.fecha }}</td>
                <td class="px-3 py-2 text-right">{{ fmt(row.horas_trabajadas) }}</td>
                <td class="px-3 py-2 text-right">{{ fmt(row.produccion) }}</td>
                <td class="px-3 py-2 whitespace-nowrap">{{ row.turno }}</td>
              </template>
              <template v-else>
                <td class="px-3 py-2 whitespace-nowrap">{{ row.fecha }}</td>
                <td class="px-3 py-2 text-right">{{ fmt(row.egreso) }}</td>
                <td class="px-3 py-2 text-right">{{ fmt(row.km_hora) }}</td>
                <td class="px-3 py-2 whitespace-nowrap">{{ row.remito }}</td>
              </template>
            </tr>
            <tr v-if="!rows.length">
              <td :colspan="4" class="px-3 py-8 text-center text-gray-500">Sin registros.</td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>
  `,
}

export default {
  name: 'DashboardView',
  components: { NavBar, FilterSidebar, apexchart: ApexChart, RankingList, DetailTable },
  setup() {
    const payload = ref(null)
    const loading = ref(false)
    const error = ref('')
    const currentFilters = ref({})
    const segmentSearch = ref('')
    const detail = ref({
      open: false,
      loading: false,
      error: '',
      title: '',
      subtitle: '',
      produccion: [],
      combustible: [],
    })

    const resumen = computed(() => payload.value?.resumen_general || {})
    const produccionPorUnidad = computed(() => payload.value?.produccion_por_unidad || [])
    const avanceMensual = computed(() => payload.value?.avance_mensual || [])
    const avanceMensualTop = computed(() => avanceMensual.value.slice(0, 10))
    const segmentos = computed(() => payload.value?.segmentos || [])
    const rankings = computed(() => payload.value?.rankings || {})
    const alertasTop = computed(() => (payload.value?.alertas || []).slice(0, 8))
    const isEmpty = computed(() => !loading.value && !error.value && payload.value && segmentos.value.length === 0)
    const periodoLabel = computed(() => {
      const periodo = payload.value?.periodo
      if (!periodo) return 'Esperando filtros'
      return `${periodo.fecha_desde} al ${periodo.fecha_hasta} · histórico: ${periodo.historico_desde} al ${periodo.historico_hasta}`
    })

    const filteredSegmentos = computed(() => {
      const term = segmentSearch.value.trim().toLowerCase()
      if (!term) return segmentos.value
      return segmentos.value.filter(item => [
        item.unidad_negocio,
        item.tipo_operacion,
        item.unidad_produccion,
        item.equipo,
      ].join(' ').toLowerCase().includes(term))
    })

    const trendSeries = computed(() => {
      const series = payload.value?.series
      if (!series?.fechas?.length) return []
      return [
        { name: 'Horas', data: series.horas || [] },
        { name: 'Combustible (L)', data: series.combustible || [] },
      ]
    })

    const trendOptions = computed(() => ({
      chart: { toolbar: { show: true }, zoom: { enabled: false } },
      xaxis: { categories: payload.value?.series?.fechas || [] },
      stroke: { curve: 'smooth', width: 3 },
      colors: ['#16a34a', '#f59e0b'],
      legend: { position: 'top' },
      dataLabels: { enabled: false },
    }))

    function fmt(value) {
      return Number(value || 0).toFixed(2)
    }

    function statusLabel(status) {
      const labels = {
        rojo: 'Crítico',
        amarillo: 'Atención',
        verde: 'Normal',
        sin_historico: 'Sin histórico',
      }
      return labels[status] || 'Sin datos'
    }

    function statusClass(status) {
      if (status === 'rojo') return 'bg-red-100 text-red-700'
      if (status === 'amarillo') return 'bg-amber-100 text-amber-800'
      if (status === 'verde') return 'bg-green-100 text-green-700'
      return 'bg-gray-100 text-gray-700'
    }

    function alertBorderClass(status) {
      if (status === 'rojo') return 'border-red-200'
      if (status === 'amarillo') return 'border-amber-200'
      return 'border-gray-200'
    }

    function ratioLabel(segmento) {
      if (segmento.metric_value == null) return '-'
      return `${fmt(segmento.metric_value)} ${segmento.metric_label}`
    }

    function avanceDiffLabel(item) {
      if (item.estado === 'sin_historico') return 'Sin historico'
      const value = Number(item.diferencia_pct || 0)
      return `${value >= 0 ? '-' : '+'}${Math.abs(value).toFixed(2)}%`
    }

    function avanceKey(item) {
      return `${item.unidad_negocio_id}-${item.tipo_operacion_id}-${item.unidad_produccion_id}`
    }

    function segmentKey(segmento) {
      return `${segmento.unidad_negocio_id}-${segmento.tipo_operacion_id}-${segmento.unidad_produccion_id}-${segmento.equipo_id}`
    }

    function appendCommonParams(params, filters) {
      if (filters.fecha_desde) params.append('fecha_desde', filters.fecha_desde)
      if (filters.fecha_hasta) params.append('fecha_hasta', filters.fecha_hasta)
      if (filters.unidad_negocio_id) params.append('unidad_negocio_id', filters.unidad_negocio_id)
      if (filters.tipo_operacion_id) params.append('tipo_operacion_id', filters.tipo_operacion_id)
      if (filters.unidad_produccion_id) params.append('unidad_produccion_id', filters.unidad_produccion_id)
      if (filters.equipo_id) params.append('equipo_id', filters.equipo_id)
      if (filters.empleado_id) params.append('empleado_id', filters.empleado_id)
    }

    async function loadData(filters = {}) {
      loading.value = true
      error.value = ''
      try {
        const API_BASE = import.meta.env.VITE_API_BASE || '/api'
        const params = new URLSearchParams()
        appendCommonParams(params, filters)
        const res = await fetch(`${API_BASE}/dashboard/ejecutivo/?${params.toString()}`, { credentials: 'include' })
        const json = await res.json().catch(() => ({}))
        if (!res.ok) throw new Error(json.detail || 'No se pudo cargar el dashboard ejecutivo.')
        payload.value = json
      } catch (err) {
        console.error('Error cargando dashboard ejecutivo:', err)
        error.value = err.message || 'Error de conexión al cargar el dashboard ejecutivo.'
        payload.value = null
      } finally {
        loading.value = false
      }
    }

    function onFilterChange(filters) {
      currentFilters.value = filters
      loadData(filters)
    }

    async function openSegmentDetail(segmento) {
      if (!segmento) return
      detail.value = {
        open: true,
        loading: true,
        error: '',
        title: segmento.equipo || segmento.unidad_negocio,
        subtitle: `${segmento.unidad_negocio} · ${segmento.tipo_operacion} · ${segmento.unidad_produccion}`,
        produccion: [],
        combustible: [],
      }

      try {
        const API_BASE = import.meta.env.VITE_API_BASE || '/api'
        const params = new URLSearchParams()
        appendCommonParams(params, {
          ...currentFilters.value,
          unidad_negocio_id: segmento.unidad_negocio_id,
          tipo_operacion_id: segmento.tipo_operacion_id,
          unidad_produccion_id: segmento.unidad_produccion_id,
          equipo_id: segmento.equipo_id,
        })
        params.append('page', '1')
        params.append('page_size', '100')

        const [prodRes, combRes] = await Promise.all([
          fetch(`${API_BASE}/produccion/detalle/?${params.toString()}`, { credentials: 'include' }),
          fetch(`${API_BASE}/combustible/detalle/?${params.toString()}`, { credentials: 'include' }),
        ])

        const prodJson = await prodRes.json().catch(() => ({}))
        const combJson = await combRes.json().catch(() => ({}))
        if (!prodRes.ok || !combRes.ok) throw new Error('No se pudieron cargar los registros del segmento.')

        detail.value.produccion = prodJson.detalle || []
        detail.value.combustible = combJson.detalle || []
      } catch (err) {
        console.error('Error cargando detalle de segmento:', err)
        detail.value.error = err.message || 'Error de conexión al cargar el detalle.'
      } finally {
        detail.value.loading = false
      }
    }

    function closeDetail() {
      detail.value.open = false
    }

    return {
      payload,
      loading,
      error,
      resumen,
      produccionPorUnidad,
      avanceMensualTop,
      rankings,
      alertasTop,
      isEmpty,
      periodoLabel,
      segmentSearch,
      filteredSegmentos,
      trendSeries,
      trendOptions,
      detail,
      fmt,
      statusLabel,
      statusClass,
      alertBorderClass,
      ratioLabel,
      avanceDiffLabel,
      avanceKey,
      segmentKey,
      onFilterChange,
      openSegmentDetail,
      closeDetail,
    }
  },
}
</script>

<style scoped>
</style>

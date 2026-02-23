<template>
  <div class="min-h-full bg-slate-50 p-6">
    <!-- Header: saludo + Nueva Cotización -->
    <div class="mb-6 flex flex-wrap items-center justify-between gap-4">
      <div>
        <h1 class="text-2xl font-bold text-gray-900">{{ saludo }}</h1>
        <p class="mt-0.5 text-sm text-gray-500">Centro de control operativo</p>
      </div>
      <div class="flex items-center gap-2">
        <button
          type="button"
          class="inline-flex items-center gap-2 rounded-lg border border-gray-300 bg-white px-3 py-1.5 text-sm font-medium text-gray-700 shadow-sm hover:bg-gray-50"
          :disabled="loading"
          @click="refreshDashboard"
        >
          <Loader2 v-if="loading" class="h-4 w-4 animate-spin" />
          Actualizar
        </button>
        <router-link
          to="/comercial/consultas"
          class="inline-flex items-center gap-2 rounded-lg bg-indigo-600 px-4 py-2 text-sm font-medium text-white shadow-sm hover:bg-indigo-700"
        >
          <PlusCircle class="h-5 w-5" />
          Nueva Cotización
        </router-link>
      </div>
    </div>

    <div v-if="loading" class="flex items-center justify-center py-20">
      <Loader2 class="h-8 w-8 animate-spin text-indigo-500" />
    </div>
    <div v-else-if="error" class="rounded-xl border border-red-200 bg-red-50 p-6 text-center text-sm text-red-600">
      {{ error }}
    </div>
    <template v-else>
      <!-- KPIs operativos -->
      <div class="mb-6 grid grid-cols-2 gap-3 sm:grid-cols-4 lg:grid-cols-5 xl:grid-cols-7">
        <div class="rounded-xl border border-gray-200 bg-white p-4 shadow-sm">
          <p class="text-xs font-medium uppercase tracking-wider text-gray-500">OT activas</p>
          <p class="mt-1 text-2xl font-bold text-gray-900">{{ data.kpis?.active_count ?? "—" }}</p>
        </div>
        <div class="rounded-xl border border-gray-200 bg-white p-4 shadow-sm">
          <p class="text-xs font-medium uppercase tracking-wider text-gray-500">Nuevas</p>
          <p class="mt-1 text-2xl font-bold text-gray-900">{{ data.kpis?.new_count ?? "—" }}</p>
        </div>
        <div class="rounded-xl border border-gray-200 bg-white p-4 shadow-sm">
          <p class="text-xs font-medium uppercase tracking-wider text-gray-500">Diseño</p>
          <p class="mt-1 text-2xl font-bold text-gray-900">{{ data.kpis?.design_count ?? "—" }}</p>
        </div>
        <div class="rounded-xl border border-amber-200 bg-amber-50/50 p-4 shadow-sm">
          <p class="text-xs font-medium uppercase tracking-wider text-amber-700">Esperando aprobación</p>
          <p class="mt-1 text-2xl font-bold text-amber-800">{{ data.kpis?.waiting_approval_count ?? "—" }}</p>
        </div>
        <div class="rounded-xl border border-gray-200 bg-white p-4 shadow-sm">
          <p class="text-xs font-medium uppercase tracking-wider text-gray-500">Aprobadas</p>
          <p class="mt-1 text-2xl font-bold text-gray-900">{{ data.kpis?.approved_count ?? "—" }}</p>
        </div>
        <div class="rounded-xl border border-blue-200 bg-blue-50/50 p-4 shadow-sm">
          <p class="text-xs font-medium uppercase tracking-wider text-blue-700">En producción</p>
          <p class="mt-1 text-2xl font-bold text-blue-800">{{ data.kpis?.production_count ?? "—" }}</p>
        </div>
        <div class="rounded-xl border border-gray-200 bg-white p-4 shadow-sm">
          <p class="text-xs font-medium uppercase tracking-wider text-gray-500">Hechas</p>
          <p class="mt-1 text-2xl font-bold text-gray-900">{{ data.kpis?.done_count ?? "—" }}</p>
        </div>
        <div class="rounded-xl border border-gray-200 bg-white p-4 shadow-sm">
          <p class="text-xs font-medium uppercase tracking-wider text-gray-500">Entregas hoy</p>
          <p class="mt-1 text-2xl font-bold text-emerald-600">{{ data.kpis?.deliveries_today_count ?? "—" }}</p>
        </div>
        <div class="rounded-xl border border-red-200 bg-red-50/50 p-4 shadow-sm">
          <p class="text-xs font-medium uppercase tracking-wider text-red-700">Atrasadas</p>
          <p class="mt-1 text-2xl font-bold text-red-800">{{ data.kpis?.overdue_deliveries_count ?? "—" }}</p>
        </div>
        <div class="rounded-xl border border-gray-200 bg-white p-4 shadow-sm">
          <p class="text-xs font-medium uppercase tracking-wider text-gray-500">Terc. pendiente proveedor</p>
          <p class="mt-1 text-2xl font-bold text-gray-900">{{ data.kpis?.outsource_pending_vendor_count ?? "—" }}</p>
        </div>
        <div class="rounded-xl border border-gray-200 bg-white p-4 shadow-sm">
          <p class="text-xs font-medium uppercase tracking-wider text-gray-500">Terc. enviadas</p>
          <p class="mt-1 text-2xl font-bold text-gray-900">{{ data.kpis?.outsource_sent_count ?? "—" }}</p>
        </div>
        <div class="rounded-xl border border-red-200 bg-red-50 p-4 shadow-sm">
          <p class="text-xs font-medium uppercase tracking-wider text-red-700">Alertas peligro</p>
          <p class="mt-1 text-2xl font-bold text-red-800">{{ data.kpis?.danger_alerts_count ?? "—" }}</p>
        </div>
        <div class="rounded-xl border border-amber-200 bg-amber-50 p-4 shadow-sm">
          <p class="text-xs font-medium uppercase tracking-wider text-amber-700">Alertas advertencia</p>
          <p class="mt-1 text-2xl font-bold text-amber-800">{{ data.kpis?.warning_alerts_count ?? "—" }}</p>
        </div>
      </div>

      <!-- KPIs financieros (solo si el plan incluye finanzas) -->
      <div v-if="data.kpis?.revenue_period != null" class="mb-8 grid grid-cols-1 gap-3 sm:grid-cols-3">
        <div class="rounded-xl border border-gray-200 bg-white p-4 shadow-sm">
          <p class="text-xs font-medium uppercase tracking-wider text-gray-500">Ventas período</p>
          <p class="mt-1 text-xl font-bold text-gray-900">{{ formatCurrency(data.kpis.revenue_period) }}</p>
        </div>
        <div class="rounded-xl border border-gray-200 bg-white p-4 shadow-sm">
          <p class="text-xs font-medium uppercase tracking-wider text-gray-500">Margen total período</p>
          <p class="mt-1 text-xl font-bold" :class="(data.kpis.total_margin_period ?? 0) >= 0 ? 'text-emerald-600' : 'text-red-600'">
            {{ formatCurrency(data.kpis.total_margin_period) }}
          </p>
        </div>
        <div class="rounded-xl border border-gray-200 bg-white p-4 shadow-sm">
          <p class="text-xs font-medium uppercase tracking-wider text-gray-500">Margen % período</p>
          <p class="mt-1 text-xl font-bold" :class="marginClass(data.kpis.avg_margin_pct_period)">
            {{ (data.kpis.avg_margin_pct_period ?? 0).toFixed(1) }}%
          </p>
        </div>
      </div>

      <!-- 4 secciones con tablas -->
      <div class="grid grid-cols-1 gap-6 lg:grid-cols-2">
        <!-- Urgentes -->
        <div class="rounded-xl border border-gray-200 bg-white shadow-sm">
          <h2 class="border-b border-gray-200 px-4 py-3 text-sm font-semibold text-gray-900">Urgentes (entrega más próxima)</h2>
          <div class="overflow-x-auto">
            <table class="min-w-full divide-y divide-gray-200">
              <thead class="bg-gray-50">
                <tr>
                  <th class="px-3 py-2 text-left text-xs font-medium uppercase text-gray-500">OT / Cliente</th>
                  <th class="px-3 py-2 text-left text-xs font-medium uppercase text-gray-500">Entrega</th>
                  <th class="px-3 py-2 text-left text-xs font-medium uppercase text-gray-500">Estado</th>
                  <th class="px-3 py-2 text-right text-xs font-medium uppercase text-gray-500">Margen</th>
                  <th class="px-3 py-2 text-right text-xs font-medium uppercase text-gray-500 w-40">Acciones</th>
                </tr>
              </thead>
              <tbody class="divide-y divide-gray-200 bg-white">
                <tr
                  v-for="row in data.urgent"
                  :key="row.work_order_id"
                  class="hover:bg-indigo-50/50 transition-colors"
                  :class="[
                    { 'border-l-4 border-red-500': isOverdue(row.delivery_date) },
                    { 'bg-orange-50': isDueToday(row.delivery_date) },
                    { 'bg-red-50': isNegativeMargin(row.gross_margin_pct) },
                    { 'bg-indigo-50/30': loadingRowId === row.work_order_id }
                  ]"
                >
                  <td class="px-3 py-2 cursor-pointer" @click="openQuickView(row)">
                    <span class="block font-mono text-sm text-gray-900">{{ row.work_order_id }}</span>
                    <span class="block text-xs text-gray-600">{{ row.customer_name || "—" }}</span>
                  </td>
                  <td class="whitespace-nowrap px-3 py-2 text-sm text-gray-600 cursor-pointer" @click="openQuickView(row)">{{ formatDate(row.delivery_date) }}</td>
                  <td class="whitespace-nowrap px-3 py-2 cursor-pointer" @click="openQuickView(row)">
                    <span class="inline-flex items-center gap-1">
                      <span class="inline-flex rounded px-2 py-0.5 text-xs font-medium" :class="statusBadgeClass(row.status)">{{ row.status || "—" }}</span>
                      <AlertTriangle v-if="(row.alerts_summary?.danger || 0) > 0" class="h-4 w-4 shrink-0 text-red-500 animate-pulse" title="Alertas peligro" />
                      <span v-else-if="(row.alerts_summary?.warning || 0) > 0" class="rounded-full bg-amber-500 h-2 w-2" title="Alertas advertencia" />
                    </span>
                  </td>
                  <td class="whitespace-nowrap px-3 py-2 text-right text-sm font-medium cursor-pointer" :class="isLowMargin(row.gross_margin_pct) ? 'text-red-500 font-semibold' : marginClass(row.gross_margin_pct)" @click="openQuickView(row)">{{ (row.gross_margin_pct ?? 0).toFixed(1) }}%</td>
                  <td class="px-3 py-2 text-right" @click.stop>
                    <div class="flex flex-wrap items-center justify-end gap-1">
                      <template v-if="(row.status || '').toLowerCase() === 'approved'">
                        <button type="button" class="rounded bg-blue-600 px-2 py-1 text-xs text-white hover:bg-blue-700 disabled:opacity-50" :disabled="loadingRowId === row.work_order_id" @click="confirmAction('start_production', row, 'urgent')">
                          <Loader2 v-if="loadingRowId === row.work_order_id" class="h-3 w-3 animate-spin inline" />
                          <Play v-else class="h-3 w-3 inline" />
                          Iniciar
                        </button>
                      </template>
                      <template v-else-if="(row.status || '').toLowerCase() === 'production'">
                        <button type="button" class="rounded bg-emerald-600 px-2 py-1 text-xs text-white hover:bg-emerald-700 disabled:opacity-50" :disabled="loadingRowId === row.work_order_id" @click="confirmAction('finish', row, 'urgent')">
                          <Loader2 v-if="loadingRowId === row.work_order_id" class="h-3 w-3 animate-spin inline" />
                          Finalizar
                        </button>
                      </template>
                      <select class="rounded border border-gray-300 text-xs py-1 pr-6 bg-white" @change="onAssign(row, $event.target.value); $event.target.value = ''">
                        <option value="">Asignar a</option>
                        <option v-for="u in systemUsers" :key="u.name" :value="u.name">{{ u.full_name || u.name }}</option>
                      </select>
                    </div>
                  </td>
                </tr>
                <tr v-if="!(data.urgent || []).length">
                  <td colspan="5" class="px-3 py-8 text-center text-sm text-gray-500">No hay pendientes.</td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>

        <!-- Alertas críticas -->
        <div class="rounded-xl border border-red-200 bg-white shadow-sm">
          <h2 class="border-b border-red-200 bg-red-50 px-4 py-3 text-sm font-semibold text-red-900">Alertas críticas</h2>
          <div class="overflow-x-auto">
            <table class="min-w-full divide-y divide-gray-200">
              <thead class="bg-gray-50">
                <tr>
                  <th class="px-3 py-2 text-left text-xs font-medium uppercase text-gray-500">OT / Cliente</th>
                  <th class="px-3 py-2 text-left text-xs font-medium uppercase text-gray-500">Entrega</th>
                  <th class="px-3 py-2 text-left text-xs font-medium uppercase text-gray-500">Alerta</th>
                  <th class="px-3 py-2 text-right text-xs font-medium uppercase text-gray-500 w-32">Acciones</th>
                </tr>
              </thead>
              <tbody class="divide-y divide-gray-200 bg-white">
                <tr
                  v-for="row in data.critical_alerts"
                  :key="row.work_order_id"
                  class="hover:bg-red-50/50 transition-colors"
                  :class="[
                    { 'border-l-4 border-red-500': isOverdue(row.delivery_date) },
                    { 'bg-orange-50': isDueToday(row.delivery_date) },
                    { 'bg-red-50': isNegativeMargin(row.gross_margin_pct) },
                    { 'bg-red-50/30': loadingRowId === row.work_order_id }
                  ]"
                >
                  <td class="px-3 py-2 cursor-pointer" @click="openQuickView(row)">
                    <span class="block font-mono text-sm text-gray-900">{{ row.work_order_id }}</span>
                    <span class="block text-xs text-gray-600">{{ row.customer_name || "—" }}</span>
                  </td>
                  <td class="whitespace-nowrap px-3 py-2 text-sm text-gray-600 cursor-pointer" @click="openQuickView(row)">{{ formatDate(row.delivery_date) }}</td>
                  <td class="px-3 py-2 text-sm text-red-700 cursor-pointer" @click="openQuickView(row)">
                    <span class="inline-flex items-center gap-1">
                      <AlertTriangle v-if="(row.alerts_summary?.danger || 0) > 0" class="h-4 w-4 shrink-0 text-red-500 animate-pulse" title="Alertas peligro" />
                      {{ row.top_alert_title || "—" }}
                    </span>
                  </td>
                  <td class="px-3 py-2 text-right" @click.stop>
                    <select class="rounded border border-gray-300 text-xs py-1 pr-6 bg-white" @change="onAssign(row, $event.target.value); $event.target.value = ''">
                      <option value="">Asignar a</option>
                      <option v-for="u in systemUsers" :key="u.name" :value="u.name">{{ u.full_name || u.name }}</option>
                    </select>
                  </td>
                </tr>
                <tr v-if="!(data.critical_alerts || []).length">
                  <td colspan="4" class="px-3 py-8 text-center text-sm text-gray-500">No hay pendientes.</td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>

        <!-- Esperando aprobación -->
        <div class="rounded-xl border border-amber-200 bg-white shadow-sm">
          <h2 class="border-b border-amber-200 bg-amber-50 px-4 py-3 text-sm font-semibold text-amber-900">Esperando aprobación</h2>
          <div class="overflow-x-auto">
            <table class="min-w-full divide-y divide-gray-200">
              <thead class="bg-gray-50">
                <tr>
                  <th class="px-3 py-2 text-left text-xs font-medium uppercase text-gray-500">OT / Cliente</th>
                  <th class="px-3 py-2 text-left text-xs font-medium uppercase text-gray-500">Entrega</th>
                  <th class="px-3 py-2 text-left text-xs font-medium uppercase text-gray-500">Tiempo / Alerta</th>
                  <th class="px-3 py-2 text-right text-xs font-medium uppercase text-gray-500 w-44">Acciones</th>
                </tr>
              </thead>
              <tbody class="divide-y divide-gray-200 bg-white">
                <tr
                  v-for="row in data.waiting_approval_oldest"
                  :key="row.work_order_id"
                  class="hover:bg-amber-50/50 transition-colors"
                  :class="[
                    { 'border-l-4 border-red-500': isOverdue(row.delivery_date) },
                    { 'bg-orange-50': isDueToday(row.delivery_date) },
                    { 'bg-red-50': isNegativeMargin(row.gross_margin_pct) },
                    { 'bg-amber-50/50': loadingRowId === row.work_order_id }
                  ]"
                >
                  <td class="px-3 py-2 cursor-pointer" @click="openQuickView(row)">
                    <span class="block font-mono text-sm text-gray-900">{{ row.work_order_id }}</span>
                    <span class="block text-xs text-gray-600">{{ row.customer_name || "—" }}</span>
                  </td>
                  <td class="whitespace-nowrap px-3 py-2 text-sm text-gray-600 cursor-pointer" @click="openQuickView(row)">{{ formatDate(row.delivery_date) }}</td>
                  <td class="px-3 py-2 text-sm text-amber-700 cursor-pointer" @click="openQuickView(row)">
                    <span class="inline-flex items-center gap-1">
                      <AlertTriangle v-if="(row.alerts_summary?.danger || 0) > 0" class="h-4 w-4 shrink-0 text-red-500 animate-pulse" title="Alertas peligro" />
                      <span>
                        <span v-if="row.time_in_status_days != null" class="block">Hace {{ row.time_in_status_days }} día(s)</span>
                        <span class="block text-gray-600">{{ row.top_alert_title || "—" }}</span>
                      </span>
                    </span>
                  </td>
                  <td class="px-3 py-2 text-right" @click.stop>
                    <div class="flex flex-wrap items-center justify-end gap-1">
                      <button type="button" class="rounded bg-emerald-600 px-2 py-1 text-xs text-white hover:bg-emerald-700 disabled:opacity-50" :disabled="loadingRowId === row.work_order_id" @click="confirmAction('approve', row, 'waiting_approval_oldest')">
                        <Loader2 v-if="loadingRowId === row.work_order_id" class="h-3 w-3 animate-spin inline" />
                        Aprobar
                      </button>
                      <button type="button" class="rounded border border-amber-600 px-2 py-1 text-xs text-amber-800 hover:bg-amber-50 disabled:opacity-50" :disabled="loadingRowId === row.work_order_id" @click="confirmAction('reject', row, 'waiting_approval_oldest')">
                        Rechazar
                      </button>
                      <select class="rounded border border-gray-300 text-xs py-1 pr-6 bg-white" @change="onAssign(row, $event.target.value); $event.target.value = ''">
                        <option value="">Asignar a</option>
                        <option v-for="u in systemUsers" :key="u.name" :value="u.name">{{ u.full_name || u.name }}</option>
                      </select>
                    </div>
                  </td>
                </tr>
                <tr v-if="!(data.waiting_approval_oldest || []).length">
                  <td colspan="4" class="px-3 py-8 text-center text-sm text-gray-500">No hay pendientes.</td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>

        <!-- Tercerización vencida -->
        <div class="rounded-xl border border-gray-200 bg-white shadow-sm">
          <h2 class="border-b border-gray-200 px-4 py-3 text-sm font-semibold text-gray-900">Tercerización vencida</h2>
          <div class="overflow-x-auto">
            <table class="min-w-full divide-y divide-gray-200">
              <thead class="bg-gray-50">
                <tr>
                  <th class="px-3 py-2 text-left text-xs font-medium uppercase text-gray-500">OT / Cliente</th>
                  <th class="px-3 py-2 text-left text-xs font-medium uppercase text-gray-500">Entrega</th>
                  <th class="px-3 py-2 text-left text-xs font-medium uppercase text-gray-500">Estado / Tiempo</th>
                  <th class="px-3 py-2 text-right text-xs font-medium uppercase text-gray-500 w-44">Acciones</th>
                </tr>
              </thead>
              <tbody class="divide-y divide-gray-200 bg-white">
                <tr
                  v-for="row in data.outsourcing_overdue"
                  :key="row.work_order_id"
                  class="hover:bg-gray-50 transition-colors"
                  :class="[
                    { 'border-l-4 border-red-500': isOverdue(row.delivery_date) },
                    { 'bg-orange-50': isDueToday(row.delivery_date) },
                    { 'bg-red-50': isNegativeMargin(row.gross_margin_pct) },
                    { 'bg-gray-100': loadingRowId === row.work_order_id }
                  ]"
                >
                  <td class="px-3 py-2 cursor-pointer" @click="openQuickView(row)">
                    <span class="block font-mono text-sm text-gray-900">{{ row.work_order_id }}</span>
                    <span class="block text-xs text-gray-600">{{ row.customer_name || "—" }}</span>
                  </td>
                  <td class="whitespace-nowrap px-3 py-2 text-sm text-gray-600 cursor-pointer" @click="openQuickView(row)">{{ formatDate(row.delivery_date) }}</td>
                  <td class="px-3 py-2 cursor-pointer" @click="openQuickView(row)">
                    <span class="inline-flex items-center gap-1">
                      <span class="inline-flex rounded px-2 py-0.5 text-xs font-medium" :class="statusBadgeClass(row.status)">{{ row.status || "—" }}</span>
                      <AlertTriangle v-if="(row.alerts_summary?.danger || 0) > 0" class="h-4 w-4 shrink-0 text-red-500 animate-pulse" title="Alertas peligro" />
                      <span v-if="row.time_in_status_days != null" class="text-xs text-gray-600">Hace {{ row.time_in_status_days }} día(s) enviado</span>
                    </span>
                  </td>
                  <td class="px-3 py-2 text-right" @click.stop>
                    <div class="flex flex-wrap items-center justify-end gap-1">
                      <button type="button" class="rounded bg-emerald-600 px-2 py-1 text-xs text-white hover:bg-emerald-700 disabled:opacity-50" :disabled="loadingRowId === row.work_order_id" @click="onMarkReceived(row)">
                        <Loader2 v-if="loadingRowId === row.work_order_id" class="h-3 w-3 animate-spin inline" />
                        Marcar recibido
                      </button>
                      <router-link :to="'/orden/' + (row.sales_order || '')" class="rounded border border-gray-400 px-2 py-1 text-xs text-gray-700 hover:bg-gray-100" @click.native.stop>Ver orden</router-link>
                      <select class="rounded border border-gray-300 text-xs py-1 pr-6 bg-white" @change="onAssign(row, $event.target.value); $event.target.value = ''">
                        <option value="">Asignar a</option>
                        <option v-for="u in systemUsers" :key="u.name" :value="u.name">{{ u.full_name || u.name }}</option>
                      </select>
                    </div>
                  </td>
                </tr>
                <tr v-if="!(data.outsourcing_overdue || []).length">
                  <td colspan="4" class="px-3 py-8 text-center text-sm text-gray-500">No hay pendientes.</td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>
      </div>

      <!-- Modal confirmación -->
      <div v-if="confirmModal" class="fixed inset-0 z-50 flex items-center justify-center bg-black/50 p-4" @click.self="confirmModal = null">
        <div class="w-full max-w-sm rounded-lg bg-white p-4 shadow-xl">
          <p class="font-medium text-gray-900">{{ confirmModal.title }}</p>
          <p class="mt-1 text-sm text-gray-600">{{ confirmModal.message }}</p>
          <div class="mt-4 flex justify-end gap-2">
            <button type="button" class="rounded border border-gray-300 px-3 py-1.5 text-sm font-medium text-gray-700 hover:bg-gray-50" @click="confirmModal = null">Cancelar</button>
            <button type="button" class="rounded bg-indigo-600 px-3 py-1.5 text-sm font-medium text-white hover:bg-indigo-700" :disabled="confirmModal.loading" @click="runConfirmAction">
              <Loader2 v-if="confirmModal.loading" class="h-4 w-4 animate-spin inline" />
              {{ confirmModal.confirmLabel || "Confirmar" }}
            </button>
          </div>
        </div>
      </div>

      <!-- Quick View lateral (Fase 8) -->
      <QuickViewWorkOrder
        :work-order-id="quickViewId"
        :visible="quickViewVisible"
        @close="quickViewVisible = false"
      />

      <!-- Toast -->
      <Transition name="toast">
        <div
          v-if="toastVisible"
          class="fixed bottom-6 left-1/2 z-[60] -translate-x-1/2 rounded-lg px-4 py-2.5 text-sm font-medium text-white shadow-lg"
          :class="toastError ? 'bg-red-600' : 'bg-emerald-600'"
          role="alert"
        >
          {{ toastMessage }}
        </div>
      </Transition>
    </template>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from "vue";
import { useRouter } from "vue-router";
import { Loader2, PlusCircle, Play, AlertTriangle } from "lucide-vue-next";
import { call, getSession } from "@/api/frappe";
import QuickViewWorkOrder from "@/components/QuickViewWorkOrder.vue";

const router = useRouter();
const quickViewId = ref(null);
const quickViewVisible = ref(false);
const loading = ref(true);
const error = ref(null);
const sessionUser = ref(null);
const loadingRowId = ref(null);
const systemUsers = ref([]);
const confirmModal = ref(null);
const toastVisible = ref(false);
const toastMessage = ref("");
const toastError = ref(false);

const data = ref({
  kpis: {},
  urgent: [],
  critical_alerts: [],
  waiting_approval_oldest: [],
  outsourcing_overdue: [],
});

const saludo = computed(() => {
  const u = sessionUser.value;
  const name = u && typeof u === "string" ? u.split("@")[0] : "";
  const hour = new Date().getHours();
  const parte = hour < 12 ? "Buenos días" : hour < 19 ? "Buenas tardes" : "Buenas noches";
  return name ? `${parte}, ${name}` : parte;
});

function showToast(message, isError = false) {
  toastMessage.value = message;
  toastError.value = isError;
  toastVisible.value = true;
  setTimeout(() => { toastVisible.value = false; }, 3000);
}

function formatDate(val) {
  if (!val) return "—";
  try {
    const d = new Date(val);
    return d.toLocaleDateString("es-AR", { day: "2-digit", month: "2-digit", year: "numeric" });
  } catch (_) {
    return String(val);
  }
}

function formatCurrency(value) {
  if (value == null || value === "") return "—";
  return new Intl.NumberFormat("es-AR", { style: "currency", currency: "ARS", minimumFractionDigits: 0, maximumFractionDigits: 0 }).format(value);
}

function goToOrder(salesOrderId) {
  if (salesOrderId) router.push({ path: "/orden/" + salesOrderId });
}

function openQuickView(row) {
  const id = row?.work_order_id || row?.name;
  if (id) {
    quickViewId.value = id;
    quickViewVisible.value = true;
  }
}

function statusBadgeClass(status) {
  if (!status) return "bg-gray-100 text-gray-600";
  const s = String(status).toLowerCase();
  if (["done", "delivered"].includes(s)) return "bg-emerald-100 text-emerald-800";
  if (s === "production") return "bg-blue-100 text-blue-800";
  if (s === "waitingapproval") return "bg-amber-100 text-amber-800";
  if (s === "approved") return "bg-green-100 text-green-800";
  return "bg-gray-100 text-gray-600";
}

function marginClass(pct) {
  if (pct == null) return "text-gray-600";
  if (pct >= 25) return "text-emerald-600";
  if (pct >= 15) return "text-amber-600";
  return "text-red-600";
}

/** Fase 8B: indicadores visuales de urgencia y margen */
function isOverdue(delivery_date) {
  if (!delivery_date) return false;
  try {
    const today = new Date();
    today.setHours(0, 0, 0, 0);
    const d = new Date(delivery_date);
    if (Number.isNaN(d.getTime())) return false;
    d.setHours(0, 0, 0, 0);
    return d.getTime() < today.getTime();
  } catch (_) {
    return false;
  }
}

function isDueToday(delivery_date) {
  if (!delivery_date) return false;
  try {
    const today = new Date();
    today.setHours(0, 0, 0, 0);
    const d = new Date(delivery_date);
    if (Number.isNaN(d.getTime())) return false;
    d.setHours(0, 0, 0, 0);
    return d.getTime() === today.getTime();
  } catch (_) {
    return false;
  }
}

function isLowMargin(margin_pct) {
  return margin_pct != null && Number(margin_pct) < 15;
}

function isNegativeMargin(margin_pct) {
  return margin_pct != null && Number(margin_pct) < 0;
}

/** Actualiza una fila por work_order_id en la lista que corresponda (solo esa fila). */
function updateRowFromResponse(workOrderId, payload) {
  const id = workOrderId || payload?.work_order_id || payload?.name;
  if (!id) return;
  const keys = ["urgent", "critical_alerts", "waiting_approval_oldest", "outsourcing_overdue"];
  for (const key of keys) {
    const arr = data.value[key] || [];
    const idx = arr.findIndex((r) => (r.work_order_id || r.name) === id);
    if (idx >= 0) {
      const next = [...arr];
      next[idx] = { ...next[idx], ...payload, status: payload.new_status ?? payload.status ?? next[idx].status, alerts_summary: payload.alerts_summary ?? next[idx].alerts_summary };
      data.value = { ...data.value, [key]: next };
      break;
    }
  }
}

/** Quitar fila de una lista (ej. al aprobar sale de waiting_approval_oldest). */
function removeRowFromList(workOrderId, listKey) {
  const arr = data.value[listKey] || [];
  const next = arr.filter((r) => (r.work_order_id || r.name) !== workOrderId);
  data.value = { ...data.value, [listKey]: next };
}

function confirmAction(action, row, listKey) {
  const titles = {
    approve: "Aprobar OT",
    reject: "Rechazar aprobación",
    start_production: "Iniciar producción",
    finish: "Finalizar OT",
  };
  const messages = {
    approve: `¿Aprobar la OT ${row.work_order_id}?`,
    reject: `¿Devolver la OT ${row.work_order_id} a Diseño?`,
    start_production: `¿Iniciar producción de ${row.work_order_id}?`,
    finish: `¿Marcar como finalizada la OT ${row.work_order_id}?`,
  };
  confirmModal.value = { action, row, listKey, title: titles[action] || "Confirmar", message: messages[action] || "¿Continuar?", loading: false, confirmLabel: action === "reject" ? "Rechazar" : "Confirmar" };
}

async function runConfirmAction() {
  if (!confirmModal.value) return;
  const { action, row, listKey } = confirmModal.value;
  confirmModal.value.loading = true;
  loadingRowId.value = row.work_order_id;
  try {
    let res;
    if (action === "approve") {
      res = await call("mathipe_ui.api.approve_work_order", { work_order_id: row.work_order_id, comment: "" });
    } else if (action === "reject") {
      res = await call("mathipe_ui.api.update_work_order_status", { work_order_id: row.work_order_id, to_status: "Design", comment: "Rechazado desde dashboard" });
    } else if (action === "start_production") {
      res = await call("mathipe_ui.api.update_work_order_status", { work_order_id: row.work_order_id, to_status: "Production", comment: "" });
    } else if (action === "finish") {
      res = await call("mathipe_ui.api.update_work_order_status", { work_order_id: row.work_order_id, to_status: "Done", comment: "" });
    }
    const detail = res?.message ?? res ?? {};
    updateRowFromResponse(row.work_order_id, { new_status: detail.new_status ?? detail.status, alerts_summary: detail.alerts_summary });
    if (action === "approve" || action === "reject") removeRowFromList(row.work_order_id, listKey);
    showToast(action === "approve" ? "OT aprobada." : action === "reject" ? "Devolvida a Diseño." : action === "start_production" ? "Producción iniciada." : "OT finalizada.");
  } catch (e) {
    showToast(e.message || "Error al ejecutar.", true);
  } finally {
    loadingRowId.value = null;
    confirmModal.value = null;
  }
}

async function onAssign(row, userId) {
  if (!userId) return;
  loadingRowId.value = row.work_order_id;
  try {
    const res = await call("mathipe_ui.api.update_work_order_assignments", { work_order_id: row.work_order_id, user_ids: [userId] });
    const detail = res?.message ?? res ?? {};
    updateRowFromResponse(row.work_order_id, { new_status: detail.new_status ?? detail.status, alerts_summary: detail.alerts_summary });
    showToast("Asignación actualizada.");
  } catch (e) {
    showToast(e.message || "Error al asignar.", true);
  } finally {
    loadingRowId.value = null;
  }
}

async function onMarkReceived(row) {
  loadingRowId.value = row.work_order_id;
  try {
    const itemsRes = await call("mathipe_ui.api.get_work_order_items", { work_order_id: row.work_order_id });
    const items = itemsRes?.message ?? itemsRes ?? [];
    const sentItem = Array.isArray(items) ? items.find((i) => i.is_outsourced && (i.outsource_status || "").toLowerCase() === "sent") : null;
    if (!sentItem || !sentItem.name) {
      showToast("No hay ítem tercerizado en estado Enviado.", true);
      return;
    }
    const res = await call("mathipe_ui.api.update_outsource_status", { work_order_id: row.work_order_id, item_row_id: sentItem.name, action: "received" });
    const detail = res?.message ?? res ?? {};
    updateRowFromResponse(row.work_order_id, { new_status: detail.new_status ?? detail.status, alerts_summary: detail.alerts_summary });
    removeRowFromList(row.work_order_id, "outsourcing_overdue");
    showToast("Marcado como recibido.");
  } catch (e) {
    showToast(e.message || "Error al marcar recibido.", true);
  } finally {
    loadingRowId.value = null;
  }
}

function refreshDashboard() {
  loadData();
}

async function loadData() {
  loading.value = true;
  error.value = null;
  try {
    const res = await call("mathipe_ui.api.get_operational_dashboard", {});
    const raw = res?.message ?? res ?? {};
    data.value = {
      kpis: raw.kpis ?? {},
      urgent: raw.urgent ?? [],
      critical_alerts: raw.critical_alerts ?? [],
      waiting_approval_oldest: raw.waiting_approval_oldest ?? [],
      outsourcing_overdue: raw.outsourcing_overdue ?? [],
    };
  } catch (e) {
    error.value = e.message || "Error al cargar el dashboard.";
    data.value = { kpis: {}, urgent: [], critical_alerts: [], waiting_approval_oldest: [], outsourcing_overdue: [] };
  } finally {
    loading.value = false;
  }
}

onMounted(async () => {
  getSession().then((u) => { sessionUser.value = u; });
  call("mathipe_ui.api.get_system_users", {}).then((r) => {
    const list = r?.message ?? r ?? [];
    systemUsers.value = Array.isArray(list) ? list : [];
  });
  loadData();
});
</script>

<style scoped>
.toast-enter-active,
.toast-leave-active { transition: opacity 0.2s ease; }
.toast-enter-from,
.toast-leave-to { opacity: 0; }
</style>

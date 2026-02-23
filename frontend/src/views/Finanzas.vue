<template>
  <div class="min-h-full bg-gray-50 p-6">
    <!-- Cabecera -->
    <div class="mb-6 flex flex-wrap items-center justify-between gap-4">
      <div>
        <h1 class="text-2xl font-bold text-gray-900">Dashboard Financiero</h1>
        <p class="mt-1 text-sm text-gray-500">Ventas del período · margen bruto real por Orden de Trabajo</p>
      </div>

      <!-- Filtros de fecha -->
      <div class="flex flex-wrap items-center gap-2">
        <div class="flex items-center gap-1">
          <label class="text-xs font-medium text-gray-600" title="Filtra por Sales Order → Fecha de venta">Venta desde</label>
          <input
            v-model="dateFrom"
            type="date"
            class="rounded-lg border border-gray-300 px-3 py-1.5 text-sm focus:border-indigo-500 focus:outline-none focus:ring-1 focus:ring-indigo-500"
          />
        </div>
        <div class="flex items-center gap-1">
          <label class="text-xs font-medium text-gray-600" title="Filtra por Sales Order → Fecha de venta">Hasta</label>
          <input
            v-model="dateTo"
            type="date"
            class="rounded-lg border border-gray-300 px-3 py-1.5 text-sm focus:border-indigo-500 focus:outline-none focus:ring-1 focus:ring-indigo-500"
          />
        </div>
        <!-- Toggle: incluir OTs sin SO -->
        <label class="flex cursor-pointer items-center gap-2 rounded-lg border border-gray-200 bg-white px-3 py-1.5 text-xs text-gray-600 hover:bg-gray-50 select-none">
          <span
            class="relative inline-flex h-4 w-7 shrink-0 rounded-full transition-colors"
            :class="includeWithoutSO ? 'bg-indigo-500' : 'bg-gray-300'"
          >
            <span
              class="inline-block h-3 w-3 translate-y-0.5 rounded-full bg-white shadow transition-transform"
              :class="includeWithoutSO ? 'translate-x-3.5' : 'translate-x-0.5'"
            />
          </span>
          <input v-model="includeWithoutSO" type="checkbox" class="sr-only" />
          Incluir OT sin SO
        </label>
        <button
          class="flex items-center gap-1.5 rounded-lg bg-indigo-600 px-4 py-1.5 text-sm font-medium text-white hover:bg-indigo-700 disabled:opacity-50"
          :disabled="loading"
          @click="loadData"
        >
          <Loader2 v-if="loading" class="h-4 w-4 animate-spin" />
          <Search v-else class="h-4 w-4" />
          Consultar
        </button>
        <button
          class="rounded-lg border border-gray-300 px-4 py-1.5 text-sm text-gray-600 hover:bg-gray-50"
          @click="clearFilters"
        >
          Limpiar
        </button>
      </div>
    </div>

    <!-- Estado de carga -->
    <div v-if="loading" class="flex items-center justify-center py-20">
      <Loader2 class="h-8 w-8 animate-spin text-indigo-500" />
    </div>

    <!-- Error -->
    <div v-else-if="error" class="rounded-xl border border-red-200 bg-red-50 p-6 text-center text-sm text-red-600">
      {{ error }}
    </div>

    <template v-else-if="data">
      <!-- KPI Cards -->
      <div class="mb-6 grid grid-cols-2 gap-4 sm:grid-cols-4">
        <div class="rounded-xl border border-gray-200 bg-white p-5 shadow-sm">
          <div class="flex items-center gap-2 text-xs font-medium uppercase tracking-wider text-gray-500">
            <DollarSign class="h-4 w-4 text-indigo-400" />
            Ventas del período
          </div>
          <p class="mt-2 text-xl font-bold text-gray-900">{{ formatCurrency(data.total_revenue) }}</p>
          <p class="mt-1 text-xs text-gray-400">{{ data.total_work_orders }} órdenes · por fecha de venta</p>
        </div>

        <div class="rounded-xl border border-gray-200 bg-white p-5 shadow-sm">
          <div class="flex items-center gap-2 text-xs font-medium uppercase tracking-wider text-gray-500">
            <ShoppingCart class="h-4 w-4 text-orange-400" />
            Costo Real
          </div>
          <p class="mt-2 text-xl font-bold text-gray-900">{{ formatCurrency(data.total_real_cost) }}</p>
        </div>

        <div class="rounded-xl border border-gray-200 bg-white p-5 shadow-sm">
          <div class="flex items-center gap-2 text-xs font-medium uppercase tracking-wider text-gray-500">
            <TrendingUp class="h-4 w-4 text-emerald-400" />
            Margen Total
          </div>
          <p class="mt-2 text-xl font-bold" :class="data.total_margin >= 0 ? 'text-emerald-700' : 'text-red-600'">
            {{ formatCurrency(data.total_margin) }}
          </p>
        </div>

        <div class="rounded-xl border border-gray-200 bg-white p-5 shadow-sm">
          <div class="flex items-center gap-2 text-xs font-medium uppercase tracking-wider text-gray-500">
            <Percent class="h-4 w-4 text-blue-400" />
            Margen Promedio
          </div>
          <div class="mt-2">
            <span
              class="inline-flex items-center rounded-lg border px-3 py-1 text-lg font-bold"
              :class="marginBadgeClass(data.avg_margin_pct)"
            >
              {{ (data.avg_margin_pct || 0).toFixed(1) }}%
            </span>
          </div>
        </div>
      </div>

      <!-- Nota de fallback -->
      <div
        v-if="data.fallback_count > 0"
        class="mb-4 flex items-start gap-2 rounded-lg border border-amber-200 bg-amber-50 px-4 py-3 text-xs text-amber-700"
      >
        <Info class="mt-0.5 h-3.5 w-3.5 shrink-0" />
        <span>
          Incluye <strong>{{ data.fallback_count }}</strong>
          {{ data.fallback_count === 1 ? 'trabajo sin orden de venta' : 'trabajos sin orden de venta' }};
          se usó fecha de creación de la OT como referencia.
        </span>
      </div>

      <!-- Tablas top / bottom -->
      <div class="grid grid-cols-1 gap-6 lg:grid-cols-2">
        <!-- Top 5 más rentables -->
        <div class="rounded-xl border border-gray-200 bg-white shadow-sm">
          <div class="flex items-center gap-2 border-b border-gray-100 px-5 py-4">
            <ArrowUpCircle class="h-5 w-5 text-emerald-500" />
            <h2 class="text-sm font-semibold text-gray-900">Top 5 más rentables</h2>
          </div>
          <div v-if="data.top_profitable.length === 0" class="py-10 text-center text-sm text-gray-400">
            Sin datos
          </div>
          <table v-else class="w-full text-sm">
            <thead>
              <tr class="border-b border-gray-100 text-xs font-medium uppercase tracking-wider text-gray-400">
                <th class="px-5 py-2 text-left">OT</th>
                <th class="px-3 py-2 text-left">Cliente</th>
                <th class="px-3 py-2 text-left">Fecha venta</th>
                <th class="px-3 py-2 text-right">Venta</th>
                <th class="px-3 py-2 text-right">Costo</th>
                <th class="px-3 py-2 text-right">Margen%</th>
              </tr>
            </thead>
            <tbody class="divide-y divide-gray-50">
              <tr
                v-for="row in data.top_profitable"
                :key="row.work_order"
                class="hover:bg-gray-50 cursor-pointer"
                @click="$router.push(`/operaciones/ordenes`)"
              >
                <td class="px-5 py-2.5 font-mono text-xs text-indigo-600">{{ row.work_order }}</td>
                <td class="px-3 py-2.5 text-gray-700 truncate max-w-[100px]" :title="row.customer_name">{{ row.customer_name || '—' }}</td>
                <td class="px-3 py-2.5 text-xs text-gray-500">{{ row.sale_date || '—' }}</td>
                <td class="px-3 py-2.5 text-right text-gray-900">{{ formatCurrency(row.revenue_total) }}</td>
                <td class="px-3 py-2.5 text-right text-gray-600">{{ formatCurrency(row.real_cost_total) }}</td>
                <td class="px-3 py-2.5 text-right">
                  <span class="inline-flex rounded-full px-2 py-0.5 text-xs font-semibold" :class="marginBadgeClass(row.gross_margin_pct)">
                    {{ (row.gross_margin_pct || 0).toFixed(1) }}%
                  </span>
                </td>
              </tr>
            </tbody>
          </table>
        </div>

        <!-- Top 5 menos rentables -->
        <div class="rounded-xl border border-gray-200 bg-white shadow-sm">
          <div class="flex items-center gap-2 border-b border-gray-100 px-5 py-4">
            <ArrowDownCircle class="h-5 w-5 text-red-500" />
            <h2 class="text-sm font-semibold text-gray-900">Top 5 menos rentables</h2>
          </div>
          <div v-if="data.bottom_profitable.length === 0" class="py-10 text-center text-sm text-gray-400">
            Sin datos
          </div>
          <table v-else class="w-full text-sm">
            <thead>
              <tr class="border-b border-gray-100 text-xs font-medium uppercase tracking-wider text-gray-400">
                <th class="px-5 py-2 text-left">OT</th>
                <th class="px-3 py-2 text-left">Cliente</th>
                <th class="px-3 py-2 text-left">Fecha venta</th>
                <th class="px-3 py-2 text-right">Venta</th>
                <th class="px-3 py-2 text-right">Costo</th>
                <th class="px-3 py-2 text-right">Margen%</th>
              </tr>
            </thead>
            <tbody class="divide-y divide-gray-50">
              <tr
                v-for="row in data.bottom_profitable"
                :key="row.work_order"
                class="hover:bg-gray-50 cursor-pointer"
                @click="$router.push(`/operaciones/ordenes`)"
              >
                <td class="px-5 py-2.5 font-mono text-xs text-indigo-600">{{ row.work_order }}</td>
                <td class="px-3 py-2.5 text-gray-700 truncate max-w-[100px]" :title="row.customer_name">{{ row.customer_name || '—' }}</td>
                <td class="px-3 py-2.5 text-xs text-gray-500">{{ row.sale_date || '—' }}</td>
                <td class="px-3 py-2.5 text-right text-gray-900">{{ formatCurrency(row.revenue_total) }}</td>
                <td class="px-3 py-2.5 text-right text-gray-600">{{ formatCurrency(row.real_cost_total) }}</td>
                <td class="px-3 py-2.5 text-right">
                  <span class="inline-flex rounded-full px-2 py-0.5 text-xs font-semibold" :class="marginBadgeClass(row.gross_margin_pct)">
                    {{ (row.gross_margin_pct || 0).toFixed(1) }}%
                  </span>
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>
    </template>

    <!-- Estado vacío inicial -->
    <div v-else class="flex flex-col items-center justify-center py-20 text-center text-gray-400">
      <BarChart2 class="mb-3 h-12 w-12 opacity-30" />
      <p class="text-sm">Selecciona un rango de fechas o consultá sin filtro para ver el resumen financiero</p>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from "vue";
import {
  Loader2, Search, DollarSign, ShoppingCart, TrendingUp, Percent,
  ArrowUpCircle, ArrowDownCircle, BarChart2, Info,
} from "lucide-vue-next";
import { call } from "@/api/frappe";

const loading = ref(false);
const error = ref(null);
const data = ref(null);
const dateFrom = ref("");
const dateTo = ref("");
const includeWithoutSO = ref(false);

function formatCurrency(value) {
  if (value == null || value === "") return "—";
  return new Intl.NumberFormat("es-AR", {
    style: "currency",
    currency: "ARS",
    minimumFractionDigits: 0,
    maximumFractionDigits: 0,
  }).format(value);
}

function marginBadgeClass(pct) {
  if (pct > 30) return "bg-emerald-50 text-emerald-700 border border-emerald-200";
  if (pct >= 15) return "bg-amber-50 text-amber-700 border border-amber-200";
  return "bg-red-50 text-red-700 border border-red-200";
}

async function loadData() {
  loading.value = true;
  error.value = null;
  try {
    const args = { include_without_sales_order: includeWithoutSO.value ? 1 : 0 };
    if (dateFrom.value) args.date_from = dateFrom.value;
    if (dateTo.value) args.date_to = dateTo.value;
    const res = await call("mathipe_ui.api.get_financial_dashboard", args);
    data.value = res?.message ?? res;
  } catch (e) {
    error.value = e.message || "Error al cargar datos financieros";
  } finally {
    loading.value = false;
  }
}

function clearFilters() {
  dateFrom.value = "";
  dateTo.value = "";
  includeWithoutSO.value = false;
  loadData();
}

onMounted(() => {
  loadData();
});
</script>

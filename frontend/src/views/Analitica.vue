<template>
  <div class="min-h-full bg-gray-50 p-6">
    <!-- Cabecera + filtros -->
    <div class="mb-6 flex flex-wrap items-start justify-between gap-4">
      <div>
        <h1 class="text-2xl font-bold text-gray-900">Analítica de Rentabilidad</h1>
        <p class="mt-1 text-sm text-gray-500">Desglose por cliente, tipo de producto y proveedor</p>
      </div>

      <div class="flex flex-wrap items-center gap-2">
        <!-- Fecha desde -->
        <div class="flex items-center gap-1">
          <label class="text-xs font-medium text-gray-600" title="Filtra por Sales Order → Fecha de venta">Venta desde</label>
          <input
            v-model="dateFrom"
            type="date"
            class="rounded-lg border border-gray-300 px-3 py-1.5 text-sm focus:border-indigo-500 focus:outline-none focus:ring-1 focus:ring-indigo-500"
          />
        </div>
        <!-- Fecha hasta -->
        <div class="flex items-center gap-1">
          <label class="text-xs font-medium text-gray-600">Hasta</label>
          <input
            v-model="dateTo"
            type="date"
            class="rounded-lg border border-gray-300 px-3 py-1.5 text-sm focus:border-indigo-500 focus:outline-none focus:ring-1 focus:ring-indigo-500"
          />
        </div>
        <!-- Mínimo venta (solo relevante para bottom de clientes) -->
        <div class="flex items-center gap-1" title="Revenue mínimo para lista de bajo margen en Clientes">
          <label class="text-xs font-medium text-gray-600">Mín. venta</label>
          <input
            v-model.number="minRevenue"
            type="number"
            min="0"
            step="1000"
            class="w-28 rounded-lg border border-gray-300 px-2 py-1.5 text-sm focus:border-indigo-500 focus:outline-none focus:ring-1 focus:ring-indigo-500"
          />
        </div>
        <!-- Toggle sin SO -->
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
      <!-- Sin datos para el período -->
      <div
        v-if="isEmptyBreakdown"
        class="mb-4 rounded-xl border border-amber-200 bg-amber-50/60 px-5 py-8 text-center text-sm text-amber-800"
      >
        Sin datos para el período seleccionado. Probá otro rango de fechas o activá «Incluir OT sin SO».
      </div>
      <!-- Tabs -->
      <div class="mb-5 flex gap-1 rounded-xl bg-gray-200/60 p-1">
        <button
          v-for="tab in tabs"
          :key="tab.id"
          class="flex flex-1 items-center justify-center gap-1.5 rounded-lg px-4 py-2 text-sm font-medium transition-all"
          :class="activeTab === tab.id
            ? 'bg-white text-indigo-600 shadow-sm'
            : 'text-gray-500 hover:text-gray-700'"
          @click="activeTab = tab.id"
        >
          <component :is="tab.icon" class="h-4 w-4" />
          {{ tab.label }}
        </button>
      </div>

      <!-- ── TAB: CLIENTES ─────────────────────────────────────────────────── -->
      <div v-if="activeTab === 'clientes'">
        <!-- KPI rápido -->
        <div class="mb-4 flex flex-wrap gap-3">
          <div class="rounded-lg border border-gray-200 bg-white px-4 py-2.5 text-sm shadow-sm">
            <span class="text-gray-500">Clientes con ventas:</span>
            <span class="ml-2 font-bold text-gray-900">{{ data.by_customer.total_customers }}</span>
          </div>
          <div class="rounded-lg border border-gray-200 bg-white px-4 py-2.5 text-sm shadow-sm">
            <span class="text-gray-500">Umbral bajo margen:</span>
            <span class="ml-2 font-bold text-gray-900">{{ formatCurrency(data.by_customer.min_revenue_threshold) }}</span>
          </div>
        </div>

        <!-- Tablas top -->
        <div class="mb-6 grid grid-cols-1 gap-5 lg:grid-cols-2">
          <!-- Top por volumen -->
          <div class="rounded-xl border border-gray-200 bg-white shadow-sm">
            <div class="flex items-center gap-2 border-b border-gray-100 px-5 py-3.5">
              <TrendingUp class="h-4 w-4 text-indigo-500" />
              <h3 class="text-sm font-semibold text-gray-900">Top 10 por Volumen de Venta</h3>
            </div>
            <CustomerTable :rows="data.by_customer.top_by_revenue" sort-key="revenue_total" />
          </div>
          <!-- Top por margen -->
          <div class="rounded-xl border border-gray-200 bg-white shadow-sm">
            <div class="flex items-center gap-2 border-b border-gray-100 px-5 py-3.5">
              <DollarSign class="h-4 w-4 text-emerald-500" />
              <h3 class="text-sm font-semibold text-gray-900">Top 10 por Margen Bruto $</h3>
            </div>
            <CustomerTable :rows="data.by_customer.top_by_margin" sort-key="gross_margin" />
          </div>
        </div>

        <!-- Alertas: bajo margen -->
        <div class="rounded-xl border border-amber-200 bg-white shadow-sm">
          <div class="flex items-center gap-2 border-b border-amber-100 bg-amber-50/60 px-5 py-3.5">
            <AlertTriangle class="h-4 w-4 text-amber-500" />
            <h3 class="text-sm font-semibold text-gray-900">Clientes con Bajo Margen %</h3>
            <span class="ml-auto text-xs text-gray-400">
              Solo clientes con venta ≥ {{ formatCurrency(data.by_customer.min_revenue_threshold) }}
            </span>
          </div>
          <div v-if="data.by_customer.bottom_by_margin_pct.length === 0" class="py-8 text-center text-sm text-gray-400">
            Sin clientes que cumplan el umbral mínimo
          </div>
          <CustomerTable v-else :rows="data.by_customer.bottom_by_margin_pct" sort-key="gross_margin_pct" :ascending="true" />
        </div>
      </div>

      <!-- ── TAB: TIPOS DE PRODUCTO ────────────────────────────────────────── -->
      <div v-else-if="activeTab === 'tipos'">
        <div v-if="data.by_product_type.length === 0" class="py-16 text-center text-sm text-gray-400">
          Sin datos de tipos de producto para el período
        </div>
        <div v-else class="rounded-xl border border-gray-200 bg-white shadow-sm">
          <div class="flex items-center gap-2 border-b border-gray-100 px-5 py-3.5">
            <Layers class="h-4 w-4 text-slate-500" />
            <h3 class="text-sm font-semibold text-gray-900">Rentabilidad por Tipo de Producto</h3>
          </div>
          <!-- Barras de proporción de revenue -->
          <div class="border-b border-gray-100 px-5 py-4">
            <p class="mb-2 text-xs font-medium uppercase tracking-wider text-gray-400">Distribución de ventas</p>
            <div class="flex h-5 overflow-hidden rounded-full bg-gray-100">
              <div
                v-for="(t, i) in data.by_product_type"
                :key="t.product_type"
                class="h-full transition-all"
                :style="{ width: revenueShare(t.revenue_total) + '%', backgroundColor: typeColors[i % typeColors.length] }"
                :title="`${t.product_type}: ${revenueShare(t.revenue_total).toFixed(1)}%`"
              />
            </div>
            <div class="mt-2 flex flex-wrap gap-3">
              <div v-for="(t, i) in data.by_product_type" :key="t.product_type" class="flex items-center gap-1.5 text-xs text-gray-600">
                <span class="h-2.5 w-2.5 rounded-full" :style="{ backgroundColor: typeColors[i % typeColors.length] }" />
                {{ t.product_type }} ({{ revenueShare(t.revenue_total).toFixed(1) }}%)
              </div>
            </div>
          </div>
          <table class="w-full text-sm">
            <thead>
              <tr class="border-b border-gray-100 text-xs font-medium uppercase tracking-wider text-gray-400">
                <th class="px-5 py-2 text-left">Tipo</th>
                <th class="px-3 py-2 text-right">Ítems</th>
                <th class="px-3 py-2 text-right">Venta</th>
                <th class="px-3 py-2 text-right">Costo Est.</th>
                <th class="px-3 py-2 text-right">Costo Real</th>
                <th class="px-3 py-2 text-right">Margen $</th>
                <th class="px-3 py-2 text-right">Margen %</th>
              </tr>
            </thead>
            <tbody class="divide-y divide-gray-50">
              <tr v-for="t in data.by_product_type" :key="t.product_type" class="hover:bg-gray-50">
                <td class="px-5 py-2.5 font-medium text-gray-800">{{ t.product_type }}</td>
                <td class="px-3 py-2.5 text-right text-gray-500">{{ t.count_items }}</td>
                <td class="px-3 py-2.5 text-right font-semibold text-gray-900">{{ formatCurrency(t.revenue_total) }}</td>
                <td class="px-3 py-2.5 text-right text-gray-500">{{ formatCurrency(t.estimated_cost_total) }}</td>
                <td class="px-3 py-2.5 text-right text-gray-600">{{ formatCurrency(t.real_cost_total) }}</td>
                <td class="px-3 py-2.5 text-right" :class="t.gross_margin >= 0 ? 'text-emerald-700' : 'text-red-600'">
                  {{ formatCurrency(t.gross_margin) }}
                </td>
                <td class="px-3 py-2.5 text-right">
                  <span class="inline-flex rounded-full px-2 py-0.5 text-xs font-semibold" :class="marginClass(t.gross_margin_pct)">
                    {{ (t.gross_margin_pct || 0).toFixed(1) }}%
                  </span>
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>

      <!-- ── TAB: PROVEEDORES ──────────────────────────────────────────────── -->
      <div v-else-if="activeTab === 'proveedores'">
        <div v-if="data.by_supplier.length === 0" class="py-16 text-center text-sm text-gray-400">
          Sin ítems tercerizados en el período seleccionado
        </div>
        <div v-else class="rounded-xl border border-gray-200 bg-white shadow-sm">
          <div class="flex items-center gap-2 border-b border-gray-100 px-5 py-3.5">
            <Truck class="h-4 w-4 text-slate-500" />
            <h3 class="text-sm font-semibold text-gray-900">Rentabilidad por Proveedor Tercerizado</h3>
          </div>
          <table class="w-full text-sm">
            <thead>
              <tr class="border-b border-gray-100 text-xs font-medium uppercase tracking-wider text-gray-400">
                <th class="px-5 py-2 text-left">Proveedor</th>
                <th class="px-3 py-2 text-right">Ítems</th>
                <th class="px-3 py-2 text-center">Recibidos</th>
                <th class="px-3 py-2 text-right">Venta OS</th>
                <th class="px-3 py-2 text-right">Costo Real</th>
                <th class="px-3 py-2 text-right">Margen $</th>
                <th class="px-3 py-2 text-right">Margen %</th>
              </tr>
            </thead>
            <tbody class="divide-y divide-gray-50">
              <tr v-for="s in data.by_supplier" :key="s.supplier" class="hover:bg-gray-50">
                <td class="px-5 py-2.5 font-medium text-gray-800">{{ s.supplier }}</td>
                <td class="px-3 py-2.5 text-right text-gray-500">{{ s.count_items }}</td>
                <td class="px-3 py-2.5 text-center">
                  <span
                    class="inline-flex items-center gap-1 rounded-full px-2 py-0.5 text-xs font-medium"
                    :class="s.received_rate === 100 ? 'bg-emerald-50 text-emerald-700'
                           : s.received_rate > 50  ? 'bg-amber-50 text-amber-700'
                           : 'bg-red-50 text-red-700'"
                  >
                    {{ s.received_count }}/{{ s.count_items }}
                    ({{ (s.received_rate ?? 0).toFixed(0) }}%)
                  </span>
                </td>
                <td class="px-3 py-2.5 text-right font-semibold text-gray-900">{{ formatCurrency(s.outsourced_revenue) }}</td>
                <td class="px-3 py-2.5 text-right text-gray-600">{{ formatCurrency(s.real_cost_total) }}</td>
                <td class="px-3 py-2.5 text-right" :class="s.gross_margin >= 0 ? 'text-emerald-700' : 'text-red-600'">
                  {{ formatCurrency(s.gross_margin) }}
                </td>
                <td class="px-3 py-2.5 text-right">
                  <span class="inline-flex rounded-full px-2 py-0.5 text-xs font-semibold" :class="marginClass(s.gross_margin_pct)">
                    {{ (s.gross_margin_pct || 0).toFixed(1) }}%
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
      <PieChart class="mb-3 h-12 w-12 opacity-30" />
      <p class="text-sm">Consultá sin filtro o aplicá un rango de fechas para ver la analítica</p>
    </div>
  </div>
</template>

<!-- ── Sub-componente: tabla de clientes (reutilizada en 3 lugares) ──────── -->
<script>
const CustomerTable = {
  props: {
    rows: { type: Array, default: () => [] },
    sortKey: { type: String, default: "revenue_total" },
    ascending: { type: Boolean, default: false },
  },
  setup(props) {
    function formatCurrency(value) {
      if (value == null || value === "") return "—";
      return new Intl.NumberFormat("es-AR", {
        style: "currency", currency: "ARS",
        minimumFractionDigits: 0, maximumFractionDigits: 0,
      }).format(value);
    }
    function marginClass(pct) {
      if (pct > 30) return "bg-emerald-50 text-emerald-700 border border-emerald-200";
      if (pct >= 15) return "bg-amber-50 text-amber-700 border border-amber-200";
      return "bg-red-50 text-red-700 border border-red-200";
    }
    return { formatCurrency, marginClass };
  },
  template: `
    <div v-if="rows.length === 0" class="py-8 text-center text-sm text-gray-400">Sin datos</div>
    <table v-else class="w-full text-sm">
      <thead>
        <tr class="border-b border-gray-100 text-xs font-medium uppercase tracking-wider text-gray-400">
          <th class="px-5 py-2 text-left">Cliente</th>
          <th class="px-3 py-2 text-right">OTs</th>
          <th class="px-3 py-2 text-right">Venta</th>
          <th class="px-3 py-2 text-right">Margen $</th>
          <th class="px-3 py-2 text-right">Margen %</th>
        </tr>
      </thead>
      <tbody class="divide-y divide-gray-50">
        <tr v-for="c in rows" :key="c.customer" class="hover:bg-gray-50">
          <td class="max-w-[160px] truncate px-5 py-2.5 font-medium text-gray-800" :title="c.customer_name">
            {{ c.customer_name || '—' }}
          </td>
          <td class="px-3 py-2.5 text-right text-gray-500">{{ c.wo_count }}</td>
          <td class="px-3 py-2.5 text-right font-semibold text-gray-900">{{ formatCurrency(c.revenue_total) }}</td>
          <td class="px-3 py-2.5 text-right" :class="c.gross_margin >= 0 ? 'text-emerald-700' : 'text-red-600'">
            {{ formatCurrency(c.gross_margin) }}
          </td>
          <td class="px-3 py-2.5 text-right">
            <span class="inline-flex rounded-full px-2 py-0.5 text-xs font-semibold" :class="marginClass(c.gross_margin_pct)">
              {{ (c.gross_margin_pct || 0).toFixed(1) }}%
            </span>
          </td>
        </tr>
      </tbody>
    </table>
  `,
};
</script>

<script setup>
import { ref, computed, onMounted } from "vue";
import {
  Loader2, Search, TrendingUp, DollarSign, Layers, Truck,
  AlertTriangle, PieChart,
} from "lucide-vue-next";
import { call } from "@/api/frappe";

// ── Estado ────────────────────────────────────────────────────────────────────
const loading = ref(false);
const error = ref(null);
const data = ref(null);
const dateFrom = ref("");
const dateTo = ref("");
const minRevenue = ref(5000);
const includeWithoutSO = ref(false);
const activeTab = ref("clientes");

const tabs = [
  { id: "clientes",    label: "Clientes",           icon: TrendingUp },
  { id: "tipos",       label: "Tipos de Producto",  icon: Layers },
  { id: "proveedores", label: "Proveedores",         icon: Truck },
];

const typeColors = ["#6366f1", "#10b981", "#f59e0b", "#ef4444", "#8b5cf6", "#06b6d4"];

// ── Helpers ───────────────────────────────────────────────────────────────────
function formatCurrency(value) {
  if (value == null || value === "") return "—";
  return new Intl.NumberFormat("es-AR", {
    style: "currency", currency: "ARS",
    minimumFractionDigits: 0, maximumFractionDigits: 0,
  }).format(value);
}

function marginClass(pct) {
  if (pct > 30) return "bg-emerald-50 text-emerald-700 border border-emerald-200";
  if (pct >= 15) return "bg-amber-50 text-amber-700 border border-amber-200";
  return "bg-red-50 text-red-700 border border-red-200";
}

const totalTypeRevenue = computed(() =>
  (data.value?.by_product_type || []).reduce((s, t) => s + t.revenue_total, 0)
);

const isEmptyBreakdown = computed(() => {
  if (!data.value) return false;
  const byC = data.value.by_customer || {};
  const totalCustomers = byC.total_customers ?? 0;
  const types = (data.value.by_product_type || []).length;
  const suppliers = (data.value.by_supplier || []).length;
  return totalCustomers === 0 && types === 0 && suppliers === 0;
});

function revenueShare(revenue) {
  const total = totalTypeRevenue.value;
  return total > 0 ? (revenue / total) * 100 : 0;
}

// ── Carga de datos ────────────────────────────────────────────────────────────
async function loadData() {
  loading.value = true;
  error.value = null;
  try {
    const args = {
      include_without_sales_order: includeWithoutSO.value ? 1 : 0,
      min_revenue: minRevenue.value ?? 5000,
    };
    if (dateFrom.value) args.date_from = dateFrom.value;
    if (dateTo.value) args.date_to = dateTo.value;
    const res = await call("mathipe_ui.api.get_profitability_breakdown", args);
    data.value = res?.message ?? res;
  } catch (e) {
    error.value = e.message || "Error al cargar la analítica";
  } finally {
    loading.value = false;
  }
}

function clearFilters() {
  dateFrom.value = "";
  dateTo.value = "";
  minRevenue.value = 5000;
  includeWithoutSO.value = false;
  loadData();
}

onMounted(() => {
  loadData();
});
</script>

<template>
  <div class="min-h-full bg-gray-50 p-6">
    <div class="mb-6 flex flex-wrap items-center justify-between gap-4">
      <div>
        <h1 class="text-2xl font-bold text-gray-900">Alertas</h1>
        <p class="mt-1 text-sm text-gray-500">Órdenes de trabajo con alertas por margen, aprobación, tercerización o entrega</p>
      </div>
      <div class="flex flex-wrap items-center gap-2">
        <label class="text-xs font-medium text-gray-600">Entrega desde</label>
        <input
          v-model="dateFrom"
          type="date"
          class="rounded-lg border border-gray-300 px-3 py-1.5 text-sm focus:border-indigo-500 focus:outline-none focus:ring-1 focus:ring-indigo-500"
        />
        <label class="text-xs font-medium text-gray-600">Hasta</label>
        <input
          v-model="dateTo"
          type="date"
          class="rounded-lg border border-gray-300 px-3 py-1.5 text-sm focus:border-indigo-500 focus:outline-none focus:ring-1 focus:ring-indigo-500"
        />
        <label class="flex cursor-pointer items-center gap-2 rounded-lg border border-gray-200 bg-white px-3 py-1.5 text-xs text-gray-600 hover:bg-gray-50 select-none">
          <input v-model="onlyOpen" type="checkbox" class="rounded border-gray-300 text-indigo-600 focus:ring-indigo-500" />
          Solo abiertas
        </label>
        <select
          v-model="level"
          class="rounded-lg border border-gray-300 px-3 py-1.5 text-sm focus:border-indigo-500 focus:outline-none focus:ring-1 focus:ring-indigo-500"
        >
          <option value="">Todos los niveles</option>
          <option value="danger">Peligro</option>
          <option value="warning">Advertencia</option>
          <option value="info">Info</option>
        </select>
        <button
          class="flex items-center gap-1.5 rounded-lg bg-indigo-600 px-4 py-1.5 text-sm font-medium text-white hover:bg-indigo-700 disabled:opacity-50"
          :disabled="loading"
          @click="loadData"
        >
          <Loader2 v-if="loading" class="h-4 w-4 animate-spin" />
          <Search v-else class="h-4 w-4" />
          Consultar
        </button>
      </div>
    </div>

    <div v-if="loading" class="flex items-center justify-center py-20">
      <Loader2 class="h-8 w-8 animate-spin text-indigo-500" />
    </div>
    <div v-else-if="error" class="rounded-xl border border-red-200 bg-red-50 p-6 text-center text-sm text-red-600">
      {{ error }}
    </div>
    <div v-else class="overflow-hidden rounded-xl border border-gray-200 bg-white shadow-sm">
      <table class="min-w-full divide-y divide-gray-200">
        <thead class="bg-gray-50">
          <tr>
            <th scope="col" class="px-4 py-3 text-left text-xs font-medium uppercase tracking-wider text-gray-500">OT</th>
            <th scope="col" class="px-4 py-3 text-left text-xs font-medium uppercase tracking-wider text-gray-500">Cliente</th>
            <th scope="col" class="px-4 py-3 text-left text-xs font-medium uppercase tracking-wider text-gray-500">Entrega</th>
            <th scope="col" class="px-4 py-3 text-left text-xs font-medium uppercase tracking-wider text-gray-500">Estado</th>
            <th scope="col" class="px-4 py-3 text-right text-xs font-medium uppercase tracking-wider text-gray-500">Margen %</th>
            <th scope="col" class="px-4 py-3 text-center text-xs font-medium uppercase tracking-wider text-gray-500">Alertas</th>
            <th scope="col" class="px-4 py-3 text-left text-xs font-medium uppercase tracking-wider text-gray-500">Top alerta</th>
          </tr>
        </thead>
        <tbody class="divide-y divide-gray-200 bg-white">
          <tr
            v-for="row in rows"
            :key="row.work_order_id"
            class="cursor-pointer hover:bg-indigo-50/50 transition-colors"
            @click="goToOrder(row.sales_order)"
          >
            <td class="whitespace-nowrap px-4 py-3 text-sm font-mono text-gray-900">{{ row.work_order_id }}</td>
            <td class="whitespace-nowrap px-4 py-3 text-sm text-gray-700">{{ row.customer_name || "—" }}</td>
            <td class="whitespace-nowrap px-4 py-3 text-sm text-gray-600">{{ row.delivery_date || "—" }}</td>
            <td class="whitespace-nowrap px-4 py-3">
              <span
                class="inline-flex rounded px-2 py-0.5 text-xs font-medium"
                :class="statusBadgeClass(row.status)"
              >
                {{ row.status || "—" }}
              </span>
            </td>
            <td class="whitespace-nowrap px-4 py-3 text-right text-sm font-medium" :class="marginClass(row.margin_pct)">
              {{ (row.margin_pct ?? 0).toFixed(1) }}%
            </td>
            <td class="whitespace-nowrap px-4 py-3 text-center">
              <span v-if="(row.alerts_summary?.danger || 0) > 0" class="rounded-full bg-red-100 px-2 py-0.5 text-xs font-medium text-red-800">{{ row.alerts_summary.danger }}</span>
              <span v-if="(row.alerts_summary?.warning || 0) > 0" class="ml-0.5 rounded-full bg-amber-100 px-2 py-0.5 text-xs font-medium text-amber-800">{{ row.alerts_summary.warning }}</span>
              <span v-if="(row.alerts_summary?.info || 0) > 0" class="ml-0.5 rounded-full bg-blue-100 px-2 py-0.5 text-xs font-medium text-blue-800">{{ row.alerts_summary.info }}</span>
              <span v-if="!totalAlerts(row)" class="text-xs text-gray-400">—</span>
            </td>
            <td class="px-4 py-3 text-sm text-gray-600">{{ row.top_alert_title || "—" }}</td>
          </tr>
          <tr v-if="rows.length === 0">
            <td colspan="7" class="px-4 py-12 text-center text-sm text-gray-500">No hay órdenes con alertas en el período.</td>
          </tr>
        </tbody>
      </table>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from "vue";
import { useRouter } from "vue-router";
import { Loader2, Search } from "lucide-vue-next";
import { call } from "@/api/frappe";

const router = useRouter();
const loading = ref(false);
const error = ref(null);
const rows = ref([]);
const dateFrom = ref("");
const dateTo = ref("");
const onlyOpen = ref(true);
const level = ref("");

function totalAlerts(row) {
  const s = row.alerts_summary || {};
  return (s.danger || 0) + (s.warning || 0) + (s.info || 0);
}

function statusBadgeClass(status) {
  if (!status) return "bg-gray-100 text-gray-600";
  const s = (status || "").toLowerCase();
  if (s === "done" || s === "delivered") return "bg-emerald-100 text-emerald-800";
  if (s === "production") return "bg-blue-100 text-blue-800";
  if (s === "waitingapproval") return "bg-amber-100 text-amber-800";
  if (s === "approved") return "bg-green-100 text-green-800";
  return "bg-gray-100 text-gray-600";
}

function marginClass(pct) {
  if (pct >= 25) return "text-emerald-600";
  if (pct >= 15) return "text-amber-600";
  return "text-red-600";
}

function goToOrder(salesOrderId) {
  if (salesOrderId) router.push({ path: "/orden/" + salesOrderId });
}

async function loadData() {
  loading.value = true;
  error.value = null;
  try {
    const res = await call("mathipe_ui.api.get_alerts_board", {
      date_from: dateFrom.value || undefined,
      date_to: dateTo.value || undefined,
      only_open: onlyOpen.value ? 1 : 0,
      level: level.value || undefined,
    });
    rows.value = res?.message ?? res ?? [];
  } catch (e) {
    error.value = e.message || "Error al cargar alertas.";
    rows.value = [];
  } finally {
    loading.value = false;
  }
}

onMounted(() => {
  loadData();
});
</script>

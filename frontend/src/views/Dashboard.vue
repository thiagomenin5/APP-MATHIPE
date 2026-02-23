<template>
  <div class="min-h-full bg-slate-50">
    <h1 class="mb-6 text-xl font-semibold text-gray-900">Panel de Control</h1>

    <div v-if="loading" class="flex flex-col items-center justify-center gap-4 py-12">
      <Loader2 class="h-10 w-10 animate-spin text-indigo-600" />
      <p class="text-sm text-gray-500">Cargando datos...</p>
    </div>

    <template v-else>
      <!-- Sección 1: KPIs -->
      <div class="mb-8 grid grid-cols-1 gap-4 sm:grid-cols-3">
        <div
          class="flex items-center gap-4 rounded-xl border border-gray-200 bg-white p-5 shadow-sm"
        >
          <div class="flex h-12 w-12 shrink-0 items-center justify-center rounded-lg bg-emerald-100 text-emerald-600">
            <DollarSign class="h-6 w-6" />
          </div>
          <div>
            <p class="text-sm font-medium text-gray-500">Ventas del Mes</p>
            <p class="text-2xl font-semibold text-gray-900">{{ formatCurrency(data.sales_total) }}</p>
          </div>
        </div>

        <button
          type="button"
          class="flex cursor-pointer items-center gap-4 rounded-xl border border-gray-200 bg-white p-5 text-left shadow-sm transition hover:shadow-md focus:outline-none focus:ring-2 focus:ring-orange-400 focus:ring-offset-2"
          @click="router.push('/operaciones/tablero')"
        >
          <div class="flex h-12 w-12 shrink-0 items-center justify-center rounded-lg bg-orange-100 text-orange-600">
            <Clock class="h-6 w-6" />
          </div>
          <div>
            <p class="text-sm font-medium text-gray-500">En Cola</p>
            <p class="text-2xl font-semibold text-gray-900">{{ data.orders_pending ?? "—" }}</p>
          </div>
        </button>

        <div
          class="flex items-center gap-4 rounded-xl border border-gray-200 bg-white p-5 shadow-sm"
        >
          <div class="flex h-12 w-12 shrink-0 items-center justify-center rounded-lg bg-blue-100 text-blue-600">
            <Activity class="h-6 w-6" />
          </div>
          <div>
            <p class="text-sm font-medium text-gray-500">En Producción</p>
            <p class="text-2xl font-semibold text-gray-900">{{ data.orders_in_production ?? "—" }}</p>
          </div>
        </div>
      </div>

      <!-- Sección 2: Accesos Rápidos -->
      <div class="mb-8">
        <h2 class="mb-3 text-sm font-medium uppercase tracking-wider text-gray-500">Accesos Rápidos</h2>
        <div class="flex flex-wrap gap-3">
          <button
            type="button"
            class="inline-flex items-center gap-2 rounded-lg bg-indigo-600 px-5 py-3 text-sm font-medium text-white shadow-sm hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:ring-offset-2"
            @click="router.push('/comercial/consultas')"
          >
            <FileText class="h-5 w-5" />
            Nueva Cotización
          </button>
          <button
            type="button"
            class="inline-flex items-center gap-2 rounded-lg border border-gray-300 bg-white px-5 py-3 text-sm font-medium text-gray-700 shadow-sm hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:ring-offset-2"
            @click="router.push('/operaciones/tablero')"
          >
            <LayoutGrid class="h-5 w-5" />
            Ver Tablero
          </button>
          <button
            type="button"
            class="inline-flex items-center gap-2 rounded-lg border border-gray-300 bg-white px-5 py-3 text-sm font-medium text-gray-700 shadow-sm hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:ring-offset-2"
            @click="router.push('/operaciones/inventario')"
          >
            <Package class="h-5 w-5" />
            Inventario
          </button>
        </div>
      </div>

      <!-- Sección 3: Actividad Reciente -->
      <div class="rounded-xl border border-gray-200 bg-white shadow-sm">
        <div class="flex items-center justify-between border-b border-gray-200 px-5 py-4">
          <h2 class="text-base font-semibold text-gray-900">Actividad Reciente</h2>
          <button
            type="button"
            class="text-sm font-medium text-indigo-600 hover:text-indigo-700"
            @click="router.push('/operaciones/ordenes')"
          >
            Ver Todas
          </button>
        </div>
        <div class="overflow-x-auto">
          <table class="min-w-full divide-y divide-gray-200">
            <thead class="bg-gray-50">
              <tr>
                <th scope="col" class="px-5 py-3 text-left text-xs font-medium uppercase tracking-wider text-gray-500">ID</th>
                <th scope="col" class="px-5 py-3 text-left text-xs font-medium uppercase tracking-wider text-gray-500">Cliente</th>
                <th scope="col" class="px-5 py-3 text-left text-xs font-medium uppercase tracking-wider text-gray-500">Estado</th>
                <th scope="col" class="px-5 py-3 text-right text-xs font-medium uppercase tracking-wider text-gray-500">Total</th>
              </tr>
            </thead>
            <tbody class="divide-y divide-gray-200 bg-white">
              <tr
                v-for="order in data.recent_orders"
                :key="order.name"
                class="cursor-pointer transition-colors hover:bg-gray-50"
                @click="goToOrder(order.name)"
              >
                <td class="whitespace-nowrap px-5 py-3 text-sm font-medium text-gray-900">{{ order.name }}</td>
                <td class="whitespace-nowrap px-5 py-3 text-sm text-gray-700">{{ order.customer_name || "—" }}</td>
                <td class="whitespace-nowrap px-5 py-3">
                  <span
                    class="inline-flex rounded-full px-2.5 py-0.5 text-xs font-medium"
                    :class="badgeClass(order.status)"
                  >
                    {{ statusLabel(order.status) }}
                  </span>
                </td>
                <td class="whitespace-nowrap px-5 py-3 text-right text-sm font-medium text-gray-900">
                  {{ formatCurrency(order.grand_total) }}
                </td>
              </tr>
              <tr v-if="data.recent_orders && data.recent_orders.length === 0">
                <td colspan="4" class="px-5 py-8 text-center text-sm text-gray-500">No hay órdenes recientes.</td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>
    </template>
  </div>
</template>

<script setup>
import { ref, onMounted } from "vue";
import { useRouter } from "vue-router";
import { Loader2, DollarSign, Clock, Activity, FileText, LayoutGrid, Package } from "lucide-vue-next";
import { call } from "@/api/frappe";

const router = useRouter();
const loading = ref(true);
const data = ref({
  sales_total: 0,
  orders_pending: 0,
  orders_in_production: 0,
  recent_orders: [],
});

onMounted(async () => {
  try {
    const res = await call("mathipe_ui.api.get_dashboard_data", {});
    data.value = res?.message ?? res ?? data.value;
  } catch (e) {
    console.error("Dashboard data:", e);
  } finally {
    loading.value = false;
  }
});

function formatCurrency(value) {
  if (value == null || value === "") return "—";
  return new Intl.NumberFormat("es-AR", {
    style: "currency",
    currency: "ARS",
    minimumFractionDigits: 0,
    maximumFractionDigits: 0,
  }).format(value);
}

function goToOrder(name) {
  if (name) router.push("/orden/" + name);
}

function statusLabel(status) {
  const map = {
    Draft: "Borrador",
    Submitted: "Enviado",
    "To Bill": "A facturar",
    "To Deliver": "A entregar",
    "Partially Delivered": "Parc. entregado",
    Delivered: "Entregado",
    Completed: "Completado",
    Cancelled: "Cancelado",
  };
  return map[status] || status || "—";
}

function badgeClass(status) {
  const s = (status || "").trim();
  if (["Cancelled"].includes(s)) return "bg-red-100 text-red-800";
  if (["Delivered", "Completed"].includes(s)) return "bg-emerald-100 text-emerald-800";
  if (["Draft"].includes(s)) return "bg-gray-100 text-gray-700";
  if (["To Deliver", "Partially Delivered", "To Bill", "Submitted"].includes(s)) return "bg-amber-100 text-amber-800";
  return "bg-gray-100 text-gray-700";
}
</script>

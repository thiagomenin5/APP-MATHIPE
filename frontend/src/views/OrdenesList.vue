<template>
  <div class="max-w-6xl">
    <!-- Header -->
    <div class="mb-6 flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
      <h1 class="text-xl font-semibold text-gray-900">Órdenes de Trabajo</h1>
      <button
        type="button"
        class="inline-flex items-center justify-center gap-2 rounded-lg bg-indigo-600 px-4 py-2.5 text-sm font-medium text-white shadow-sm hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:ring-offset-2"
        @click="router.push('/comercial/consultas')"
      >
        <Plus class="h-5 w-5" />
        Nueva Orden
      </button>
    </div>

    <!-- Filtros -->
    <div class="mb-4 flex flex-col gap-3 sm:flex-row sm:items-center sm:gap-4">
      <div class="relative flex-1">
        <Search class="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-gray-400" />
        <input
          v-model="searchTerm"
          type="text"
          placeholder="Buscar por ID o cliente..."
          class="w-full rounded-lg border border-gray-300 py-2.5 pl-10 pr-4 text-sm placeholder-gray-500 focus:border-indigo-500 focus:outline-none focus:ring-2 focus:ring-indigo-500"
          @input="onSearchInput"
        />
      </div>
      <select
        v-model="statusFilter"
        class="rounded-lg border border-gray-300 py-2.5 pl-4 pr-10 text-sm focus:border-indigo-500 focus:outline-none focus:ring-2 focus:ring-indigo-500"
        @change="fetchOrders"
      >
        <option value="">Todos</option>
        <option value="Pendientes">Pendientes</option>
        <option value="Completados">Completados</option>
      </select>
    </div>

    <!-- Tabla -->
    <div class="overflow-hidden rounded-lg border border-gray-200 bg-white shadow-sm">
      <div v-if="loading" class="flex items-center justify-center gap-2 px-5 py-12 text-sm text-gray-500">
        <Loader2 class="h-5 w-5 animate-spin" />
        Cargando...
      </div>

      <template v-else>
        <table class="min-w-full divide-y divide-gray-200">
          <thead class="bg-gray-50">
            <tr>
              <th scope="col" class="px-5 py-3 text-left text-xs font-medium uppercase tracking-wider text-gray-500">ID</th>
              <th scope="col" class="px-5 py-3 text-left text-xs font-medium uppercase tracking-wider text-gray-500">Fecha</th>
              <th scope="col" class="px-5 py-3 text-left text-xs font-medium uppercase tracking-wider text-gray-500">Cliente</th>
              <th scope="col" class="px-5 py-3 text-left text-xs font-medium uppercase tracking-wider text-gray-500">Detalle</th>
              <th scope="col" class="px-5 py-3 text-left text-xs font-medium uppercase tracking-wider text-gray-500">Estado</th>
              <th scope="col" class="px-5 py-3 text-right text-xs font-medium uppercase tracking-wider text-gray-500">Total</th>
              <th scope="col" class="relative w-12 px-2 py-3"><span class="sr-only">Ver</span></th>
            </tr>
          </thead>
          <tbody class="divide-y divide-gray-200 bg-white">
            <tr
              v-for="row in orders"
              :key="row.name"
              class="cursor-pointer transition-colors hover:bg-gray-50"
              @click="goToOrder(row.name)"
            >
              <td class="whitespace-nowrap px-5 py-3 text-sm font-medium text-gray-900">{{ row.name }}</td>
              <td class="whitespace-nowrap px-5 py-3 text-sm text-gray-600">{{ row.transaction_date || "—" }}</td>
              <td class="whitespace-nowrap px-5 py-3 text-sm text-gray-900">{{ row.customer_name || "—" }}</td>
              <td class="max-w-[200px] truncate px-5 py-3 text-sm text-gray-600" :title="row.items_preview">
                {{ row.items_preview || "—" }}
              </td>
              <td class="whitespace-nowrap px-5 py-3">
                <span :class="badgeClass(row.status)" class="inline-flex rounded-full px-2.5 py-0.5 text-xs font-medium">
                  {{ statusLabel(row.status) }}
                </span>
              </td>
              <td class="whitespace-nowrap px-5 py-3 text-right text-sm font-medium text-gray-900">
                {{ formatCurrency(row.grand_total) }}
              </td>
              <td class="whitespace-nowrap px-2 py-3">
                <button
                  type="button"
                  class="rounded p-1.5 text-gray-400 hover:bg-gray-100 hover:text-indigo-600"
                  aria-label="Ver orden"
                  @click.stop="goToOrder(row.name)"
                >
                  <ChevronRight class="h-5 w-5" />
                </button>
              </td>
            </tr>
            <tr v-if="!loading && orders.length === 0">
              <td colspan="7" class="px-5 py-10 text-center text-sm text-gray-500">
                No se encontraron órdenes.
              </td>
            </tr>
          </tbody>
        </table>
      </template>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from "vue";
import { useRouter } from "vue-router";
import { Plus, Search, Loader2, ChevronRight } from "lucide-vue-next";
import { call } from "@/api/frappe";

const router = useRouter();
const loading = ref(true);
const orders = ref([]);
const searchTerm = ref("");
const statusFilter = ref("");
let searchDebounce = null;

function onSearchInput() {
  clearTimeout(searchDebounce);
  searchDebounce = setTimeout(fetchOrders, 300);
}

async function fetchOrders() {
  loading.value = true;
  try {
    const res = await call("mathipe_ui.api.get_sales_orders_list", {
      status: statusFilter.value || undefined,
      search_term: searchTerm.value.trim() || undefined,
    });
    const data = res?.message ?? res;
    orders.value = Array.isArray(data) ? data : [];
  } catch (e) {
    console.error("OrdenesList: error al cargar", e);
    orders.value = [];
  } finally {
    loading.value = false;
  }
}

function goToOrder(id) {
  if (id) router.push("/orden/" + id);
}

function formatCurrency(value) {
  if (value == null || value === "") return "—";
  return new Intl.NumberFormat("es-AR", {
    style: "currency",
    currency: "ARS",
    minimumFractionDigits: 0,
    maximumFractionDigits: 2,
  }).format(value);
}

function statusLabel(status) {
  const s = (status || "").trim();
  const map = {
    Draft: "Borrador",
    Submitted: "Enviado",
    "To Bill": "A facturar",
    "To Deliver": "A entregar",
    "Partially Delivered": "Parc. entregado",
    Delivered: "Entregado",
    Completed: "Completado",
    Cancelled: "Cancelado",
    Closed: "Cerrado",
  };
  return map[s] || s || "—";
}

function badgeClass(status) {
  const s = (status || "").trim();
  if (["Cancelled", "Closed"].includes(s)) return "bg-red-100 text-red-800";
  if (["Delivered", "Completed"].includes(s)) return "bg-green-100 text-green-800";
  if (["Draft"].includes(s)) return "bg-gray-100 text-gray-800";
  if (["To Deliver", "Partially Delivered", "To Bill", "Submitted"].includes(s)) return "bg-amber-100 text-amber-800";
  return "bg-gray-100 text-gray-700";
}

onMounted(() => {
  fetchOrders();
});
</script>

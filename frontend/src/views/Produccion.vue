<template>
  <div>
    <div class="mb-6 flex flex-wrap items-center justify-between gap-4">
      <h1 class="text-xl font-semibold text-gray-900">Tablero de Producción</h1>
      <router-link
        to="/operaciones/tercerizacion"
        class="inline-flex items-center gap-1.5 rounded border border-indigo-200 bg-indigo-50 px-3 py-1.5 text-sm font-medium text-indigo-700 hover:bg-indigo-100"
      >
        Ver tercerización
      </router-link>
    </div>

    <div v-if="loading" class="flex flex-col items-center justify-center gap-4 py-12">
      <Loader2 class="h-10 w-10 animate-spin text-indigo-600" />
      <p class="text-sm text-gray-500">Cargando tablero...</p>
    </div>

    <div v-else class="grid grid-cols-1 gap-6 bg-gray-100 p-4 rounded-xl lg:grid-cols-3">
      <!-- Columna 1: Pendientes (status: Approved) -->
      <div class="flex flex-col rounded-xl border border-red-200 bg-white shadow-sm">
        <div class="rounded-t-xl border-b border-red-200 bg-red-50 px-4 py-3">
          <h2 class="text-base font-bold uppercase tracking-wide text-red-800">Pendientes</h2>
          <p class="mt-0.5 text-xs text-red-700">Cola de impresión · {{ board.approved.length }} órdenes</p>
        </div>
        <div class="flex-1 space-y-3 overflow-y-auto p-3 min-h-[200px]">
          <div
            v-for="card in board.approved"
            :key="card.name"
            class="rounded-lg border border-gray-200 bg-white p-4 shadow-sm transition hover:shadow-md relative"
          >
            <span
              v-if="(card.alerts_summary?.danger || 0) > 0"
              class="absolute top-2 right-2 rounded-full bg-red-500 h-2.5 w-2.5"
              title="Hay alertas"
            />
            <span
              v-else-if="(card.alerts_summary?.warning || 0) > 0"
              class="absolute top-2 right-2 rounded-full bg-amber-500 h-2.5 w-2.5"
              title="Hay alertas"
            />
            <p class="text-[10px] font-mono text-gray-400 mb-0.5">{{ card.name }}</p>
            <p class="font-semibold text-gray-900">{{ card.customer_name || "—" }}</p>
            <div class="mt-2 flex items-center justify-between gap-2">
              <span
                class="inline-flex rounded px-2 py-0.5 text-xs font-medium"
                :class="isUrgentDelivery(card.delivery_date) ? 'bg-red-100 text-red-800' : 'bg-gray-100 text-gray-600'"
              >
                {{ card.delivery_date || "—" }}
              </span>
              <div class="flex flex-wrap gap-1">
                <span v-for="tag in (card.tags || [])" :key="tag" class="rounded-full bg-purple-100 px-2 py-0.5 text-[10px] font-medium text-purple-700">{{ tag }}</span>
              </div>
            </div>
            <div class="mt-3 flex gap-2">
              <button
                type="button"
                class="inline-flex items-center gap-1 rounded bg-amber-500 px-2.5 py-1.5 text-xs font-medium text-white hover:bg-amber-600"
                :disabled="actioning === card.name"
                @click.stop="setStatus(card.name, 'Production')"
              >
                <Play class="h-3.5 w-3.5" />
                Iniciar
              </button>
              <button
                type="button"
                class="rounded border border-gray-300 px-2.5 py-1.5 text-xs font-medium text-gray-700 hover:bg-gray-50"
                @click.stop="goToOrder(card.sales_order)"
              >
                Ver orden
              </button>
            </div>
          </div>
          <p v-if="board.approved.length === 0" class="py-8 text-center text-sm text-gray-500">Sin órdenes pendientes</p>
        </div>
      </div>

      <!-- Columna 2: En Máquina (status: Production) -->
      <div class="flex flex-col rounded-xl border border-amber-200 bg-white shadow-sm">
        <div class="rounded-t-xl border-b border-amber-200 bg-amber-50 px-4 py-3">
          <h2 class="text-base font-bold uppercase tracking-wide text-amber-800">En Máquina</h2>
          <p class="mt-0.5 text-xs text-amber-700">Producción · {{ board.production.length }} órdenes</p>
        </div>
        <div class="flex-1 space-y-3 overflow-y-auto p-3 min-h-[200px]">
          <div
            v-for="card in board.production"
            :key="card.name"
            class="rounded-lg border border-gray-200 bg-white p-4 shadow-sm transition hover:shadow-md relative"
          >
            <span v-if="(card.alerts_summary?.danger || 0) > 0" class="absolute top-2 right-2 rounded-full bg-red-500 h-2.5 w-2.5" title="Hay alertas" />
            <span v-else-if="(card.alerts_summary?.warning || 0) > 0" class="absolute top-2 right-2 rounded-full bg-amber-500 h-2.5 w-2.5" title="Hay alertas" />
            <p class="text-[10px] font-mono text-gray-400 mb-0.5">{{ card.name }}</p>
            <p class="font-semibold text-gray-900">{{ card.customer_name || "—" }}</p>
            <div class="mt-2 flex items-center justify-between gap-2">
              <span
                class="inline-flex rounded px-2 py-0.5 text-xs font-medium"
                :class="isUrgentDelivery(card.delivery_date) ? 'bg-red-100 text-red-800' : 'bg-gray-100 text-gray-600'"
              >
                {{ card.delivery_date || "—" }}
              </span>
              <div class="flex flex-wrap gap-1">
                <span v-for="tag in (card.tags || [])" :key="tag" class="rounded-full bg-purple-100 px-2 py-0.5 text-[10px] font-medium text-purple-700">{{ tag }}</span>
              </div>
            </div>
            <div class="mt-3 flex gap-2">
              <button
                type="button"
                class="inline-flex items-center gap-1 rounded bg-green-600 px-2.5 py-1.5 text-xs font-medium text-white hover:bg-green-700"
                :disabled="actioning === card.name"
                @click.stop="setStatus(card.name, 'Done')"
              >
                <Check class="h-3.5 w-3.5" />
                Terminar
              </button>
              <button
                type="button"
                class="rounded border border-gray-300 px-2.5 py-1.5 text-xs font-medium text-gray-700 hover:bg-gray-50"
                @click.stop="goToOrder(card.sales_order)"
              >
                Ver orden
              </button>
            </div>
          </div>
          <p v-if="board.production.length === 0" class="py-8 text-center text-sm text-gray-500">Ninguna en máquina</p>
        </div>
      </div>

      <!-- Columna 3: Finalizado (status: Done) -->
      <div class="flex flex-col rounded-xl border border-green-200 bg-white shadow-sm">
        <div class="rounded-t-xl border-b border-green-200 bg-green-50 px-4 py-3">
          <h2 class="text-base font-bold uppercase tracking-wide text-green-800">Finalizado</h2>
          <p class="mt-0.5 text-xs text-green-700">Para entrega · {{ board.done.length }} órdenes</p>
        </div>
        <div class="flex-1 space-y-3 overflow-y-auto p-3 min-h-[200px]">
          <div
            v-for="card in board.done"
            :key="card.name"
            class="rounded-lg border border-gray-200 bg-white p-4 shadow-sm transition hover:shadow-md cursor-pointer relative"
            @click="goToOrder(card.sales_order)"
          >
            <span v-if="(card.alerts_summary?.danger || 0) > 0" class="absolute top-2 right-2 rounded-full bg-red-500 h-2.5 w-2.5" title="Hay alertas" />
            <span v-else-if="(card.alerts_summary?.warning || 0) > 0" class="absolute top-2 right-2 rounded-full bg-amber-500 h-2.5 w-2.5" title="Hay alertas" />
            <p class="text-[10px] font-mono text-gray-400 mb-0.5">{{ card.name }}</p>
            <p class="font-semibold text-gray-900">{{ card.customer_name || "—" }}</p>
            <div class="mt-2 flex items-center justify-between gap-2">
              <span class="inline-flex rounded px-2 py-0.5 text-xs font-medium bg-gray-100 text-gray-600">
                {{ card.delivery_date || "—" }}
              </span>
              <div class="flex flex-wrap gap-1">
                <span v-for="tag in (card.tags || [])" :key="tag" class="rounded-full bg-purple-100 px-2 py-0.5 text-[10px] font-medium text-purple-700">{{ tag }}</span>
              </div>
            </div>
            <div class="mt-3 flex gap-2">
              <button
                type="button"
                class="rounded border border-gray-300 px-2.5 py-1.5 text-xs font-medium text-gray-700 hover:bg-gray-50"
                @click.stop="goToOrder(card.sales_order)"
              >
                Ver orden
              </button>
              <button
                type="button"
                class="rounded border border-teal-300 px-2.5 py-1.5 text-xs font-medium text-teal-700 hover:bg-teal-50"
                :disabled="actioning === card.name"
                @click.stop="setStatus(card.name, 'Delivered')"
              >
                Marcar Entregado
              </button>
            </div>
          </div>
          <p v-if="board.done.length === 0" class="py-8 text-center text-sm text-gray-500">Ninguna finalizada</p>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted } from "vue";
import { useRouter } from "vue-router";
import { Loader2, Play, Check } from "lucide-vue-next";
import { call } from "@/api/frappe";

const router = useRouter();
const loading = ref(true);
const actioning = ref(null);
const board = ref({
  new: [],
  design: [],
  waiting_approval: [],
  approved: [],
  production: [],
  done: [],
});

const REFRESH_INTERVAL_MS = 30 * 1000;
let refreshTimer = null;

function isUrgentDelivery(deliveryDate) {
  if (!deliveryDate) return false;
  const d = new Date(deliveryDate);
  const today = new Date();
  today.setHours(0, 0, 0, 0);
  d.setHours(0, 0, 0, 0);
  return Math.ceil((d - today) / (24 * 60 * 60 * 1000)) <= 1;
}

function goToOrder(salesOrder) {
  if (salesOrder) router.push("/orden/" + salesOrder);
}

async function fetchBoard() {
  try {
    const res = await call("mathipe_ui.api.get_wo_board", {});
    const data = res?.message ?? res ?? {};
    board.value = {
      new: Array.isArray(data.new) ? data.new : [],
      design: Array.isArray(data.design) ? data.design : [],
      waiting_approval: Array.isArray(data.waiting_approval) ? data.waiting_approval : [],
      approved: Array.isArray(data.approved) ? data.approved : [],
      production: Array.isArray(data.production) ? data.production : [],
      done: Array.isArray(data.done) ? data.done : [],
    };
  } catch (e) {
    console.error("Tablero producción:", e);
  } finally {
    loading.value = false;
  }
}

async function setStatus(woName, status) {
  if (actioning.value) return;
  actioning.value = woName;
  try {
    await call("mathipe_ui.api.update_wo_status", { work_order_id: woName, status });
    await fetchBoard();
  } catch (e) {
    console.error("update_wo_status:", e);
  } finally {
    actioning.value = null;
  }
}

onMounted(() => {
  fetchBoard();
  refreshTimer = setInterval(fetchBoard, REFRESH_INTERVAL_MS);
});

onUnmounted(() => {
  if (refreshTimer) clearInterval(refreshTimer);
});
</script>

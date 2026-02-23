<template>
  <div>
    <div class="mb-6 flex flex-wrap items-center justify-between gap-4">
      <h1 class="text-xl font-semibold text-gray-900">Tablero de Tercerización</h1>
      <div class="flex flex-wrap items-center gap-2">
        <input
          v-model="filterSupplier"
          type="text"
          placeholder="Filtrar por proveedor"
          class="rounded border border-gray-300 px-3 py-1.5 text-sm focus:border-indigo-500 focus:ring-1 focus:ring-indigo-500"
          @keyup.enter="fetchBoard"
        />
        <button
          type="button"
          class="rounded bg-indigo-600 px-3 py-1.5 text-sm font-medium text-white hover:bg-indigo-700"
          @click="fetchBoard"
        >
          Actualizar
        </button>
      </div>
    </div>

    <div v-if="loading" class="flex flex-col items-center justify-center gap-4 py-12">
      <Loader2 class="h-10 w-10 animate-spin text-indigo-600" />
      <p class="text-sm text-gray-500">Cargando tablero...</p>
    </div>

    <div v-else class="grid grid-cols-1 gap-6 bg-gray-100 p-4 rounded-xl lg:grid-cols-3">
      <!-- Pendiente Proveedor -->
      <div class="flex flex-col rounded-xl border border-amber-200 bg-white shadow-sm">
        <div class="rounded-t-xl border-b border-amber-200 bg-amber-50 px-4 py-3">
          <h2 class="text-base font-bold uppercase tracking-wide text-amber-800">Pendiente proveedor</h2>
          <p class="mt-0.5 text-xs text-amber-700">{{ board.pending_vendor.length }} ítems</p>
        </div>
        <div class="flex-1 space-y-3 overflow-y-auto p-3 min-h-[200px]">
          <div
            v-for="card in board.pending_vendor"
            :key="card.work_order_id + '-' + card.item_row_id"
            class="rounded-lg border border-gray-200 bg-white p-4 shadow-sm transition hover:shadow-md relative"
          >
            <span v-if="(card.alerts_summary?.danger || 0) > 0" class="absolute top-2 right-2 rounded-full bg-red-500 h-2.5 w-2.5" title="Hay alertas" />
            <span v-else-if="(card.alerts_summary?.warning || 0) > 0" class="absolute top-2 right-2 rounded-full bg-amber-500 h-2.5 w-2.5" title="Hay alertas" />
            <div class="cursor-pointer" @click="goToOrder(card.sales_order)">
              <p class="text-[10px] font-mono text-gray-400 mb-0.5">{{ card.work_order_id }}</p>
              <p class="font-semibold text-gray-900">{{ card.customer || card.customer_name || "—" }}</p>
              <p class="mt-1 text-xs text-gray-600">{{ card.item_desc || card.item_summary || "—" }}</p>
              <p class="mt-0.5 text-xs text-gray-500">Proveedor: {{ card.supplier || "—" }}</p>
              <p class="mt-0.5 text-[10px] text-gray-400">OT: {{ card.wo_status || card.status || "—" }}</p>
              <span class="mt-2 inline-flex rounded px-2 py-0.5 text-xs font-medium bg-gray-100 text-gray-600">
                {{ card.delivery_date || "—" }}
              </span>
            </div>
            <div class="mt-3 flex flex-wrap gap-1" @click.stop>
              <button
                type="button"
                :disabled="actioning === card.work_order_id + '-' + card.item_row_id"
                class="rounded bg-amber-500 px-2 py-1 text-xs font-medium text-white hover:bg-amber-600 disabled:opacity-50"
                @click="setStatus(card, 'sent')"
              >
                Marcar Enviado
              </button>
              <button
                type="button"
                :disabled="actioning === card.work_order_id + '-' + card.item_row_id"
                class="rounded bg-emerald-600 px-2 py-1 text-xs font-medium text-white hover:bg-emerald-700 disabled:opacity-50"
                @click="setStatus(card, 'received')"
              >
                Marcar Recibido
              </button>
            </div>
          </div>
          <p v-if="board.pending_vendor.length === 0" class="py-8 text-center text-sm text-gray-500">Sin ítems pendientes</p>
        </div>
      </div>

      <!-- Enviado -->
      <div class="flex flex-col rounded-xl border border-blue-200 bg-white shadow-sm">
        <div class="rounded-t-xl border-b border-blue-200 bg-blue-50 px-4 py-3">
          <h2 class="text-base font-bold uppercase tracking-wide text-blue-800">Enviado</h2>
          <p class="mt-0.5 text-xs text-blue-700">{{ board.sent.length }} ítems</p>
        </div>
        <div class="flex-1 space-y-3 overflow-y-auto p-3 min-h-[200px]">
          <div
            v-for="card in board.sent"
            :key="card.work_order_id + '-' + card.item_row_id"
            class="rounded-lg border border-gray-200 bg-white p-4 shadow-sm transition hover:shadow-md relative"
          >
            <span v-if="(card.alerts_summary?.danger || 0) > 0" class="absolute top-2 right-2 rounded-full bg-red-500 h-2.5 w-2.5" title="Hay alertas" />
            <span v-else-if="(card.alerts_summary?.warning || 0) > 0" class="absolute top-2 right-2 rounded-full bg-amber-500 h-2.5 w-2.5" title="Hay alertas" />
            <div class="cursor-pointer" @click="goToOrder(card.sales_order)">
              <p class="text-[10px] font-mono text-gray-400 mb-0.5">{{ card.work_order_id }}</p>
              <p class="font-semibold text-gray-900">{{ card.customer || card.customer_name || "—" }}</p>
              <p class="mt-1 text-xs text-gray-600">{{ card.item_desc || card.item_summary || "—" }}</p>
              <p class="mt-0.5 text-xs text-gray-500">Proveedor: {{ card.supplier || "—" }}</p>
              <p v-if="card.time_since" class="mt-1 text-[10px] text-gray-400">Enviado: {{ card.time_since }}</p>
              <span class="mt-2 inline-flex rounded px-2 py-0.5 text-xs font-medium bg-gray-100 text-gray-600">
                {{ card.delivery_date || "—" }}
              </span>
            </div>
            <div class="mt-3 flex flex-wrap gap-1" @click.stop>
              <button
                type="button"
                :disabled="actioning === card.work_order_id + '-' + card.item_row_id"
                class="rounded bg-emerald-600 px-2 py-1 text-xs font-medium text-white hover:bg-emerald-700 disabled:opacity-50"
                @click="setStatus(card, 'received')"
              >
                Marcar Recibido
              </button>
            </div>
          </div>
          <p v-if="board.sent.length === 0" class="py-8 text-center text-sm text-gray-500">Ninguno enviado</p>
        </div>
      </div>

      <!-- Recibido -->
      <div class="flex flex-col rounded-xl border border-emerald-200 bg-white shadow-sm">
        <div class="rounded-t-xl border-b border-emerald-200 bg-emerald-50 px-4 py-3">
          <h2 class="text-base font-bold uppercase tracking-wide text-emerald-800">Recibido</h2>
          <p class="mt-0.5 text-xs text-emerald-700">{{ board.received.length }} ítems</p>
        </div>
        <div class="flex-1 space-y-3 overflow-y-auto p-3 min-h-[200px]">
          <div
            v-for="card in board.received"
            :key="card.work_order_id + '-' + card.item_row_id"
            class="cursor-pointer rounded-lg border border-gray-200 bg-white p-4 shadow-sm transition hover:shadow-md relative"
            @click="goToOrder(card.sales_order)"
          >
            <span v-if="(card.alerts_summary?.danger || 0) > 0" class="absolute top-2 right-2 rounded-full bg-red-500 h-2.5 w-2.5" title="Hay alertas" />
            <span v-else-if="(card.alerts_summary?.warning || 0) > 0" class="absolute top-2 right-2 rounded-full bg-amber-500 h-2.5 w-2.5" title="Hay alertas" />
            <p class="text-[10px] font-mono text-gray-400 mb-0.5">{{ card.work_order_id }}</p>
            <p class="font-semibold text-gray-900">{{ card.customer || card.customer_name || "—" }}</p>
            <p class="mt-1 text-xs text-gray-600">{{ card.item_desc || card.item_summary || "—" }}</p>
            <p class="mt-0.5 text-xs text-gray-500">Proveedor: {{ card.supplier || "—" }}</p>
            <p v-if="card.time_since" class="mt-1 text-[10px] text-gray-400">Recibido: {{ card.time_since }}</p>
            <span class="mt-2 inline-flex rounded px-2 py-0.5 text-xs font-medium bg-gray-100 text-gray-600">
              {{ card.delivery_date || "—" }}
            </span>
          </div>
          <p v-if="board.received.length === 0" class="py-8 text-center text-sm text-gray-500">Ninguno recibido</p>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from "vue";
import { useRouter } from "vue-router";
import { Loader2 } from "lucide-vue-next";
import { call } from "@/api/frappe";

const router = useRouter();
const loading = ref(true);
const actioning = ref(null);
const filterSupplier = ref("");
const board = ref({
  pending_vendor: [],
  sent: [],
  received: [],
});

function goToOrder(salesOrder) {
  if (salesOrder) router.push("/orden/" + salesOrder);
}

async function setStatus(card, action) {
  const key = card.work_order_id + "-" + card.item_row_id;
  if (actioning.value) return;
  actioning.value = key;
  try {
    await call("mathipe_ui.api.update_outsource_status", {
      work_order_id: card.work_order_id,
      item_row_id: card.item_row_id,
      action,
    });
    await fetchBoard();
  } catch (e) {
    console.error("update_outsource_status:", e);
  } finally {
    actioning.value = null;
  }
}

async function fetchBoard() {
  loading.value = true;
  try {
    const filters = filterSupplier.value ? { supplier: filterSupplier.value.trim() } : {};
    const res = await call("mathipe_ui.api.get_outsource_board", { filters });
    const data = res?.message ?? res ?? {};
    board.value = {
      pending_vendor: Array.isArray(data.pending_vendor) ? data.pending_vendor : [],
      sent: Array.isArray(data.sent) ? data.sent : [],
      received: Array.isArray(data.received) ? data.received : [],
    };
  } catch (e) {
    console.error("Tablero tercerización:", e);
  } finally {
    loading.value = false;
  }
}

onMounted(() => {
  fetchBoard();
});
</script>

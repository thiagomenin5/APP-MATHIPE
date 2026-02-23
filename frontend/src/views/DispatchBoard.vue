<template>
  <div class="min-h-full bg-slate-50 p-6">
    <div class="mb-6 flex flex-wrap items-center justify-between gap-4">
      <h1 class="text-2xl font-bold text-gray-900">Tablero de Despacho</h1>
      <button
        type="button"
        class="inline-flex items-center gap-2 rounded-lg border border-gray-300 bg-white px-3 py-1.5 text-sm font-medium text-gray-700 shadow-sm hover:bg-gray-50"
        :disabled="loading"
        @click="fetchBoard"
      >
        <Loader2 v-if="loading" class="h-4 w-4 animate-spin" />
        Actualizar
      </button>
    </div>

    <div v-if="loading" class="flex flex-col items-center justify-center gap-4 py-12">
      <Loader2 class="h-10 w-10 animate-spin text-indigo-600" />
      <p class="text-sm text-gray-500">Cargando tablero...</p>
    </div>

    <div v-else-if="error" class="rounded-xl border border-red-200 bg-red-50 p-6 text-center text-sm text-red-600">
      {{ error }}
    </div>

    <div v-else class="grid grid-cols-1 gap-4 lg:grid-cols-4">
      <!-- A remito -->
      <div class="flex flex-col rounded-xl border border-amber-200 bg-white shadow-sm">
        <div class="rounded-t-xl border-b border-amber-200 bg-amber-50 px-4 py-3">
          <h2 class="text-sm font-bold uppercase tracking-wide text-amber-800">A remito</h2>
          <p class="mt-0.5 text-xs text-amber-700">{{ board.to_remito.length }} OT(s)</p>
        </div>
        <div class="flex-1 space-y-2 overflow-y-auto p-3 min-h-[180px]">
          <div
            v-for="card in board.to_remito"
            :key="card.work_order_id"
            class="cursor-pointer rounded-lg border border-gray-200 bg-white p-3 shadow-sm transition hover:shadow"
            @click="openQuickView(card)"
          >
            <p class="text-[10px] font-mono text-gray-400">{{ card.work_order_id }}</p>
            <p class="font-medium text-gray-900 truncate">{{ card.customer_name || "—" }}</p>
            <p class="mt-0.5 text-xs text-gray-600">{{ formatDate(card.delivery_date) }}</p>
            <p v-if="card.top_alert_title" class="mt-1 text-xs text-amber-700 truncate" :title="card.top_alert_title">{{ card.top_alert_title }}</p>
          </div>
          <p v-if="board.to_remito.length === 0" class="py-6 text-center text-sm text-gray-500">Ninguna</p>
        </div>
      </div>

      <!-- A entregar -->
      <div class="flex flex-col rounded-xl border border-blue-200 bg-white shadow-sm">
        <div class="rounded-t-xl border-b border-blue-200 bg-blue-50 px-4 py-3">
          <h2 class="text-sm font-bold uppercase tracking-wide text-blue-800">A entregar</h2>
          <p class="mt-0.5 text-xs text-blue-700">{{ board.to_deliver.length }} OT(s)</p>
        </div>
        <div class="flex-1 space-y-2 overflow-y-auto p-3 min-h-[180px]">
          <div
            v-for="card in board.to_deliver"
            :key="card.work_order_id"
            class="cursor-pointer rounded-lg border border-gray-200 bg-white p-3 shadow-sm transition hover:shadow"
            @click="openQuickView(card)"
          >
            <p class="text-[10px] font-mono text-gray-400">{{ card.work_order_id }}</p>
            <p class="font-medium text-gray-900 truncate">{{ card.customer_name || "—" }}</p>
            <p class="mt-0.5 text-xs text-gray-600">{{ formatDate(card.delivery_date) }}</p>
            <p v-if="card.top_alert_title" class="mt-1 text-xs text-amber-700 truncate">{{ card.top_alert_title }}</p>
          </div>
          <p v-if="board.to_deliver.length === 0" class="py-6 text-center text-sm text-gray-500">Ninguna</p>
        </div>
      </div>

      <!-- Entregado sin factura -->
      <div class="flex flex-col rounded-xl border border-red-200 bg-white shadow-sm">
        <div class="rounded-t-xl border-b border-red-200 bg-red-50 px-4 py-3">
          <h2 class="text-sm font-bold uppercase tracking-wide text-red-800">Entregado sin factura</h2>
          <p class="mt-0.5 text-xs text-red-700">{{ board.delivered_uninvoiced.length }} OT(s)</p>
        </div>
        <div class="flex-1 space-y-2 overflow-y-auto p-3 min-h-[180px]">
          <div
            v-for="card in board.delivered_uninvoiced"
            :key="card.work_order_id"
            class="rounded-lg border border-gray-200 bg-white p-3 shadow-sm transition hover:shadow"
          >
            <div class="cursor-pointer" @click="openQuickView(card)">
              <span v-if="(card.alerts_summary?.danger || 0) > 0" class="inline-block rounded-full bg-red-500 h-2 w-2 align-middle mr-1" title="Alerta" />
              <span v-else-if="(card.alerts_summary?.warning || 0) > 0" class="inline-block rounded-full bg-amber-500 h-2 w-2 align-middle mr-1" title="Alerta" />
              <p class="text-[10px] font-mono text-gray-400">{{ card.work_order_id }}</p>
              <p class="font-medium text-gray-900 truncate">{{ card.customer_name || "—" }}</p>
              <p class="mt-0.5 text-xs text-gray-600">{{ formatDate(card.delivery_date) }}</p>
              <p v-if="card.top_alert_title" class="mt-1 text-xs text-amber-700 truncate">{{ card.top_alert_title }}</p>
            </div>
            <div class="mt-2" @click.stop>
              <button type="button" class="w-full rounded bg-emerald-600 px-2 py-1 text-xs font-medium text-white hover:bg-emerald-700 disabled:opacity-50" :disabled="actioningId === card.work_order_id" @click="openMarkInvoicedModal(card)">
                Marcar Facturado
              </button>
            </div>
          </div>
          <p v-if="board.delivered_uninvoiced.length === 0" class="py-6 text-center text-sm text-gray-500">Ninguna</p>
        </div>
      </div>

      <!-- Completado -->
      <div class="flex flex-col rounded-xl border border-emerald-200 bg-white shadow-sm">
        <div class="rounded-t-xl border-b border-emerald-200 bg-emerald-50 px-4 py-3">
          <h2 class="text-sm font-bold uppercase tracking-wide text-emerald-800">Completado</h2>
          <p class="mt-0.5 text-xs text-emerald-700">{{ board.completed.length }} OT(s)</p>
        </div>
        <div class="flex-1 space-y-2 overflow-y-auto p-3 min-h-[180px]">
          <div
            v-for="card in board.completed"
            :key="card.work_order_id"
            class="cursor-pointer rounded-lg border border-gray-200 bg-white p-3 shadow-sm transition hover:shadow"
            @click="openQuickView(card)"
          >
            <p class="text-[10px] font-mono text-gray-400">{{ card.work_order_id }}</p>
            <p class="font-medium text-gray-900 truncate">{{ card.customer_name || "—" }}</p>
            <p class="mt-0.5 text-xs text-gray-600">{{ formatDate(card.delivery_date) }}</p>
          </div>
          <p v-if="board.completed.length === 0" class="py-6 text-center text-sm text-gray-500">Ninguna</p>
        </div>
      </div>
    </div>

    <QuickViewWorkOrder :work-order-id="quickViewId" :visible="quickViewVisible" @close="quickViewVisible = false" />

    <!-- Modal Marcar Facturado -->
    <div v-if="markInvoicedModal" class="fixed inset-0 z-50 flex items-center justify-center bg-black/50 p-4" @click.self="markInvoicedModal = null">
      <div class="w-full max-w-sm rounded-lg bg-white p-4 shadow-xl">
        <p class="font-medium text-gray-900">Marcar como facturado</p>
        <p class="mt-1 text-sm text-gray-600">{{ markInvoicedModal.work_order_id }} — {{ markInvoicedModal.customer_name || "—" }}</p>
        <div class="mt-4 flex justify-end gap-2">
          <button type="button" class="rounded border border-gray-300 px-3 py-1.5 text-sm font-medium text-gray-700 hover:bg-gray-50" @click="markInvoicedModal = null">Cancelar</button>
          <button type="button" class="rounded bg-emerald-600 px-3 py-1.5 text-sm font-medium text-white hover:bg-emerald-700 disabled:opacity-50" :disabled="actioningId" @click="confirmMarkInvoiced">
            Marcar facturado
          </button>
        </div>
      </div>
    </div>

    <Transition name="toast">
      <div v-if="toastVisible" class="fixed bottom-6 left-1/2 z-[60] -translate-x-1/2 rounded-lg px-4 py-2.5 text-sm font-medium text-white shadow-lg" :class="toastError ? 'bg-red-600' : 'bg-emerald-600'" role="alert">
        {{ toastMessage }}
      </div>
    </Transition>
  </div>
</template>

<script setup>
import { ref, onMounted } from "vue";
import { Loader2 } from "lucide-vue-next";
import { call } from "@/api/frappe";
import QuickViewWorkOrder from "@/components/QuickViewWorkOrder.vue";

const loading = ref(true);
const error = ref(null);
const actioningId = ref(null);
const toastVisible = ref(false);
const toastMessage = ref("");
const toastError = ref(false);
const markInvoicedModal = ref(null);

const board = ref({
  to_remito: [],
  to_deliver: [],
  delivered_uninvoiced: [],
  completed: [],
});

const quickViewId = ref(null);
const quickViewVisible = ref(false);

onMounted(() => fetchBoard());

function fetchBoard() {
  loading.value = true;
  error.value = null;
  call("mathipe_ui.api.get_dispatch_board", {})
    .then((res) => {
      const data = res?.message ?? res ?? {};
      board.value = {
        to_remito: data.to_remito || [],
        to_deliver: data.to_deliver || [],
        delivered_uninvoiced: data.delivered_uninvoiced || [],
        completed: data.completed || [],
      };
    })
    .catch((e) => {
      error.value = e.message || "Error al cargar el tablero.";
      board.value = { to_remito: [], to_deliver: [], delivered_uninvoiced: [], completed: [] };
    })
    .finally(() => { loading.value = false; });
}

function openQuickView(card) {
  const id = card?.work_order_id || card?.name;
  if (id) {
    quickViewId.value = id;
    quickViewVisible.value = true;
  }
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

function openMarkInvoicedModal(card) {
  markInvoicedModal.value = card;
}

function confirmMarkInvoiced() {
  if (!markInvoicedModal.value?.work_order_id) return;
  const wid = markInvoicedModal.value.work_order_id;
  actioningId.value = wid;
  call("mathipe_ui.api.mark_wo_invoiced", { work_order_id: wid })
    .then(() => {
      showToast("Marcado como facturado.");
      markInvoicedModal.value = null;
      fetchBoard();
    })
    .catch((e) => {
      showToast(e.message || "Error.", true);
    })
    .finally(() => { actioningId.value = null; });
}

function showToast(message, isError = false) {
  toastMessage.value = message;
  toastError.value = isError;
  toastVisible.value = true;
  setTimeout(() => { toastVisible.value = false; }, 3000);
}
</script>

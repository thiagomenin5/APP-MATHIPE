<template>
  <div class="min-h-full bg-slate-50 p-6">
    <div class="mb-6 flex flex-wrap items-center justify-between gap-4">
      <div>
        <h1 class="text-2xl font-bold text-gray-900">Tablero: {{ sectorName }}</h1>
        <p class="mt-0.5 text-sm text-gray-500">Ruta: /operaciones/sector/{{ sectorKey }}</p>
      </div>
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

    <div v-else class="grid grid-cols-1 gap-6 lg:grid-cols-3">
      <!-- Pendiente -->
      <div class="flex flex-col rounded-xl border border-amber-200 bg-white shadow-sm">
        <div class="rounded-t-xl border-b border-amber-200 bg-amber-50 px-4 py-3">
          <h2 class="text-base font-bold uppercase tracking-wide text-amber-800">Pendiente</h2>
          <p class="mt-0.5 text-xs text-amber-700">{{ board.pending.length }} OT(s)</p>
        </div>
        <div class="flex-1 space-y-3 overflow-y-auto p-3 min-h-[200px]">
          <div
            v-for="card in board.pending"
            :key="card.work_order_id"
            class="rounded-lg border border-gray-200 bg-white p-4 shadow-sm transition hover:shadow-md cursor-pointer relative"
            @click="openQuickView(card)"
          >
            <span v-if="(card.alerts_summary?.danger || 0) > 0" class="absolute top-2 right-2 rounded-full bg-red-500 h-2.5 w-2.5" title="Alertas" />
            <span v-else-if="(card.alerts_summary?.warning || 0) > 0" class="absolute top-2 right-2 rounded-full bg-amber-500 h-2.5 w-2.5" title="Alertas" />
            <p class="text-[10px] font-mono text-gray-400">{{ card.work_order_id }}</p>
            <p class="font-semibold text-gray-900">{{ card.customer_name || "—" }}</p>
            <p class="mt-0.5 text-xs text-gray-600">{{ formatDate(card.delivery_date) }}</p>
            <p v-if="card.top_alert_title" class="mt-1 text-xs text-amber-700 truncate" :title="card.top_alert_title">{{ card.top_alert_title }}</p>
            <p class="mt-1 text-xs" :class="marginClass(card.gross_margin_pct)">Margen {{ (card.gross_margin_pct ?? 0).toFixed(1) }}%</p>
            <div class="mt-3 flex flex-wrap gap-1" @click.stop>
              <button
                type="button"
                :disabled="actioningId === card.work_order_id"
                class="rounded bg-indigo-600 px-2 py-1 text-xs font-medium text-white hover:bg-indigo-700 disabled:opacity-50"
                @click="runAction(card, 'take')"
              >
                Tomar
              </button>
              <select
                class="rounded border border-gray-300 text-xs py-1 pr-6 bg-white"
                @change="onAssign(card, $event.target.value); $event.target.value = ''"
              >
                <option value="">Asignar</option>
                <option v-for="u in systemUsers" :key="u.name" :value="u.name">{{ u.full_name || u.name }}</option>
              </select>
            </div>
          </div>
          <p v-if="board.pending.length === 0" class="py-8 text-center text-sm text-gray-500">Sin pendientes</p>
        </div>
      </div>

      <!-- En proceso -->
      <div class="flex flex-col rounded-xl border border-blue-200 bg-white shadow-sm">
        <div class="rounded-t-xl border-b border-blue-200 bg-blue-50 px-4 py-3">
          <h2 class="text-base font-bold uppercase tracking-wide text-blue-800">En proceso</h2>
          <p class="mt-0.5 text-xs text-blue-700">{{ board.in_progress.length }} OT(s)</p>
        </div>
        <div class="flex-1 space-y-3 overflow-y-auto p-3 min-h-[200px]">
          <div
            v-for="card in board.in_progress"
            :key="card.work_order_id"
            class="rounded-lg border border-gray-200 bg-white p-4 shadow-sm transition hover:shadow-md cursor-pointer relative"
            @click="openQuickView(card)"
          >
            <span v-if="(card.alerts_summary?.danger || 0) > 0" class="absolute top-2 right-2 rounded-full bg-red-500 h-2.5 w-2.5" title="Alertas" />
            <span v-else-if="(card.alerts_summary?.warning || 0) > 0" class="absolute top-2 right-2 rounded-full bg-amber-500 h-2.5 w-2.5" title="Alertas" />
            <p class="text-[10px] font-mono text-gray-400">{{ card.work_order_id }}</p>
            <p class="font-semibold text-gray-900">{{ card.customer_name || "—" }}</p>
            <p class="mt-0.5 text-xs text-gray-600">{{ formatDate(card.delivery_date) }}</p>
            <p v-if="card.assigned_to" class="text-[10px] text-gray-500">Asignado: {{ card.assigned_to }}</p>
            <p v-if="card.top_alert_title" class="mt-1 text-xs text-amber-700 truncate">{{ card.top_alert_title }}</p>
            <p class="mt-1 text-xs" :class="marginClass(card.gross_margin_pct)">Margen {{ (card.gross_margin_pct ?? 0).toFixed(1) }}%</p>
            <div class="mt-3 flex flex-wrap gap-1" @click.stop>
              <button
                type="button"
                :disabled="actioningId === card.work_order_id"
                class="rounded bg-emerald-600 px-2 py-1 text-xs font-medium text-white hover:bg-emerald-700 disabled:opacity-50"
                @click="runAction(card, 'finish')"
              >
                Finalizar
              </button>
              <select
                class="rounded border border-gray-300 text-xs py-1 pr-6 bg-white"
                @change="onAssign(card, $event.target.value); $event.target.value = ''"
              >
                <option value="">Asignar</option>
                <option v-for="u in systemUsers" :key="u.name" :value="u.name">{{ u.full_name || u.name }}</option>
              </select>
            </div>
          </div>
          <p v-if="board.in_progress.length === 0" class="py-8 text-center text-sm text-gray-500">Ninguna en proceso</p>
        </div>
      </div>

      <!-- Finalizado -->
      <div class="flex flex-col rounded-xl border border-emerald-200 bg-white shadow-sm">
        <div class="rounded-t-xl border-b border-emerald-200 bg-emerald-50 px-4 py-3">
          <h2 class="text-base font-bold uppercase tracking-wide text-emerald-800">Finalizado</h2>
          <p class="mt-0.5 text-xs text-emerald-700">{{ board.done.length }} OT(s)</p>
        </div>
        <div class="flex-1 space-y-3 overflow-y-auto p-3 min-h-[200px]">
          <div
            v-for="card in board.done"
            :key="card.work_order_id"
            class="rounded-lg border border-gray-200 bg-white p-4 shadow-sm transition hover:shadow-md cursor-pointer"
            @click="openQuickView(card)"
          >
            <p class="text-[10px] font-mono text-gray-400">{{ card.work_order_id }}</p>
            <p class="font-semibold text-gray-900">{{ card.customer_name || "—" }}</p>
            <p class="mt-0.5 text-xs text-gray-600">{{ formatDate(card.delivery_date) }}</p>
            <p class="mt-1 text-xs" :class="marginClass(card.gross_margin_pct)">Margen {{ (card.gross_margin_pct ?? 0).toFixed(1) }}%</p>
            <div class="mt-2" @click.stop>
              <button
                type="button"
                class="rounded border border-gray-400 px-2 py-1 text-xs text-gray-700 hover:bg-gray-100"
                @click="openQuickView(card)"
              >
                Ver
              </button>
            </div>
          </div>
          <p v-if="board.done.length === 0" class="py-8 text-center text-sm text-gray-500">Ninguna finalizada</p>
        </div>
      </div>
    </div>

    <QuickViewWorkOrder
      :work-order-id="quickViewId"
      :visible="quickViewVisible"
      @close="quickViewVisible = false"
    />

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
  </div>
</template>

<script setup>
import { ref, watch, onMounted } from "vue";
import { useRoute } from "vue-router";
import { Loader2 } from "lucide-vue-next";
import { call } from "@/api/frappe";
import QuickViewWorkOrder from "@/components/QuickViewWorkOrder.vue";

const route = useRoute();
const sectorKey = ref(route.params.sectorKey || "");
const sectorName = ref(sectorKey.value.replace(/-/g, " ").replace(/\b\w/g, (c) => c.toUpperCase()));
const loading = ref(true);
const error = ref(null);
const actioningId = ref(null);
const systemUsers = ref([]);
const toastVisible = ref(false);
const toastMessage = ref("");
const toastError = ref(false);

const board = ref({
  pending: [],
  in_progress: [],
  done: [],
});

const quickViewId = ref(null);
const quickViewVisible = ref(false);

watch(
  () => route.params.sectorKey,
  (newKey) => {
    sectorKey.value = newKey || "";
    sectorName.value = (sectorKey.value || "").replace(/-/g, " ").replace(/\b\w/g, (c) => c.toUpperCase());
    fetchBoard();
  },
  { immediate: false }
);

onMounted(() => {
  loadUsers();
  fetchBoard();
});

function loadUsers() {
  call("mathipe_ui.api.get_system_users")
    .then((res) => {
      const list = res?.message ?? res ?? [];
      systemUsers.value = Array.isArray(list) ? list : [];
    })
    .catch(() => {
      systemUsers.value = [];
    });
}

function fetchBoard() {
  if (!sectorKey.value) {
    error.value = "Sector no especificado.";
    loading.value = false;
    return;
  }
  loading.value = true;
  error.value = null;
  call("mathipe_ui.api.get_sector_board", { sector_key: sectorKey.value, only_open: 1 })
    .then((res) => {
      const data = res?.message ?? res ?? {};
      board.value = {
        pending: data.pending || [],
        in_progress: data.in_progress || [],
        done: data.done || [],
      };
    })
    .catch((e) => {
      error.value = e.message || "Error al cargar el tablero.";
      board.value = { pending: [], in_progress: [], done: [] };
    })
    .finally(() => {
      loading.value = false;
    });
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

function marginClass(pct) {
  if (pct == null) return "text-gray-600";
  if (pct >= 25) return "text-emerald-600";
  if (pct >= 15) return "text-amber-600";
  return "text-red-600";
}

function openQuickView(card) {
  const id = card?.work_order_id || card?.name;
  if (id) {
    quickViewId.value = id;
    quickViewVisible.value = true;
  }
}

function showToast(message, isError = false) {
  toastMessage.value = message;
  toastError.value = isError;
  toastVisible.value = true;
  setTimeout(() => { toastVisible.value = false; }, 3000);
}

function runAction(card, action) {
  const wid = card.work_order_id;
  const rowId = card.stage_row_id;
  if (!wid || !rowId) return;
  actioningId.value = wid;
  call("mathipe_ui.api.update_wo_stage", {
    work_order_id: wid,
    stage_row_id: rowId,
    action,
  })
    .then((res) => {
      const detail = res?.message ?? res;
      if (detail && detail.work_order_id) {
        showToast("Estado actualizado.");
        fetchBoard();
      }
    })
    .catch((e) => {
      showToast(e.message || "Error al actualizar.", true);
    })
    .finally(() => {
      actioningId.value = null;
    });
}

function onAssign(card, userId) {
  if (!userId || !card.work_order_id || !card.stage_row_id) return;
  actioningId.value = card.work_order_id;
  call("mathipe_ui.api.update_wo_stage", {
    work_order_id: card.work_order_id,
    stage_row_id: card.stage_row_id,
    action: "assign",
    assigned_to: userId,
  })
    .then(() => {
      showToast("Asignación actualizada.");
      fetchBoard();
    })
    .catch((e) => {
      showToast(e.message || "Error al asignar.", true);
    })
    .finally(() => {
      actioningId.value = null;
    });
}
</script>

<template>
  <Teleport to="body">
    <Transition name="overlay">
      <div
        v-if="visible"
        class="fixed inset-0 z-50 flex justify-end"
        aria-modal="true"
        role="dialog"
      >
        <div class="fixed inset-0 bg-black/40" aria-hidden="true" @click="$emit('close')" />
        <Transition name="drawer">
          <aside
            v-if="visible"
            class="relative flex h-full w-full max-w-md flex-col bg-white shadow-xl"
          >
            <!-- Header -->
            <div class="flex shrink-0 items-center justify-between border-b border-gray-200 px-4 py-3">
              <h2 class="text-lg font-semibold text-gray-900">OT {{ workOrderId || "—" }}</h2>
              <button
                type="button"
                class="rounded-lg p-2 text-gray-500 hover:bg-gray-100 hover:text-gray-700"
                aria-label="Cerrar"
                @click="$emit('close')"
              >
                <X class="h-5 w-5" />
              </button>
            </div>

            <!-- Content: scroll independiente -->
            <div class="flex-1 overflow-y-auto p-4">
              <div v-if="loading" class="flex items-center justify-center py-12">
                <Loader2 class="h-8 w-8 animate-spin text-indigo-500" />
              </div>
              <div v-else-if="error" class="rounded-lg border border-red-200 bg-red-50 p-3 text-sm text-red-700">
                {{ error }}
              </div>
              <template v-else-if="detail">
                <!-- Cliente -->
                <p class="text-sm font-medium text-gray-500">Cliente</p>
                <p class="mt-0.5 text-base text-gray-900">{{ detail.customer_name || detail.customer || "—" }}</p>

                <!-- Entrega -->
                <p class="mt-4 text-sm font-medium text-gray-500">Entrega</p>
                <p class="mt-0.5 text-base text-gray-900">{{ formatDate(detail.delivery_date) }}</p>

                <!-- Estado -->
                <p class="mt-4 text-sm font-medium text-gray-500">Estado</p>
                <p class="mt-0.5">
                  <span class="inline-flex rounded px-2 py-0.5 text-sm font-medium" :class="statusBadgeClass(detail.status)">{{ detail.status || "—" }}</span>
                </p>

                <!-- Margen -->
                <p class="mt-4 text-sm font-medium text-gray-500">Margen</p>
                <p class="mt-0.5 text-base font-medium" :class="marginClass(detail.gross_margin_pct)">{{ (detail.gross_margin_pct ?? 0).toFixed(1) }}%</p>

                <!-- Alertas (resumen) -->
                <div v-if="(detail.alerts_summary?.danger || 0) + (detail.alerts_summary?.warning || 0) + (detail.alerts_summary?.info || 0) > 0" class="mt-4">
                  <p class="text-sm font-medium text-gray-500">Alertas</p>
                  <div class="mt-1 flex flex-wrap gap-1">
                    <span v-if="(detail.alerts_summary?.danger || 0) > 0" class="rounded bg-red-100 px-2 py-0.5 text-xs text-red-800">{{ detail.alerts_summary.danger }} peligro</span>
                    <span v-if="(detail.alerts_summary?.warning || 0) > 0" class="rounded bg-amber-100 px-2 py-0.5 text-xs text-amber-800">{{ detail.alerts_summary.warning }} advertencia</span>
                    <span v-if="(detail.alerts_summary?.info || 0) > 0" class="rounded bg-blue-100 px-2 py-0.5 text-xs text-blue-800">{{ detail.alerts_summary.info }} info</span>
                  </div>
                  <p v-if="detail.top_alert_title" class="mt-1 text-xs text-gray-600">{{ detail.top_alert_title }}</p>
                </div>

                <!-- Ítems (compacto) -->
                <div class="mt-4">
                  <p class="text-sm font-medium text-gray-500">Ítems ({{ (detail.items || []).length }})</p>
                  <ul class="mt-1 space-y-1 rounded border border-gray-200 bg-gray-50 p-2 text-sm">
                    <li v-for="item in (detail.items || []).slice(0, 8)" :key="item.name" class="flex justify-between gap-2">
                      <span class="truncate text-gray-700">{{ item.description || item.item_code || item.name }}</span>
                      <span class="shrink-0 text-gray-500">×{{ item.qty || 0 }}</span>
                    </li>
                    <li v-if="(detail.items || []).length > 8" class="text-xs text-gray-500">+ {{ (detail.items || []).length - 8 }} más</li>
                  </ul>
                </div>

                <!-- Usuarios asignados -->
                <div v-if="(detail.assigned_users || []).length" class="mt-4">
                  <p class="text-sm font-medium text-gray-500">Asignados</p>
                  <p class="mt-0.5 text-sm text-gray-700">{{ (detail.assigned_users || []).map((u) => u.full_name || u.user).join(", ") }}</p>
                </div>

                <!-- Último cambio de estado -->
                <div v-if="(detail.status_log || []).length" class="mt-4">
                  <p class="text-sm font-medium text-gray-500">Último cambio</p>
                  <p class="mt-0.5 text-xs text-gray-600">
                    {{ (detail.status_log || [])[0].to_status }} — {{ (detail.status_log || [])[0].changed_by }} · {{ formatDateTime((detail.status_log || [])[0].changed_at) }}
                  </p>
                </div>

                <!-- Acciones -->
                <div class="mt-6 flex flex-wrap gap-2 border-t border-gray-200 pt-4">
                  <template v-if="(detail.status || '').toLowerCase() === 'waitingapproval'">
                    <button
                      type="button"
                      class="rounded-lg bg-emerald-600 px-3 py-2 text-sm font-medium text-white hover:bg-emerald-700 disabled:opacity-50"
                      :disabled="actionLoading"
                      @click="runAction('approve')"
                    >
                      <Loader2 v-if="actionLoading" class="h-4 w-4 animate-spin inline" />
                      Aprobar
                    </button>
                  </template>
                  <template v-else-if="(detail.status || '').toLowerCase() === 'approved'">
                    <button
                      type="button"
                      class="rounded-lg bg-blue-600 px-3 py-2 text-sm font-medium text-white hover:bg-blue-700 disabled:opacity-50"
                      :disabled="actionLoading"
                      @click="runAction('start_production')"
                    >
                      <Loader2 v-if="actionLoading" class="h-4 w-4 animate-spin inline" />
                      Iniciar producción
                    </button>
                  </template>
                  <template v-else-if="(detail.status || '').toLowerCase() === 'production'">
                    <button
                      type="button"
                      class="rounded-lg bg-emerald-600 px-3 py-2 text-sm font-medium text-white hover:bg-emerald-700 disabled:opacity-50"
                      :disabled="actionLoading"
                      @click="runAction('finish')"
                    >
                      <Loader2 v-if="actionLoading" class="h-4 w-4 animate-spin inline" />
                      Finalizar
                    </button>
                  </template>
                  <button
                    type="button"
                    class="rounded-lg border border-gray-300 bg-white px-3 py-2 text-sm font-medium text-gray-700 hover:bg-gray-50"
                    @click="goToFullDetail"
                  >
                    Ver detalle completo
                  </button>
                </div>
              </template>
            </div>
          </aside>
        </Transition>
      </div>
    </Transition>
  </Teleport>
</template>

<script setup>
import { ref, watch } from "vue";
import { useRouter } from "vue-router";
import { X, Loader2 } from "lucide-vue-next";
import { call } from "@/api/frappe";

const props = defineProps({
  workOrderId: { type: String, default: null },
  visible: { type: Boolean, default: false },
});
const emit = defineEmits(["close"]);

const router = useRouter();
const loading = ref(false);
const error = ref(null);
const detail = ref(null);
const actionLoading = ref(false);

function formatDate(val) {
  if (!val) return "—";
  try {
    return new Date(val).toLocaleDateString("es-AR", { day: "2-digit", month: "2-digit", year: "numeric" });
  } catch (_) {
    return String(val);
  }
}

function formatDateTime(val) {
  if (!val) return "—";
  try {
    return new Date(val).toLocaleString("es-AR", { day: "2-digit", month: "2-digit", year: "numeric", hour: "2-digit", minute: "2-digit" });
  } catch (_) {
    return String(val);
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

async function fetchDetail() {
  if (!props.workOrderId) {
    detail.value = null;
    return;
  }
  loading.value = true;
  error.value = null;
  detail.value = null;
  try {
    const res = await call("mathipe_ui.api.get_work_order_details", { work_order_id: props.workOrderId });
    detail.value = res?.message ?? res ?? null;
  } catch (e) {
    error.value = e.message || "Error al cargar la OT.";
  } finally {
    loading.value = false;
  }
}

function goToFullDetail() {
  const so = detail.value?.sales_order;
  if (so) {
    emit("close");
    router.push({ path: "/orden/" + so });
  }
}

async function runAction(action) {
  if (!detail.value?.name) return;
  actionLoading.value = true;
  try {
    let res;
    if (action === "approve") {
      res = await call("mathipe_ui.api.approve_work_order", { work_order_id: detail.value.name, comment: "" });
    } else if (action === "start_production") {
      res = await call("mathipe_ui.api.update_work_order_status", { work_order_id: detail.value.name, to_status: "Production", comment: "" });
    } else if (action === "finish") {
      res = await call("mathipe_ui.api.update_work_order_status", { work_order_id: detail.value.name, to_status: "Done", comment: "" });
    }
    const updated = res?.message ?? res ?? {};
    detail.value = { ...detail.value, ...updated, status: updated.new_status ?? updated.status ?? detail.value.status, alerts_summary: updated.alerts_summary ?? detail.value.alerts_summary };
  } catch (e) {
    error.value = e.message || "Error al ejecutar.";
  } finally {
    actionLoading.value = false;
  }
}

watch(
  () => [props.visible, props.workOrderId],
  ([vis, id]) => {
    if (vis && id) fetchDetail();
    if (!vis) {
      detail.value = null;
      error.value = null;
    }
  },
  { immediate: true }
);
</script>

<style scoped>
.overlay-enter-active,
.overlay-leave-active { transition: opacity 0.2s ease; }
.overlay-enter-from,
.overlay-leave-to { opacity: 0; }
.drawer-enter-active,
.drawer-leave-active { transition: transform 0.25s ease; }
.drawer-enter-from,
.drawer-leave-to { transform: translateX(100%); }
</style>

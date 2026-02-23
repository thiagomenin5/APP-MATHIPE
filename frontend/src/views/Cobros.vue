<template>
  <div class="max-w-6xl">
    <h1 class="mb-6 text-xl font-semibold text-gray-900">Cuentas por Cobrar (Señas y Saldos)</h1>

    <div v-if="loading" class="flex items-center justify-center gap-2 py-12">
      <Loader2 class="h-8 w-8 animate-spin text-indigo-600" />
      <p class="text-sm text-gray-500">Cargando...</p>
    </div>

    <div v-else class="overflow-hidden rounded-lg border border-gray-200 bg-white shadow-sm">
      <table class="min-w-full divide-y divide-gray-200">
        <thead class="bg-gray-50">
          <tr>
            <th scope="col" class="px-5 py-3 text-left text-xs font-medium uppercase tracking-wider text-gray-500">Orden</th>
            <th scope="col" class="px-5 py-3 text-left text-xs font-medium uppercase tracking-wider text-gray-500">Cliente</th>
            <th scope="col" class="px-5 py-3 text-right text-xs font-medium uppercase tracking-wider text-gray-500">Total</th>
            <th scope="col" class="px-5 py-3 text-right text-xs font-medium uppercase tracking-wider text-gray-500">Pagado</th>
            <th scope="col" class="px-5 py-3 text-right text-xs font-medium uppercase tracking-wider text-gray-500">Saldo Pendiente</th>
            <th scope="col" class="px-5 py-3 text-right text-xs font-medium uppercase tracking-wider text-gray-500">Acción</th>
          </tr>
        </thead>
        <tbody class="divide-y divide-gray-200 bg-white">
          <tr v-for="row in collections" :key="row.name" class="transition-colors hover:bg-gray-50">
            <td class="whitespace-nowrap px-5 py-3 text-sm font-medium text-gray-900">{{ row.name }}</td>
            <td class="px-5 py-3 text-sm text-gray-600">{{ row.customer_name || "—" }}</td>
            <td class="whitespace-nowrap px-5 py-3 text-sm text-right text-gray-600">{{ formatMoney(row.grand_total) }}</td>
            <td class="whitespace-nowrap px-5 py-3 text-sm text-right text-gray-600">{{ formatMoney(row.advance_paid) }}</td>
            <td class="whitespace-nowrap px-5 py-3 text-sm text-right font-medium" :class="row.pending_amount > 0 ? 'text-red-600' : 'text-gray-600'">
              {{ formatMoney(row.pending_amount) }}
            </td>
            <td class="whitespace-nowrap px-5 py-3 text-right">
              <button
                type="button"
                class="inline-flex items-center gap-1.5 rounded-lg bg-indigo-600 px-3 py-1.5 text-xs font-medium text-white hover:bg-indigo-700"
                :disabled="saving === row.name"
                @click="openPaymentModal(row)"
              >
                <Banknote class="h-3.5 w-3.5" />
                Cobrar
              </button>
            </td>
          </tr>
          <tr v-if="!loading && collections.length === 0">
            <td colspan="6" class="px-5 py-10 text-center text-sm text-gray-500">
              No hay órdenes con saldo pendiente.
            </td>
          </tr>
        </tbody>
      </table>
    </div>

    <!-- Modal Registrar Pago -->
    <Teleport to="body">
      <div
        v-if="showPaymentModal"
        class="fixed inset-0 z-50 flex items-center justify-center bg-black/50 p-4"
        @click.self="closePaymentModal"
      >
        <div class="w-full max-w-md rounded-xl border border-gray-200 bg-white p-6 shadow-xl" role="dialog" aria-modal="true">
          <h2 class="mb-4 text-lg font-semibold text-gray-900">Registrar Pago</h2>
          <template v-if="selectedOrder">
            <p class="mb-1 text-sm text-gray-600">Cobrando Orden <strong>#{{ selectedOrder.name }}</strong></p>
            <p class="mb-4 text-sm text-gray-600">
              Saldo Pendiente: <strong class="text-red-600">{{ formatMoney(selectedOrder.pending_amount) }}</strong>
            </p>
          </template>
          <form class="space-y-4" @submit.prevent="savePayment">
            <div>
              <label for="paid-amount" class="mb-1 block text-sm font-medium text-gray-700">Monto a Cobrar</label>
              <input
                id="paid-amount"
                v-model.number="form.paid_amount"
                type="number"
                step="0.01"
                min="0.01"
                required
                class="w-full rounded-lg border border-gray-300 py-2.5 px-4 text-sm focus:border-indigo-500 focus:outline-none focus:ring-2 focus:ring-indigo-500"
              />
            </div>
            <div>
              <label for="mode-of-payment" class="mb-1 block text-sm font-medium text-gray-700">Medio de Pago</label>
              <select
                id="mode-of-payment"
                v-model="form.mode_of_payment"
                class="w-full rounded-lg border border-gray-300 py-2.5 px-4 text-sm focus:border-indigo-500 focus:outline-none focus:ring-2 focus:ring-indigo-500"
              >
                <option value="Efectivo">Efectivo</option>
                <option value="Transferencia">Transferencia</option>
                <option value="Tarjeta">Tarjeta</option>
              </select>
            </div>
            <div class="flex justify-end gap-3 pt-2">
              <button
                type="button"
                class="rounded-lg border border-gray-300 bg-white px-4 py-2.5 text-sm font-medium text-gray-700 hover:bg-gray-50"
                @click="closePaymentModal"
              >
                Cancelar
              </button>
              <button
                type="submit"
                :disabled="saving"
                class="inline-flex items-center gap-2 rounded-lg bg-indigo-600 px-4 py-2.5 text-sm font-medium text-white hover:bg-indigo-700 disabled:opacity-50"
              >
                <Wallet class="h-4 w-4" />
                {{ saving ? "Guardando..." : "Guardar Pago" }}
              </button>
            </div>
          </form>
        </div>
      </div>
    </Teleport>

    <!-- Toast -->
    <Teleport to="body">
      <div
        v-if="toastVisible"
        class="fixed bottom-6 left-1/2 z-[60] -translate-x-1/2 rounded-lg px-4 py-2.5 text-sm font-medium shadow-lg"
        :class="toastError ? 'bg-red-600 text-white' : 'bg-indigo-600 text-white'"
        role="status"
      >
        {{ toastMessage }}
      </div>
    </Teleport>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from "vue";
import { Loader2, Banknote, Wallet } from "lucide-vue-next";
import { call } from "@/api/frappe";

const loading = ref(true);
const saving = ref(null);
const collections = ref([]);
const showPaymentModal = ref(false);
const selectedOrder = ref(null);
const toastVisible = ref(false);
const toastMessage = ref("");
const toastError = ref(false);

const form = reactive({
  paid_amount: 0,
  mode_of_payment: "Efectivo",
});

const CURRENCY_OPTIONS = {
  style: "currency",
  currency: "ARS",
  minimumFractionDigits: 0,
  maximumFractionDigits: 2,
};

function formatMoney(value) {
  if (value == null || value === "") return "—";
  return new Intl.NumberFormat("es-AR", CURRENCY_OPTIONS).format(value);
}

function openPaymentModal(order) {
  selectedOrder.value = order;
  form.paid_amount = order.pending_amount;
  form.mode_of_payment = "Efectivo";
  showPaymentModal.value = true;
}

function closePaymentModal() {
  showPaymentModal.value = false;
  selectedOrder.value = null;
}

function showToast(message, isError = false) {
  toastMessage.value = message;
  toastError.value = isError;
  toastVisible.value = true;
  setTimeout(() => {
    toastVisible.value = false;
  }, 3500);
}

async function fetchCollections() {
  loading.value = true;
  try {
    const res = await call("mathipe_ui.api.get_pending_collections", {});
    const data = res?.message ?? res ?? [];
    collections.value = Array.isArray(data) ? data : [];
  } catch (e) {
    console.error("Cobros:", e);
    collections.value = [];
  } finally {
    loading.value = false;
  }
}

async function savePayment() {
  if (!selectedOrder.value || saving.value) return;
  const amount = Number(form.paid_amount);
  if (amount <= 0) {
    showToast("El monto debe ser mayor a cero.", true);
    return;
  }
  saving.value = selectedOrder.value.name;
  try {
    const res = await call("mathipe_ui.api.register_payment", {
      order_id: selectedOrder.value.name,
      paid_amount: amount,
      mode_of_payment: form.mode_of_payment,
    });
    const data = res?.message ?? res ?? {};
    if (data.ok) {
      showToast("Pago registrado correctamente.");
      closePaymentModal();
      await fetchCollections();
    } else {
      showToast(data.error || data.message || "Error al registrar el pago.", true);
    }
  } catch (e) {
    showToast(e.message || "Error al registrar el pago.", true);
  } finally {
    saving.value = null;
  }
}

onMounted(() => {
  fetchCollections();
});
</script>

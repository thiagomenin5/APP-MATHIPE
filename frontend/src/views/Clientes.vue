<template>
  <div class="max-w-5xl">
    <div class="mb-6 flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
      <h1 class="text-xl font-semibold text-gray-900">Directorio de Clientes</h1>
      <button
        type="button"
        class="inline-flex items-center gap-2 rounded-lg bg-indigo-600 px-4 py-2.5 text-sm font-medium text-white shadow-sm hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:ring-offset-2"
        @click="openModal"
      >
        <UserPlus class="h-5 w-5" />
        Nuevo Cliente
      </button>
    </div>

    <div class="mb-4">
      <div class="relative">
        <Search class="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-gray-400" />
        <input
          v-model="searchTerm"
          type="text"
          placeholder="Buscar cliente..."
          class="w-full rounded-lg border border-gray-300 py-2.5 pl-10 pr-4 text-sm placeholder-gray-500 focus:border-indigo-500 focus:outline-none focus:ring-2 focus:ring-indigo-500 sm:max-w-xs"
          @input="onSearchInput"
        />
      </div>
    </div>

    <div class="overflow-hidden rounded-lg border border-gray-200 bg-white shadow-sm">
      <div v-if="loading" class="flex items-center justify-center gap-2 px-5 py-12 text-sm text-gray-500">
        <Loader2 class="h-5 w-5 animate-spin" />
        Cargando...
      </div>
      <template v-else>
        <table class="min-w-full divide-y divide-gray-200">
          <thead class="bg-gray-50">
            <tr>
              <th scope="col" class="px-5 py-3 text-left text-xs font-medium uppercase tracking-wider text-gray-500">ID / Razón Social</th>
              <th scope="col" class="px-5 py-3 text-left text-xs font-medium uppercase tracking-wider text-gray-500">Grupo</th>
              <th scope="col" class="px-5 py-3 text-left text-xs font-medium uppercase tracking-wider text-gray-500">Territorio</th>
            </tr>
          </thead>
          <tbody class="divide-y divide-gray-200 bg-white">
            <tr v-for="row in customers" :key="row.name" class="transition-colors hover:bg-gray-50">
              <td class="px-5 py-3">
                <span class="font-medium text-gray-900">{{ row.customer_name || row.name || "—" }}</span>
                <span v-if="row.name && row.name !== row.customer_name" class="ml-1 text-xs text-gray-500">{{ row.name }}</span>
              </td>
              <td class="whitespace-nowrap px-5 py-3 text-sm text-gray-600">{{ row.customer_group || "—" }}</td>
              <td class="whitespace-nowrap px-5 py-3 text-sm text-gray-600">{{ row.territory || "—" }}</td>
            </tr>
            <tr v-if="!loading && customers.length === 0">
              <td colspan="3" class="px-5 py-10 text-center text-sm text-gray-500">
                No se encontraron clientes.
              </td>
            </tr>
          </tbody>
        </table>
      </template>
    </div>

    <!-- Modal Nuevo Cliente -->
    <Teleport to="body">
      <div
        v-if="isModalOpen"
        class="fixed inset-0 z-50 flex items-center justify-center bg-black/50 p-4"
        @click.self="closeModal"
      >
        <div class="w-full max-w-md rounded-xl border border-gray-200 bg-white p-6 shadow-xl" role="dialog" aria-modal="true" aria-labelledby="modal-clientes-title">
          <h2 id="modal-clientes-title" class="mb-4 text-lg font-semibold text-gray-900">Nuevo Cliente</h2>
          <form class="space-y-4" @submit.prevent="createClient">
            <div>
              <label for="customer-name" class="mb-1 block text-sm font-medium text-gray-700">Razón Social / Nombre <span class="text-red-500">*</span></label>
              <input
                id="customer-name"
                v-model="form.customer_name"
                type="text"
                required
                class="w-full rounded-lg border border-gray-300 py-2.5 px-4 text-sm focus:border-indigo-500 focus:outline-none focus:ring-2 focus:ring-indigo-500"
                placeholder="Ej: Gráfica López S.A."
              />
            </div>
            <p class="text-xs text-gray-500">
              Se creará en el grupo <strong>Clientes</strong> y territorio <strong>General</strong> (igual que el resto).
            </p>
            <div class="flex justify-end gap-3 pt-2">
              <button
                type="button"
                class="rounded-lg border border-gray-300 bg-white px-4 py-2.5 text-sm font-medium text-gray-700 hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:ring-offset-2"
                @click="closeModal"
              >
                Cancelar
              </button>
              <button
                type="submit"
                :disabled="saving"
                class="rounded-lg bg-indigo-600 px-4 py-2.5 text-sm font-medium text-white hover:bg-indigo-700 disabled:opacity-50 focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:ring-offset-2"
              >
                {{ saving ? "Creando..." : "Crear Cliente" }}
              </button>
            </div>
          </form>
        </div>
      </div>
    </Teleport>

    <Transition name="toast">
      <div
        v-if="toastVisible"
        class="fixed bottom-6 left-1/2 z-[60] min-w-[280px] -translate-x-1/2 rounded-xl px-5 py-4 text-center text-base font-medium text-white shadow-lg"
        :class="toastError ? 'bg-red-600' : 'bg-emerald-600'"
        role="alert"
      >
        {{ toastMessage }}
      </div>
    </Transition>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from "vue";
import { Users, Search, UserPlus, Loader2 } from "lucide-vue-next";
import { call } from "@/api/frappe";

const loading = ref(true);
const saving = ref(false);
const customers = ref([]);
const searchTerm = ref("");
const isModalOpen = ref(false);
const toastVisible = ref(false);
const toastMessage = ref("");
const toastError = ref(false);

let searchDebounce = null;

const form = reactive({
  customer_name: "",
});

function onSearchInput() {
  clearTimeout(searchDebounce);
  searchDebounce = setTimeout(fetchCustomers, 300);
}

async function fetchCustomers() {
  loading.value = true;
  try {
    const res = await call("mathipe_ui.api.get_all_customers", {
      search_term: searchTerm.value.trim(),
    });
    const data = res?.message ?? res ?? [];
    customers.value = Array.isArray(data) ? data : [];
  } catch (e) {
    console.error("Clientes:", e);
    customers.value = [];
  } finally {
    loading.value = false;
  }
}

function openModal() {
  form.customer_name = "";
  isModalOpen.value = true;
}

function closeModal() {
  isModalOpen.value = false;
}

async function createClient() {
  if (saving.value) return;
  saving.value = true;
  try {
    const res = await call("mathipe_ui.api.create_simple_customer", {
      customer_name: form.customer_name.trim(),
    });
    const data = res?.message ?? res ?? {};
    if (data.ok) {
      showToast("Cliente creado correctamente.");
      closeModal();
      await fetchCustomers();
    } else {
      showToast(data.error || "Error al crear.", true);
    }
  } catch (e) {
    showToast(e.message || "Error al crear el cliente.", true);
  } finally {
    saving.value = false;
  }
}

function showToast(message, isError = false) {
  toastMessage.value = message;
  toastError.value = isError;
  toastVisible.value = true;
  setTimeout(() => {
    toastVisible.value = false;
  }, 3500);
}

onMounted(() => {
  fetchCustomers();
});
</script>

<style scoped>
.toast-enter-active,
.toast-leave-active {
  transition: opacity 0.2s ease, transform 0.2s ease;
}
.toast-enter-from,
.toast-leave-to {
  opacity: 0;
  transform: translate(-50%, 12px);
}
</style>

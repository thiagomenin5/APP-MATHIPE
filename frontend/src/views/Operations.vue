<template>
  <div class="max-w-5xl">
    <div class="mb-6 flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
      <h1 class="text-xl font-semibold text-gray-900">Operaciones</h1>
      <button type="button" class="inline-flex items-center gap-2 rounded-lg bg-indigo-600 px-4 py-2.5 text-sm font-medium text-white shadow-sm hover:bg-indigo-700" @click="openModal()">
        <Plus class="h-5 w-5" /> Nuevo
      </button>
    </div>
    <div class="mb-4">
      <div class="relative">
        <Search class="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-gray-400" />
        <input v-model="searchTerm" type="text" placeholder="Buscar operación..." class="w-full rounded-lg border border-gray-300 py-2.5 pl-10 pr-4 text-sm focus:border-indigo-500 focus:outline-none focus:ring-2 focus:ring-indigo-500 sm:max-w-xs" @input="onSearchInput" />
      </div>
    </div>
    <div class="overflow-hidden rounded-lg border border-gray-200 bg-white shadow-sm">
      <div v-if="loading" class="flex items-center justify-center gap-2 px-5 py-12 text-sm text-gray-500"><Loader2 class="h-5 w-5 animate-spin" /> Cargando...</div>
      <template v-else>
        <table class="min-w-full divide-y divide-gray-200">
          <thead class="bg-gray-50">
            <tr>
              <th class="px-5 py-3 text-left text-xs font-medium uppercase text-gray-500">Nombre</th>
              <th class="px-5 py-3 text-left text-xs font-medium uppercase text-gray-500">Modo costo</th>
              <th class="px-5 py-3 text-left text-xs font-medium uppercase text-gray-500">Costo fijo</th>
              <th class="px-5 py-3 text-right text-xs font-medium uppercase text-gray-500">Acciones</th>
            </tr>
          </thead>
          <tbody class="divide-y divide-gray-200 bg-white">
            <tr v-for="row in items" :key="row.name" class="hover:bg-gray-50">
              <td class="px-5 py-3 font-medium text-gray-900">{{ row.operation_name || row.name }}</td>
              <td class="px-5 py-3 text-sm text-gray-600">{{ row.costing_mode || "—" }}</td>
              <td class="px-5 py-3 text-sm text-gray-600">{{ row.cost_fixed != null ? row.cost_fixed : "—" }}</td>
              <td class="px-5 py-3 text-right">
                <button type="button" class="text-indigo-600 hover:underline" @click="openModal(row)">Editar</button>
                <button type="button" class="ml-3 text-red-600 hover:underline" @click="confirmDelete(row)">Eliminar</button>
              </td>
            </tr>
            <tr v-if="!loading && items.length === 0"><td colspan="4" class="px-5 py-10 text-center text-sm text-gray-500">No hay operaciones.</td></tr>
          </tbody>
        </table>
      </template>
    </div>
    <Teleport to="body">
      <div v-if="isModalOpen" class="fixed inset-0 z-50 flex items-center justify-center bg-black/50 p-4" @click.self="closeModal">
        <div class="w-full max-w-lg rounded-xl border border-gray-200 bg-white p-6 shadow-xl">
          <h2 class="mb-4 text-lg font-semibold text-gray-900">{{ editingName ? 'Editar operación' : 'Nueva operación' }}</h2>
          <form class="space-y-4" @submit.prevent="save">
            <div>
              <label class="mb-1 block text-sm font-medium text-gray-700">Nombre <span class="text-red-500">*</span></label>
              <input v-model="form.operation_name" type="text" required :readonly="!!editingName" class="w-full rounded-lg border border-gray-300 py-2.5 px-4 text-sm focus:border-indigo-500 focus:outline-none focus:ring-2 focus:ring-indigo-500" />
            </div>
            <div>
              <label class="mb-1 block text-sm font-medium text-gray-700">Sector <span class="text-red-500">*</span></label>
              <select v-model="form.sector_key" required class="w-full rounded-lg border border-gray-300 py-2.5 px-4 text-sm focus:border-indigo-500 focus:outline-none focus:ring-2 focus:ring-indigo-500">
                <option value="">Seleccionar</option>
                <option v-for="s in sectors" :key="s.name" :value="s.name">{{ s.sector_name || s.sector_key }}</option>
              </select>
            </div>
            <div>
              <label class="mb-1 block text-sm font-medium text-gray-700">Modo costo</label>
              <select v-model="form.costing_mode" class="w-full rounded-lg border border-gray-300 py-2.5 px-4 text-sm focus:border-indigo-500 focus:outline-none focus:ring-2 focus:ring-indigo-500">
                <option value="">—</option>
                <option value="Fixed">Fixed</option>
                <option value="TimeBased">TimeBased</option>
                <option value="PerUnit">PerUnit</option>
                <option value="AreaBased">AreaBased</option>
              </select>
            </div>
            <div>
              <label class="mb-1 block text-sm font-medium text-gray-700">Costo fijo</label>
              <input v-model.number="form.cost_fixed" type="number" step="0.01" class="w-full rounded-lg border border-gray-300 py-2.5 px-4 text-sm focus:border-indigo-500 focus:outline-none focus:ring-2 focus:ring-indigo-500" />
            </div>
            <div class="flex items-center gap-2">
              <input id="active" v-model="form.active" type="checkbox" class="h-4 w-4 rounded border-gray-300 text-indigo-600 focus:ring-indigo-500" />
              <label for="active" class="text-sm text-gray-700">Activa</label>
            </div>
            <div class="flex justify-end gap-3 pt-2">
              <button type="button" class="rounded-lg border border-gray-300 bg-white px-4 py-2.5 text-sm font-medium text-gray-700 hover:bg-gray-50" @click="closeModal">Cancelar</button>
              <button type="submit" :disabled="saving" class="rounded-lg bg-indigo-600 px-4 py-2.5 text-sm font-medium text-white hover:bg-indigo-700 disabled:opacity-50">{{ saving ? 'Guardando...' : 'Guardar' }}</button>
            </div>
          </form>
        </div>
      </div>
    </Teleport>
    <Transition name="toast">
      <div v-if="toastVisible" class="fixed bottom-6 left-1/2 z-[60] min-w-[280px] -translate-x-1/2 rounded-xl px-5 py-4 text-center text-base font-medium text-white shadow-lg" :class="toastError ? 'bg-red-600' : 'bg-emerald-600'">{{ toastMessage }}</div>
    </Transition>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from "vue";
import { Plus, Search, Loader2 } from "lucide-vue-next";
import { call } from "@/api/frappe";

const loading = ref(true);
const saving = ref(false);
const items = ref([]);
const sectors = ref([]);
const searchTerm = ref("");
const isModalOpen = ref(false);
const editingName = ref(null);
const toastVisible = ref(false);
const toastMessage = ref("");
const toastError = ref(false);
let searchDebounce = null;
const form = reactive({ operation_name: "", sector_key: "", costing_mode: "", cost_fixed: null, active: true });

function onSearchInput() { clearTimeout(searchDebounce); searchDebounce = setTimeout(fetchList, 300); }
async function fetchList() {
  loading.value = true;
  try {
    const res = await call("mathipe_ui.api.list_operations", { search: searchTerm.value.trim() || undefined });
    items.value = Array.isArray(res?.message ?? res) ? (res?.message ?? res) : [];
  } catch (_) { items.value = []; }
  finally { loading.value = false; }
}
async function loadSectors() {
  try {
    const res = await call("mathipe_ui.api.get_company_setup");
    sectors.value = (res?.message ?? res)?.sectors ?? [];
  } catch (_) { sectors.value = []; }
}
function openModal(row = null) {
  editingName.value = row ? (row.name || row.operation_name) : null;
  form.operation_name = row ? (row.operation_name || row.name) : "";
  form.sector_key = row ? row.sector_key : (sectors.value[0]?.name || "");
  form.costing_mode = row ? row.costing_mode : "";
  form.cost_fixed = row != null && row.cost_fixed != null ? row.cost_fixed : null;
  form.active = row != null ? !!row.active : true;
  isModalOpen.value = true;
}
function closeModal() { isModalOpen.value = false; }
async function save() {
  if (saving.value) return;
  saving.value = true;
  try {
    const payload = { operation_name: form.operation_name.trim(), sector_key: form.sector_key, costing_mode: form.costing_mode || null, cost_fixed: form.cost_fixed, active: form.active };
    if (editingName.value) payload.name = editingName.value;
    await call("mathipe_ui.api.save_operation", { payload });
    showToast("Guardado correctamente.");
    closeModal();
    await fetchList();
  } catch (e) { showToast(e.message || "Error al guardar.", true); }
  finally { saving.value = false; }
}
function confirmDelete(row) {
  if (!confirm("¿Eliminar esta operación?")) return;
  const name = row.name || row.operation_name;
  call("mathipe_ui.api.delete_operation", { name }).then(() => { showToast("Eliminada."); fetchList(); }).catch((e) => showToast(e.message || "Error al eliminar.", true));
}
function showToast(message, isError = false) { toastMessage.value = message; toastError.value = isError; toastVisible.value = true; setTimeout(() => { toastVisible.value = false; }, 3500); }
onMounted(() => { loadSectors(); fetchList(); });
</script>
<style scoped>.toast-enter-active, .toast-leave-active { transition: opacity 0.2s ease, transform 0.2s ease; } .toast-enter-from, .toast-leave-to { opacity: 0; transform: translate(-50%, 12px); }</style>

<template>
  <div class="max-w-5xl">
    <div class="mb-6 flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
      <h1 class="text-xl font-semibold text-gray-900">Materiales</h1>
      <button type="button" class="inline-flex items-center gap-2 rounded-lg bg-indigo-600 px-4 py-2.5 text-sm font-medium text-white shadow-sm hover:bg-indigo-700" @click="openModal()">
        <Plus class="h-5 w-5" /> Nuevo
      </button>
    </div>
    <div class="mb-4">
      <div class="relative">
        <Search class="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-gray-400" />
        <input v-model="searchTerm" type="text" placeholder="Buscar material..." class="w-full rounded-lg border border-gray-300 py-2.5 pl-10 pr-4 text-sm sm:max-w-xs" @input="onSearchInput" />
      </div>
    </div>
    <div class="overflow-hidden rounded-lg border border-gray-200 bg-white shadow-sm">
      <div v-if="loading" class="flex items-center justify-center gap-2 px-5 py-12 text-sm text-gray-500"><Loader2 class="h-5 w-5 animate-spin" /> Cargando...</div>
      <template v-else>
        <table class="min-w-full divide-y divide-gray-200">
          <thead class="bg-gray-50">
            <tr>
              <th class="px-5 py-3 text-left text-xs font-medium uppercase text-gray-500">Nombre</th>
              <th class="px-5 py-3 text-left text-xs font-medium uppercase text-gray-500">Tipo</th>
              <th class="px-5 py-3 text-left text-xs font-medium uppercase text-gray-500">Unidad</th>
              <th class="px-5 py-3 text-left text-xs font-medium uppercase text-gray-500">Costo/ud</th>
              <th class="px-5 py-3 text-right text-xs font-medium uppercase text-gray-500">Acciones</th>
            </tr>
          </thead>
          <tbody class="divide-y divide-gray-200 bg-white">
            <tr v-for="row in items" :key="row.name" class="hover:bg-gray-50">
              <td class="px-5 py-3 font-medium text-gray-900">{{ row.material_name || row.name }}</td>
              <td class="px-5 py-3 text-sm text-gray-600">{{ row.material_type || "—" }}</td>
              <td class="px-5 py-3 text-sm text-gray-600">{{ row.unit_type || "—" }}</td>
              <td class="px-5 py-3 text-sm text-gray-600">{{ row.cost_per_unit != null ? row.cost_per_unit : "—" }}</td>
              <td class="px-5 py-3 text-right">
                <button type="button" class="text-indigo-600 hover:underline" @click="openModal(row)">Editar</button>
                <button type="button" class="ml-3 text-red-600 hover:underline" @click="confirmDelete(row)">Eliminar</button>
              </td>
            </tr>
            <tr v-if="!loading && items.length === 0"><td colspan="5" class="px-5 py-10 text-center text-sm text-gray-500">No hay materiales.</td></tr>
          </tbody>
        </table>
      </template>
    </div>
    <Teleport to="body">
      <div v-if="isModalOpen" class="fixed inset-0 z-50 flex items-center justify-center bg-black/50 p-4" @click.self="closeModal">
        <div class="w-full max-w-lg rounded-xl border border-gray-200 bg-white p-6 shadow-xl">
          <h2 class="mb-4 text-lg font-semibold text-gray-900">{{ editingName ? "Editar material" : "Nuevo material" }}</h2>
          <form class="space-y-4" @submit.prevent="save">
            <div>
              <label class="mb-1 block text-sm font-medium text-gray-700">Nombre *</label>
              <input v-model="form.material_name" type="text" required :readonly="!!editingName" class="w-full rounded-lg border border-gray-300 py-2.5 px-4 text-sm" />
            </div>
            <div>
              <label class="mb-1 block text-sm font-medium text-gray-700">Tipo</label>
              <select v-model="form.material_type" class="w-full rounded-lg border border-gray-300 py-2.5 px-4 text-sm">
                <option value="">—</option>
                <option value="Papel">Papel</option>
                <option value="Vinilo">Vinilo</option>
                <option value="Lona">Lona</option>
                <option value="Cartón">Cartón</option>
                <option value="Otro">Otro</option>
              </select>
            </div>
            <div>
              <label class="mb-1 block text-sm font-medium text-gray-700">Unidad *</label>
              <select v-model="form.unit_type" required class="w-full rounded-lg border border-gray-300 py-2.5 px-4 text-sm">
                <option value="m2">m2</option>
                <option value="hoja">hoja</option>
                <option value="unidad">unidad</option>
              </select>
            </div>
            <div>
              <label class="mb-1 block text-sm font-medium text-gray-700">Costo por unidad *</label>
              <input v-model.number="form.cost_per_unit" type="number" step="0.01" required class="w-full rounded-lg border border-gray-300 py-2.5 px-4 text-sm" />
            </div>
            <div class="flex items-center gap-2">
              <input id="active-mat" v-model="form.active" type="checkbox" class="h-4 w-4 rounded border-gray-300 text-indigo-600" />
              <label for="active-mat" class="text-sm text-gray-700">Activo</label>
            </div>
            <div class="flex justify-end gap-3 pt-2">
              <button type="button" class="rounded-lg border border-gray-300 bg-white px-4 py-2.5 text-sm font-medium text-gray-700 hover:bg-gray-50" @click="closeModal">Cancelar</button>
              <button type="submit" :disabled="saving" class="rounded-lg bg-indigo-600 px-4 py-2.5 text-sm font-medium text-white hover:bg-indigo-700 disabled:opacity-50">{{ saving ? "Guardando..." : "Guardar" }}</button>
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
const searchTerm = ref("");
const isModalOpen = ref(false);
const editingName = ref(null);
const toastVisible = ref(false);
const toastMessage = ref("");
const toastError = ref(false);
let searchDebounce = null;
const form = reactive({ material_name: "", material_type: "", unit_type: "m2", cost_per_unit: null, active: true });

function onSearchInput() {
  clearTimeout(searchDebounce);
  searchDebounce = setTimeout(fetchList, 300);
}
async function fetchList() {
  loading.value = true;
  try {
    const res = await call("mathipe_ui.api.list_materials", { search: searchTerm.value.trim() || undefined });
    items.value = Array.isArray(res?.message ?? res) ? (res?.message ?? res) : [];
  } catch (_) {
    items.value = [];
  } finally {
    loading.value = false;
  }
}
function openModal(row = null) {
  editingName.value = row ? (row.name || row.material_name) : null;
  form.material_name = row ? (row.material_name || row.name) : "";
  form.material_type = row ? row.material_type : "";
  form.unit_type = row ? row.unit_type : "m2";
  form.cost_per_unit = row != null && row.cost_per_unit != null ? row.cost_per_unit : null;
  form.active = row != null ? !!row.active : true;
  isModalOpen.value = true;
}
function closeModal() {
  isModalOpen.value = false;
}
async function save() {
  if (saving.value) return;
  saving.value = true;
  try {
    const payload = {
      material_name: form.material_name.trim(),
      material_type: form.material_type || null,
      unit_type: form.unit_type,
      cost_per_unit: form.cost_per_unit,
      active: form.active,
    };
    if (editingName.value) payload.name = editingName.value;
    await call("mathipe_ui.api.save_material", { payload });
    showToast("Guardado correctamente.");
    closeModal();
    await fetchList();
  } catch (e) {
    showToast(e.message || "Error al guardar.", true);
  } finally {
    saving.value = false;
  }
}
function confirmDelete(row) {
  if (!confirm("¿Eliminar este material?")) return;
  const name = row.name || row.material_name;
  call("mathipe_ui.api.delete_material", { name })
    .then(() => {
      showToast("Eliminado.");
      fetchList();
    })
    .catch((e) => showToast(e.message || "Error al eliminar.", true));
}
function showToast(message, isError = false) {
  toastMessage.value = message;
  toastError.value = isError;
  toastVisible.value = true;
  setTimeout(() => {
    toastVisible.value = false;
  }, 3500);
}
onMounted(() => fetchList());
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

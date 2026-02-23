<template>
  <div class="max-w-6xl">
    <h1 class="mb-6 text-xl font-semibold text-gray-900">Inventario de Papeles e Insumos</h1>

    <div class="overflow-hidden rounded-lg border border-gray-200 bg-white shadow-sm">
      <div v-if="loading" class="flex items-center justify-center gap-2 px-5 py-12 text-sm text-gray-500">
        <Loader2 class="h-5 w-5 animate-spin" />
        Cargando...
      </div>

      <template v-else>
        <table class="min-w-full divide-y divide-gray-200">
          <thead class="bg-gray-50">
            <tr>
              <th scope="col" class="px-5 py-3 text-left text-xs font-medium uppercase tracking-wider text-gray-500">Material</th>
              <th scope="col" class="px-5 py-3 text-left text-xs font-medium uppercase tracking-wider text-gray-500">Categoría</th>
              <th scope="col" class="px-5 py-3 text-left text-xs font-medium uppercase tracking-wider text-gray-500">Stock</th>
              <th scope="col" class="px-5 py-3 text-left text-xs font-medium uppercase tracking-wider text-gray-500">Costo por Hoja</th>
              <th scope="col" class="relative w-24 px-2 py-3"><span class="sr-only">Guardar</span></th>
            </tr>
          </thead>
          <tbody class="divide-y divide-gray-200 bg-white">
            <tr
              v-for="row in materials"
              :key="row.name"
              class="transition-colors hover:bg-gray-50"
            >
              <td class="whitespace-nowrap px-5 py-3 text-sm font-medium text-gray-900">{{ row.material_name || "—" }}</td>
              <td class="whitespace-nowrap px-5 py-3 text-sm text-gray-600">{{ row.category || "—" }}</td>
              <td class="whitespace-nowrap px-5 py-3">
                <span class="inline-flex rounded-full bg-gray-100 px-2.5 py-0.5 text-xs font-medium text-gray-600">N/A</span>
              </td>
              <td class="whitespace-nowrap px-5 py-3">
                <div class="flex items-center gap-2">
                  <input
                    v-model.number="row._editCost"
                    type="number"
                    step="0.01"
                    min="0"
                    class="w-28 rounded-lg border border-gray-300 py-2 px-3 text-sm focus:border-indigo-500 focus:outline-none focus:ring-2 focus:ring-indigo-500"
                    placeholder="0"
                    @keydown.enter="saveCost(row)"
                  />
                </div>
              </td>
              <td class="whitespace-nowrap px-2 py-3">
                <button
                  type="button"
                  class="rounded bg-indigo-600 px-3 py-1.5 text-xs font-medium text-white hover:bg-indigo-700 disabled:opacity-50"
                  :disabled="saving === row.name || !hasCostChanged(row)"
                  @click="saveCost(row)"
                >
                  {{ saving === row.name ? "..." : "Guardar" }}
                </button>
              </td>
            </tr>
            <tr v-if="!loading && materials.length === 0">
              <td colspan="5" class="px-5 py-10 text-center text-sm text-gray-500">
                No hay materiales cargados. Creálos desde el Desk: Mathipe Print Material.
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
import { Loader2 } from "lucide-vue-next";
import { call } from "@/api/frappe";

const loading = ref(true);
const saving = ref(null);
const materials = ref([]);

function hasCostChanged(row) {
  const edit = row._editCost;
  if (edit === undefined || edit === "") return false;
  const num = Number(edit);
  if (Number.isNaN(num) || num < 0) return false;
  return Math.abs(num - (row.cost_per_sheet || 0)) > 1e-6;
}

async function fetchMaterials() {
  loading.value = true;
  try {
    const res = await call("mathipe_ui.api.get_inventory_materials", {});
    const data = res?.message ?? res ?? [];
    const list = Array.isArray(data) ? data : [];
    materials.value = list.map((r) => ({
      ...r,
      _editCost: r.cost_per_sheet,
    }));
  } catch (e) {
    console.error("Inventario:", e);
    materials.value = [];
  } finally {
    loading.value = false;
  }
}

async function saveCost(row) {
  if (saving.value || !hasCostChanged(row)) return;
  const newCost = Number(row._editCost);
  if (Number.isNaN(newCost) || newCost < 0) return;
  saving.value = row.name;
  try {
    await call("mathipe_ui.api.update_material_cost", {
      material_name: row.name,
      new_cost: newCost,
    });
    row.cost_per_sheet = newCost;
  } catch (e) {
    console.error("update_material_cost:", e);
  } finally {
    saving.value = null;
  }
}

onMounted(() => {
  fetchMaterials();
});
</script>

<template>
  <div class="max-w-4xl">
    <div class="mb-6 flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
      <h1 class="text-xl font-semibold text-gray-900">Catálogo de Productos</h1>
      <button
        type="button"
        class="inline-flex items-center justify-center gap-2 rounded-lg bg-indigo-600 px-4 py-2.5 text-sm font-medium text-white shadow-sm hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:ring-offset-2"
        @click="openModal()"
      >
        <Plus class="h-5 w-5" />
        Nuevo Producto
      </button>
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
              <th scope="col" class="px-5 py-3 text-left text-xs font-medium uppercase tracking-wider text-gray-500">Nombre del Producto</th>
              <th scope="col" class="px-5 py-3 text-right text-xs font-medium uppercase tracking-wider text-gray-500">Costo de Arranque</th>
              <th scope="col" class="px-5 py-3 text-right text-xs font-medium uppercase tracking-wider text-gray-500">Costo Impresión x Cara</th>
              <th scope="col" class="relative w-28 px-2 py-3 text-right text-xs font-medium uppercase tracking-wider text-gray-500">Acciones</th>
            </tr>
          </thead>
          <tbody class="divide-y divide-gray-200 bg-white">
            <tr v-for="row in products" :key="row.name" class="transition-colors hover:bg-gray-50">
              <td class="whitespace-nowrap px-5 py-3 text-sm font-medium text-gray-900">{{ row.product_name || "—" }}</td>
              <td class="whitespace-nowrap px-5 py-3 text-right text-sm text-gray-700">{{ formatCurrency(row.base_setup_cost) }}</td>
              <td class="whitespace-nowrap px-5 py-3 text-right text-sm text-gray-700">{{ formatCurrency(row.print_cost_per_side) }}</td>
              <td class="whitespace-nowrap px-2 py-3">
                <div class="flex justify-end gap-1">
                  <button
                    type="button"
                    class="rounded p-2 text-gray-500 hover:bg-gray-100 hover:text-indigo-600"
                    aria-label="Editar"
                    @click="openModal(row)"
                  >
                    <Pencil class="h-4 w-4" />
                  </button>
                  <button
                    type="button"
                    class="rounded p-2 text-gray-500 hover:bg-gray-100 hover:text-red-600"
                    aria-label="Eliminar"
                    @click="confirmDelete(row)"
                  >
                    <Trash2 class="h-4 w-4" />
                  </button>
                </div>
              </td>
            </tr>
            <tr v-if="!loading && products.length === 0">
              <td colspan="4" class="px-5 py-10 text-center text-sm text-gray-500">
                No hay productos. Creá uno con "+ Nuevo Producto".
              </td>
            </tr>
          </tbody>
        </table>
      </template>
    </div>

    <!-- Modal Crear/Editar -->
    <Teleport to="body">
      <div
        v-if="isModalOpen"
        class="fixed inset-0 z-50 flex items-center justify-center bg-black/50 p-4"
        @click.self="closeModal"
      >
        <div class="w-full max-w-md rounded-xl border border-gray-200 bg-white p-6 shadow-xl" role="dialog" aria-modal="true" aria-labelledby="modal-title">
          <h2 id="modal-title" class="mb-4 text-lg font-semibold text-gray-900">
            {{ editingProduct ? "Editar Producto" : "Nuevo Producto" }}
          </h2>
          <form class="space-y-4" @submit.prevent="saveProduct">
            <div>
              <label for="product-name" class="mb-1 block text-sm font-medium text-gray-700">Nombre del Producto</label>
              <input
                id="product-name"
                v-model="form.product_name"
                type="text"
                required
                class="w-full rounded-lg border border-gray-300 py-2.5 px-4 text-sm focus:border-indigo-500 focus:outline-none focus:ring-2 focus:ring-indigo-500"
                placeholder="Ej: Tarjeta Personal"
              />
            </div>
            <div>
              <label for="base-setup-cost" class="mb-1 block text-sm font-medium text-gray-700">Costo de Arranque</label>
              <input
                id="base-setup-cost"
                v-model.number="form.base_setup_cost"
                type="number"
                step="0.01"
                min="0"
                class="w-full rounded-lg border border-gray-300 py-2.5 px-4 text-sm focus:border-indigo-500 focus:outline-none focus:ring-2 focus:ring-indigo-500"
                placeholder="0"
              />
            </div>
            <div>
              <label for="print-cost" class="mb-1 block text-sm font-medium text-gray-700">Costo Impresión por Cara</label>
              <input
                id="print-cost"
                v-model.number="form.print_cost_per_side"
                type="number"
                step="0.01"
                min="0"
                class="w-full rounded-lg border border-gray-300 py-2.5 px-4 text-sm focus:border-indigo-500 focus:outline-none focus:ring-2 focus:ring-indigo-500"
                placeholder="0"
              />
            </div>
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
                {{ saving ? "Guardando..." : "Guardar" }}
              </button>
            </div>
          </form>
        </div>
      </div>
    </Teleport>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from "vue";
import { Plus, Pencil, Trash2, Loader2 } from "lucide-vue-next";
import { call } from "@/api/frappe";

const loading = ref(true);
const saving = ref(false);
const products = ref([]);
const isModalOpen = ref(false);
const editingProduct = ref(null);

const form = reactive({
  product_name: "",
  base_setup_cost: 0,
  print_cost_per_side: 0,
});

function resetForm() {
  form.product_name = "";
  form.base_setup_cost = 0;
  form.print_cost_per_side = 0;
  editingProduct.value = null;
}

function openModal(product = null) {
  editingProduct.value = product ?? null;
  if (product) {
    form.product_name = product.product_name || "";
    form.base_setup_cost = product.base_setup_cost ?? 0;
    form.print_cost_per_side = product.print_cost_per_side ?? 0;
  } else {
    resetForm();
  }
  isModalOpen.value = true;
}

function closeModal() {
  isModalOpen.value = false;
  resetForm();
}

async function fetchProducts() {
  loading.value = true;
  try {
    const res = await call("mathipe_ui.api.get_all_print_products", {});
    const data = res?.message ?? res ?? [];
    products.value = Array.isArray(data) ? data : [];
  } catch (e) {
    console.error("Productos:", e);
    products.value = [];
  } finally {
    loading.value = false;
  }
}

async function saveProduct() {
  if (saving.value) return;
  saving.value = true;
  try {
    await call("mathipe_ui.api.save_print_product", {
      name: editingProduct.value?.name ?? "",
      product_name: form.product_name.trim(),
      base_setup_cost: form.base_setup_cost,
      print_cost_per_side: form.print_cost_per_side,
    });
    await fetchProducts();
    closeModal();
  } catch (e) {
    console.error("save_print_product:", e);
    alert(e.message || "Error al guardar.");
  } finally {
    saving.value = false;
  }
}

function confirmDelete(row) {
  if (!confirm(`¿Eliminar el producto "${row.product_name || row.name}"?`)) return;
  deleteProduct(row.name);
}

async function deleteProduct(name) {
  try {
    await call("mathipe_ui.api.delete_print_product", { name });
    await fetchProducts();
  } catch (e) {
    console.error("delete_print_product:", e);
    alert(e.message || "Error al eliminar.");
  }
}

function formatCurrency(value) {
  if (value == null || value === "") return "—";
  return new Intl.NumberFormat("es-AR", {
    style: "currency",
    currency: "ARS",
    minimumFractionDigits: 0,
    maximumFractionDigits: 2,
  }).format(value);
}

onMounted(() => {
  fetchProducts();
});
</script>

<template>
  <div class="space-y-4">
    <!-- Header: Volver + Título + Nuevo -->
    <div class="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
      <div class="flex items-center gap-3">
        <button
          type="button"
          class="inline-flex items-center gap-2 rounded-lg border border-gray-300 bg-white px-3 py-2 text-sm font-medium text-gray-700 shadow-sm hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:ring-offset-2"
          @click="$emit('back')"
        >
          <ArrowLeft class="h-4 w-4" />
          Volver
        </button>
        <h2 class="text-lg font-semibold text-gray-900">{{ listTitle }}</h2>
      </div>
      <button
        v-if="config?.canCreate"
        type="button"
        class="inline-flex items-center gap-2 rounded-lg bg-indigo-600 px-4 py-2.5 text-sm font-medium text-white shadow-sm hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:ring-offset-2"
        @click="openModal"
      >
        <Plus class="h-4 w-4" />
        Nuevo {{ config?.singularLabel ?? doctype }}
      </button>
    </div>

    <!-- Buscador -->
    <div class="rounded-lg border border-gray-200 bg-white p-4 shadow-sm">
      <label class="sr-only" for="master-search">Buscar</label>
      <div class="relative">
        <Search class="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-gray-400" />
        <input
          id="master-search"
          v-model="searchText"
          type="text"
          placeholder="Buscar por nombre, código..."
          class="w-full rounded-lg border border-gray-300 py-2.5 pl-10 pr-4 text-sm focus:border-indigo-500 focus:outline-none focus:ring-2 focus:ring-indigo-500"
          @input="onSearchInput"
        />
      </div>
    </div>

    <!-- Loading -->
    <div v-if="loading" class="flex flex-col items-center justify-center gap-4 py-12">
      <Loader2 class="h-10 w-10 animate-spin text-indigo-600" />
      <p class="text-sm text-gray-500">Cargando lista...</p>
    </div>

    <!-- Tabla -->
    <div v-else class="overflow-hidden rounded-lg border border-gray-200 bg-white shadow-sm">
      <div class="overflow-x-auto">
        <table class="min-w-full divide-y divide-gray-200">
          <thead class="bg-gray-50">
            <tr>
              <th
                v-for="col in tableColumns"
                :key="col.key"
                scope="col"
                class="px-5 py-3 text-left text-xs font-medium uppercase tracking-wider text-gray-500"
              >
                {{ col.label }}
              </th>
            </tr>
          </thead>
          <tbody class="divide-y divide-gray-200 bg-white">
            <tr
              v-for="row in rows"
              :key="row.name"
              class="hover:bg-gray-50"
            >
              <td
                v-for="col in tableColumns"
                :key="col.key"
                class="whitespace-nowrap px-5 py-3 text-sm text-gray-900"
              >
                <span v-if="col.key === 'status'" :class="statusClass(row)">
                  {{ formatStatus(row) }}
                </span>
                <span v-else>{{ formatCell(row[col.key], col) }}</span>
              </td>
            </tr>
            <tr v-if="!loading && rows.length === 0">
              <td :colspan="tableColumns.length" class="px-5 py-8 text-center text-sm text-gray-500">
                No hay registros. {{ config?.canCreate ? "Usá «Nuevo» para agregar uno." : "" }}
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>

    <!-- Modal Alta rápida -->
    <Teleport to="body">
      <div
        v-if="showModal"
        class="fixed inset-0 z-50 flex items-center justify-center bg-black/50 p-4"
        role="dialog"
        aria-modal="true"
        aria-labelledby="modal-title"
        @click.self="showModal = false"
      >
        <div
          class="w-full max-w-md rounded-xl bg-white p-6 shadow-xl"
          @click.stop
        >
          <h3 id="modal-title" class="mb-4 text-lg font-semibold text-gray-900">
            Nuevo {{ config?.singularLabel ?? doctype }}
          </h3>
          <form @submit.prevent="submitNew">
            <div class="space-y-4">
              <div
                v-for="field in modalFields"
                :key="field.key"
              >
                <label :for="'modal-' + field.key" class="mb-1 block text-sm font-medium text-gray-700">
                  {{ field.label }}
                  <span v-if="field.required" class="text-red-500">*</span>
                </label>
                <input
                  :id="'modal-' + field.key"
                  v-model="form[field.key]"
                  type="text"
                  :required="field.required"
                  class="w-full rounded-lg border border-gray-300 py-2 px-3 text-sm focus:border-indigo-500 focus:outline-none focus:ring-2 focus:ring-indigo-500"
                />
              </div>
            </div>
            <div class="mt-6 flex justify-end gap-3">
              <button
                type="button"
                class="rounded-lg border border-gray-300 bg-white px-4 py-2 text-sm font-medium text-gray-700 hover:bg-gray-50"
                @click="showModal = false"
              >
                Cancelar
              </button>
              <button
                type="submit"
                class="rounded-lg bg-indigo-600 px-4 py-2 text-sm font-medium text-white hover:bg-indigo-700 disabled:opacity-50"
                :disabled="saving"
              >
                {{ saving ? "Guardando…" : "Guardar" }}
              </button>
            </div>
          </form>
        </div>
      </div>
    </Teleport>
  </div>
</template>

<script setup>
import { ref, computed, watch } from "vue";
import { ArrowLeft, Loader2, Plus, Search } from "lucide-vue-next";
import { call } from "@/api/frappe";

const props = defineProps({
  doctype: { type: String, required: true },
});

defineEmits(["back"]);

const DOCTYPE_CONFIG = {
  Item: {
    singularLabel: "Producto/Servicio",
    listTitle: "Productos y Servicios",
    listFields: ["name", "item_name", "item_group", "standard_rate", "disabled"],
    tableColumns: [
      { key: "name", label: "Código" },
      { key: "item_name", label: "Nombre" },
      { key: "item_group", label: "Grupo" },
      { key: "standard_rate", label: "P. unit." },
      { key: "status", label: "Estado" },
    ],
    canCreate: true,
    modalFields: [
      { key: "item_code", label: "Código", required: true },
      { key: "item_name", label: "Nombre", required: true },
      { key: "item_group", label: "Grupo de ítem", required: true },
      { key: "standard_rate", label: "Precio estándar", required: false },
    ],
    buildDoc(form) {
      return {
        doctype: "Item",
        item_code: form.item_code?.trim() || undefined,
        item_name: form.item_name?.trim() || undefined,
        item_group: form.item_group?.trim() || undefined,
        standard_rate: form.standard_rate ? parseFloat(form.standard_rate) : 0,
      };
    },
  },
  Customer: {
    singularLabel: "Cliente",
    listTitle: "Clientes",
    listFields: ["name", "customer_name", "customer_type", "disabled"],
    tableColumns: [
      { key: "name", label: "ID" },
      { key: "customer_name", label: "Nombre" },
      { key: "customer_type", label: "Tipo" },
      { key: "status", label: "Estado" },
    ],
    canCreate: true,
    modalFields: [
      { key: "customer_name", label: "Nombre del cliente", required: true },
      { key: "customer_type", label: "Tipo (ej: Company)", required: false },
    ],
    buildDoc(form) {
      return {
        doctype: "Customer",
        customer_name: form.customer_name?.trim() || undefined,
        customer_type: form.customer_type?.trim() || "Company",
      };
    },
  },
  User: {
    singularLabel: "Usuario",
    listTitle: "Usuarios",
    listFields: ["name", "full_name", "enabled"],
    tableColumns: [
      { key: "name", label: "Usuario" },
      { key: "full_name", label: "Nombre completo" },
      { key: "status", label: "Estado" },
    ],
    canCreate: false,
    modalFields: [],
    buildDoc() {
      return null;
    },
  },
};

const config = computed(() => DOCTYPE_CONFIG[props.doctype] || null);
const listTitle = computed(() => config.value?.listTitle ?? props.doctype);
const tableColumns = computed(() => config.value?.tableColumns ?? [{ key: "name", label: "Nombre" }]);
const modalFields = computed(() => config.value?.modalFields ?? []);

const searchText = ref("");
const searchDebounce = ref(null);
const rows = ref([]);
const loading = ref(true);
const showModal = ref(false);
const saving = ref(false);
const form = ref({});

function getDefaultForm() {
  const fields = config.value?.modalFields ?? [];
  return fields.reduce((acc, f) => ({ ...acc, [f.key]: "" }), {});
}

function onSearchInput() {
  clearTimeout(searchDebounce.value);
  searchDebounce.value = setTimeout(fetchList, 300);
}

function formatCell(value, col) {
  if (value == null || value === "") return "—";
  if (col.key === "standard_rate" && typeof value === "number") {
    return new Intl.NumberFormat("es-AR", { style: "currency", currency: "ARS", minimumFractionDigits: 0 }).format(value);
  }
  return String(value);
}

function formatStatus(row) {
  if (row.disabled === 1 || row.disabled === true) return "Inactivo";
  if (row.enabled === 0 || row.enabled === false) return "Deshabilitado";
  return "Activo";
}

function statusClass(row) {
  if (row.disabled === 1 || row.disabled === true) return "text-amber-600";
  if (row.enabled === 0 || row.enabled === false) return "text-red-600";
  return "text-green-600";
}

async function fetchList() {
  if (!config.value) return;
  loading.value = true;
  try {
    const txt = searchText.value.trim();
    const filters = txt
      ? [[props.doctype, "name", "like", `%${txt}%`]]
      : undefined;
    const res = await call("frappe.client.get_list", {
      doctype: props.doctype,
      fields: config.value.listFields,
      filters,
      limit_page_length: 50,
      order_by: "modified desc",
    });
    rows.value = res.message ?? res ?? [];
  } catch (e) {
    console.error("MasterList fetch:", e);
    rows.value = [];
  } finally {
    loading.value = false;
  }
}

function openModal() {
  form.value = getDefaultForm();
  showModal.value = true;
}

async function submitNew() {
  if (!config.value?.buildDoc) return;
  const doc = config.value.buildDoc(form.value);
  if (!doc) return;
  saving.value = true;
  try {
    await call("frappe.client.insert", { doc });
    showModal.value = false;
    await fetchList();
  } catch (e) {
    console.error("MasterList insert:", e);
    alert(e.message || "Error al guardar.");
  } finally {
    saving.value = false;
  }
}

watch(
  () => props.doctype,
  () => {
    searchText.value = "";
    fetchList();
  },
  { immediate: true }
);
</script>

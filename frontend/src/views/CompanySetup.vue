<template>
  <div class="max-w-4xl">
    <h1 class="mb-6 text-xl font-semibold text-gray-900">Configuración de Mi Empresa</h1>
    <div v-if="loading" class="flex items-center gap-2 text-sm text-gray-500">
      <Loader2 class="h-5 w-5 animate-spin" />
      Cargando...
    </div>
    <div v-else class="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
      <router-link
        to="/empresa/maquinas"
        class="flex items-center justify-between rounded-xl border border-gray-200 bg-white p-5 shadow-sm transition hover:border-indigo-300 hover:shadow-md"
      >
        <span class="font-medium text-gray-900">Máquinas</span>
        <span class="rounded-full bg-gray-100 px-3 py-1 text-sm font-medium text-gray-700">{{ counts.machines }}</span>
      </router-link>
      <router-link
        to="/empresa/materiales"
        class="flex items-center justify-between rounded-xl border border-gray-200 bg-white p-5 shadow-sm transition hover:border-indigo-300 hover:shadow-md"
      >
        <span class="font-medium text-gray-900">Materiales</span>
        <span class="rounded-full bg-gray-100 px-3 py-1 text-sm font-medium text-gray-700">{{ counts.materials }}</span>
      </router-link>
      <router-link
        to="/empresa/operaciones"
        class="flex items-center justify-between rounded-xl border border-gray-200 bg-white p-5 shadow-sm transition hover:border-indigo-300 hover:shadow-md"
      >
        <span class="font-medium text-gray-900">Operaciones</span>
        <span class="rounded-full bg-gray-100 px-3 py-1 text-sm font-medium text-gray-700">{{ counts.operations }}</span>
      </router-link>
      <router-link
        to="/empresa/rutas"
        class="flex items-center justify-between rounded-xl border border-gray-200 bg-white p-5 shadow-sm transition hover:border-indigo-300 hover:shadow-md"
      >
        <span class="font-medium text-gray-900">Rutas</span>
        <span class="rounded-full bg-gray-100 px-3 py-1 text-sm font-medium text-gray-700">{{ counts.route_templates }}</span>
      </router-link>
      <router-link
        to="/empresa/plantillas-producto"
        class="flex items-center justify-between rounded-xl border border-gray-200 bg-white p-5 shadow-sm transition hover:border-indigo-300 hover:shadow-md"
      >
        <span class="font-medium text-gray-900">Plantillas de producto</span>
        <span class="rounded-full bg-gray-100 px-3 py-1 text-sm font-medium text-gray-700">{{ counts.product_templates }}</span>
      </router-link>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from "vue";
import { Loader2 } from "lucide-vue-next";
import { call } from "@/api/frappe";

const loading = ref(true);
const counts = ref({
  machines: 0,
  materials: 0,
  operations: 0,
  route_templates: 0,
  product_templates: 0,
});

async function load() {
  loading.value = true;
  try {
    const res = await call("mathipe_ui.api.get_company_setup");
    const data = res?.message ?? res ?? {};
    counts.value = data.counts ?? counts.value;
  } catch (_) {
    counts.value = { machines: 0, materials: 0, operations: 0, route_templates: 0, product_templates: 0 };
  } finally {
    loading.value = false;
  }
}

onMounted(() => load());
</script>

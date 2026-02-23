<template>
  <div>
    <h1 class="mb-6 text-xl font-semibold text-gray-900">Configuración</h1>

    <!-- Grid de tarjetas (cuando no hay sección seleccionada) -->
    <div
      v-if="currentSection === null"
      class="grid grid-cols-1 gap-6 sm:grid-cols-2 lg:grid-cols-3"
    >
      <button
        type="button"
        class="flex flex-col items-center justify-center gap-4 rounded-xl border border-gray-200 bg-white p-8 text-left shadow-sm transition hover:border-indigo-200 hover:shadow-md focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:ring-offset-2"
        @click="currentSection = 'Item'"
      >
        <div class="flex h-14 w-14 items-center justify-center rounded-full bg-indigo-100 text-indigo-600">
          <Package class="h-7 w-7" />
        </div>
        <span class="text-base font-semibold text-gray-900">Productos y Servicios</span>
        <span class="text-sm text-gray-500">Gestionar ítems</span>
      </button>

      <button
        type="button"
        class="flex flex-col items-center justify-center gap-4 rounded-xl border border-gray-200 bg-white p-8 text-left shadow-sm transition hover:border-indigo-200 hover:shadow-md focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:ring-offset-2"
        @click="currentSection = 'Customer'"
      >
        <div class="flex h-14 w-14 items-center justify-center rounded-full bg-indigo-100 text-indigo-600">
          <Users class="h-7 w-7" />
        </div>
        <span class="text-base font-semibold text-gray-900">Clientes</span>
        <span class="text-sm text-gray-500">Base de datos de clientes</span>
      </button>

      <button
        type="button"
        class="flex flex-col items-center justify-center gap-4 rounded-xl border border-gray-200 bg-white p-8 text-left shadow-sm transition hover:border-indigo-200 hover:shadow-md focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:ring-offset-2"
        @click="currentSection = 'User'"
      >
        <div class="flex h-14 w-14 items-center justify-center rounded-full bg-indigo-100 text-indigo-600">
          <UserCircle class="h-7 w-7" />
        </div>
        <span class="text-base font-semibold text-gray-900">Usuarios</span>
        <span class="text-sm text-gray-500">Gestionar empleados</span>
      </button>

      <a
        :href="deskUrl"
        target="_blank"
        rel="noopener noreferrer"
        class="flex flex-col items-center justify-center gap-4 rounded-xl border-2 border-gray-300 bg-white p-8 text-left shadow-sm transition hover:border-red-300 hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-gray-400 focus:ring-offset-2"
      >
        <div class="flex h-14 w-14 items-center justify-center rounded-full bg-gray-100 text-gray-500">
          <Settings class="h-7 w-7" />
        </div>
        <span class="text-base font-semibold text-gray-900">Avanzado (Ir al Desk)</span>
        <span class="text-sm text-gray-500">Abrir ERPNext en nueva pestaña</span>
        <ExternalLink class="h-4 w-4 text-gray-400" />
      </a>
    </div>

    <!-- Listado maestro (cuando hay sección seleccionada) -->
    <MasterList
      v-else
      :doctype="currentSection"
      @back="currentSection = null"
    />
  </div>
</template>

<script setup>
import { ref, computed } from "vue";
import { Package, Users, UserCircle, Settings, ExternalLink } from "lucide-vue-next";
import MasterList from "@/components/MasterList.vue";

const deskUrl = computed(() => {
  const base = typeof window !== "undefined" ? window.location.origin : "";
  return `${base}/app`;
});

const currentSection = ref(null);
</script>

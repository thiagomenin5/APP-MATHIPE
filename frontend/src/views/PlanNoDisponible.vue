<template>
  <div class="flex flex-col items-center justify-center rounded-lg border border-amber-200 bg-amber-50 p-8 text-center">
    <Lock class="mx-auto h-12 w-12 text-amber-500" />
    <h2 class="mt-4 text-lg font-semibold text-gray-800">No disponible en tu plan</h2>
    <p class="mt-2 max-w-sm text-sm text-gray-600">
      {{ message }}
    </p>
    <router-link
      to="/dashboard"
      class="mt-6 inline-flex items-center rounded-lg bg-indigo-600 px-4 py-2 text-sm font-medium text-white hover:bg-indigo-700"
    >
      Ir al Dashboard
    </router-link>
  </div>
</template>

<script setup>
import { computed } from "vue";
import { useRoute } from "vue-router";
import { Lock } from "lucide-vue-next";

const route = useRoute();

const defaultMessages = {
  finanzas: "Tu plan no incluye Finanzas.",
  alertas: "Tu plan no incluye Alertas.",
  analitica: "Tu plan no incluye Analítica.",
  tercerizacion: "Tu plan no incluye Tercerización.",
};

const message = computed(() => {
  const q = route.query || {};
  const m = (q.planMessage && String(q.planMessage).trim()) || (route.meta && route.meta.planMessage);
  if (m) return m;
  const f = (q.feature || "").toLowerCase();
  return defaultMessages[f] || "Este módulo no está incluido en tu plan actual. Contacta a soporte para más información.";
});
</script>

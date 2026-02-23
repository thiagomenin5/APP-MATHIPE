<template>
  <div class="flex flex-col items-center justify-center rounded-xl border border-gray-200 bg-white p-12 text-center shadow-sm">
    <div class="mb-4 flex h-16 w-16 items-center justify-center rounded-full bg-amber-100 text-amber-600">
      <Construction class="h-8 w-8" />
    </div>
    <h2 class="mb-2 text-lg font-semibold text-gray-900">Próximamente</h2>
    <p class="text-sm text-gray-600">{{ routeName }}</p>
  </div>
</template>

<script setup>
import { computed } from "vue";
import { useRoute } from "vue-router";
import { Construction } from "lucide-vue-next";

const route = useRoute();

const routeName = computed(() => {
  return route.meta?.label || route.name || route.path || "Esta sección";
});
</script>

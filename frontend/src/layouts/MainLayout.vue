<template>
  <div class="flex min-h-screen font-sans text-gray-900">
    <Sidebar />

    <!-- Main: topbar + content -->
    <div class="flex min-h-screen flex-1 flex-col pl-64">
      <!-- Topbar -->
      <header class="sticky top-0 z-30 flex h-14 shrink-0 items-center gap-4 border-b border-gray-200 bg-white px-6 shadow-sm">
        <div class="flex flex-1 items-center gap-4">
          <div class="relative flex-1 max-w-md">
            <Search class="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-gray-400" />
            <input
              type="search"
              placeholder="Buscar orden, cliente..."
              class="w-full rounded-lg border border-gray-200 bg-gray-50 py-2 pl-10 pr-4 text-sm placeholder-gray-500 focus:border-indigo-500 focus:bg-white focus:outline-none focus:ring-1 focus:ring-indigo-500"
            />
          </div>
        </div>
        <div class="flex items-center gap-2">
          <button
            type="button"
            class="rounded-lg p-2 text-gray-500 hover:bg-gray-100 hover:text-gray-700"
            aria-label="Notificaciones"
          >
            <Bell class="h-5 w-5" />
          </button>
          <div class="flex h-8 w-8 items-center justify-center rounded-full bg-indigo-600 text-sm font-medium text-white">
            {{ userInitial }}
          </div>
        </div>
      </header>

      <!-- Content -->
      <main class="flex-1 bg-gray-50 p-6">
        <router-view />
      </main>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from "vue";
import { Search, Bell } from "lucide-vue-next";
import { getSession, getBranding } from "@/api/frappe";
import Sidebar from "@/components/Sidebar.vue";

const sessionUser = ref(null);

onMounted(() => {
  getSession().then((u) => {
    sessionUser.value = u;
  });
  getBranding().then((b) => {
    if (b && b.display_name) document.title = b.display_name;
  });
});

const userInitial = computed(() => {
  const u = sessionUser.value;
  if (u && typeof u === "string") return u.charAt(0).toUpperCase();
  return "U";
});
</script>

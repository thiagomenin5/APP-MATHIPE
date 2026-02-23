<template>
  <div class="min-h-screen flex items-center justify-center bg-gray-200">
    <div class="w-full max-w-sm rounded-lg bg-white p-8 shadow">
      <h1 class="mb-6 text-center text-xl font-semibold text-gray-800">{{ displayName }}</h1>
      <form @submit.prevent="onSubmit" class="space-y-4">
        <div>
          <label class="block text-sm font-medium text-gray-700">Usuario</label>
          <input
            v-model="usr"
            type="text"
            class="mt-1 w-full rounded border border-gray-300 px-3 py-2"
            required
          />
        </div>
        <div>
          <label class="block text-sm font-medium text-gray-700">Contraseña</label>
          <input
            v-model="pwd"
            type="password"
            class="mt-1 w-full rounded border border-gray-300 px-3 py-2"
            required
          />
        </div>
        <p v-if="error" class="text-sm text-red-600">{{ error }}</p>
        <button
          type="submit"
          class="w-full rounded bg-blue-600 py-2 text-white hover:bg-blue-700"
          :disabled="loading"
        >
          {{ loading ? "Entrando…" : "Entrar" }}
        </button>
      </form>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from "vue";
import { useRouter, useRoute } from "vue-router";
import { login, getBranding } from "@/api/frappe";

const router = useRouter();
const route = useRoute();
const usr = ref("");
const pwd = ref("");
const error = ref("");
const loading = ref(false);
const displayName = ref("APP Mathipe");

onMounted(async () => {
  try {
    const b = await getBranding();
    displayName.value = (b && b.display_name) || "APP Mathipe";
  } catch (_) {}
});

async function onSubmit() {
  error.value = "";
  loading.value = true;
  try {
    await login(usr.value, pwd.value);
    const redirect = route.query.redirect || "/dashboard";
    router.push(redirect);
  } catch (e) {
    error.value = e.message || "Error al iniciar sesión";
  } finally {
    loading.value = false;
  }
}
</script>

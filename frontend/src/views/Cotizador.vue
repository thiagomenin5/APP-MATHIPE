<template>
  <div class="max-w-6xl">
    <h1 class="mb-6 text-xl font-semibold text-gray-900">Cotizador (Twist Print)</h1>

    <!-- Cliente y entrega -->
    <div class="mb-6 rounded-xl border border-gray-200 bg-white p-6 shadow-sm">
      <h2 class="mb-4 text-base font-semibold text-gray-900">Cliente y entrega</h2>
      <div class="flex flex-wrap gap-4">
        <div class="flex-1 min-w-[200px]">
          <label class="mb-2 block text-sm font-medium text-gray-700">Cliente</label>
          <div class="flex gap-2">
            <div class="relative flex-1">
              <input
                v-model="customerQuery"
                type="text"
                autocomplete="off"
                placeholder="Buscar cliente..."
                class="w-full rounded-lg border border-gray-300 py-2.5 px-4 text-base focus:border-indigo-500 focus:outline-none focus:ring-2 focus:ring-indigo-500"
                @input="onCustomerInput"
                @focus="customerOpen = true"
              />
              <ul
                v-if="customerOpen && (customerOptions.length > 0 || customerQuery.length >= 2)"
                class="absolute z-10 mt-1 max-h-48 w-full overflow-auto rounded-lg border border-gray-200 bg-white py-1 shadow-lg"
              >
                <li
                  v-for="c in customerOptions"
                  :key="c.name"
                  class="cursor-pointer px-4 py-2.5 text-sm hover:bg-indigo-50"
                  @mousedown.prevent="selectCustomer(c)"
                >
                  {{ c.customer_name }} ({{ c.name }})
                </li>
                <li class="border-t border-gray-100 px-4 py-2">
                  <button type="button" class="inline-flex items-center gap-1.5 text-sm text-indigo-600 hover:text-indigo-800" @mousedown.prevent="openNewCustomerModal">
                    <UserPlus class="h-4 w-4" />
                    Nuevo Cliente
                  </button>
                </li>
              </ul>
            </div>
            <button type="button" class="shrink-0 rounded-lg border border-gray-300 bg-white px-3 py-2.5 text-sm font-medium text-gray-700 hover:bg-gray-50" @click="openNewCustomerModal">
              <UserPlus class="h-4 w-4" />
            </button>
          </div>
          <p v-if="selectedCustomer" class="mt-1 text-sm text-indigo-600">{{ selectedCustomer.customer_name }}</p>
        </div>
        <div class="w-40">
          <label class="mb-2 block text-sm font-medium text-gray-700">Fecha entrega</label>
          <input v-model="deliveryDate" type="date" class="w-full rounded-lg border border-gray-300 py-2.5 px-4 text-base focus:border-indigo-500 focus:outline-none focus:ring-2 focus:ring-indigo-500" />
        </div>
      </div>
    </div>

    <!-- Agregar ítem -->
    <div class="mb-6 rounded-xl border border-gray-200 bg-white p-6 shadow-sm">
      <h2 class="mb-4 text-base font-semibold text-gray-900">Agregar ítem</h2>
      <div v-if="loadingCatalog" class="flex items-center gap-2 text-sm text-gray-500">
        <Loader2 class="h-4 w-4 animate-spin" />
        Cargando catálogo...
      </div>
      <template v-else>
        <!-- Opción: por plantilla (Mi Empresa) -->
        <div class="mb-6 rounded-lg border border-gray-100 bg-gray-50 p-4">
          <p class="mb-2 text-sm font-medium text-gray-700">O por plantilla de producto (Mi Empresa)</p>
          <div class="flex flex-wrap items-end gap-3">
            <div class="min-w-[200px]">
              <label class="mb-1 block text-xs text-gray-600">Plantilla</label>
              <select
                v-model="templateItem.product_template"
                class="w-full rounded-lg border border-gray-300 py-2 px-3 text-sm"
                @change="onTemplateSelect"
              >
                <option value="">Seleccionar plantilla</option>
                <option v-for="t in productTemplates" :key="t.name" :value="t.name">
                  {{ t.product_name || t.name }}
                </option>
              </select>
            </div>
            <div v-if="selectedTemplateMeta?.allow_qty !== false" class="w-24">
              <label class="mb-1 block text-xs text-gray-600">Cant.</label>
              <input v-model.number="templateItem.qty" type="number" min="1" class="w-full rounded-lg border border-gray-300 py-2 px-3 text-sm" @input="fetchTemplateBreakdown" />
            </div>
            <template v-if="selectedTemplateMeta?.allow_dimensions">
              <div class="w-24">
                <label class="mb-1 block text-xs text-gray-600">Ancho (mm)</label>
                <input v-model.number="templateItem.width" type="number" min="0" class="w-full rounded-lg border border-gray-300 py-2 px-3 text-sm" @input="fetchTemplateBreakdown" />
              </div>
              <div class="w-24">
                <label class="mb-1 block text-xs text-gray-600">Alto (mm)</label>
                <input v-model.number="templateItem.height" type="number" min="0" class="w-full rounded-lg border border-gray-300 py-2 px-3 text-sm" @input="fetchTemplateBreakdown" />
              </div>
            </template>
            <div class="w-20">
              <label class="mb-1 block text-xs text-gray-600">Margen %</label>
              <input v-model.number="templateItem.margin_pct" type="number" min="0" step="0.5" class="w-full rounded-lg border border-gray-300 py-2 px-3 text-sm" placeholder="—" @input="fetchTemplateBreakdown" />
            </div>
            <button
              type="button"
              :disabled="!templateItem.product_template || templateBreakdownLoading"
              class="rounded-lg bg-indigo-600 px-3 py-2 text-sm font-medium text-white hover:bg-indigo-700 disabled:opacity-50"
              @click="fetchTemplateBreakdown"
            >
              {{ templateBreakdownLoading ? "..." : "Calcular" }}
            </button>
          </div>
          <div v-if="templateBreakdown.cost_lines?.length" class="mt-3 rounded-lg bg-white p-3 text-sm shadow-sm">
            <p class="font-medium text-gray-700 mb-2">Desglose</p>
            <ul class="space-y-1">
              <li v-for="(line, i) in templateBreakdown.cost_lines" :key="i" class="flex justify-between">
                <span>{{ line.label }}</span>
                <span>{{ formatCurrency(line.line_total) }}</span>
              </li>
            </ul>
            <p class="mt-2 flex justify-between font-medium">
              <span>Total venta</span>
              <span>{{ formatCurrency(templateBreakdown.sale_total) }}</span>
            </p>
            </div>
          <button
            v-if="templateItem.product_template && templateBreakdown.sale_total > 0"
            type="button"
            class="mt-2 rounded-lg bg-green-600 px-3 py-2 text-sm font-medium text-white hover:bg-green-700"
            @click="addTemplateToCart"
          >
            Agregar plantilla al carrito
          </button>
        </div>

        <div class="mb-4">
          <label class="mb-2 block text-sm font-medium text-gray-700">Producto (catálogo)</label>
          <select
            v-model="newItem.product"
            class="w-full max-w-md rounded-lg border border-gray-300 py-2.5 px-4 text-base focus:border-indigo-500 focus:outline-none focus:ring-2 focus:ring-indigo-500"
            @change="onProductSelect"
          >
            <option value="">Seleccionar producto</option>
            <option v-for="p in catalog" :key="p.item_code" :value="p.item_code">
              {{ p.item_name }} ({{ p.product_type }})
            </option>
          </select>
        </div>
        <template v-if="selectedProduct">
          <!-- Fixed -->
          <div v-if="selectedProduct.product_type === 'Fixed'" class="grid grid-cols-2 gap-4 max-w-lg">
            <div>
              <label class="mb-1 block text-sm font-medium text-gray-700">Cantidad</label>
              <input v-model.number="newItem.qty" type="number" min="1" class="w-full rounded-lg border border-gray-300 py-2 px-3 text-sm" />
            </div>
            <div>
              <label class="mb-1 block text-sm font-medium text-gray-700">Precio unitario</label>
              <input v-model.number="newItem.unit_price" type="number" min="0" step="0.01" class="w-full rounded-lg border border-gray-300 py-2 px-3 text-sm" />
            </div>
          </div>
          <!-- Area -->
          <div v-if="selectedProduct.product_type === 'Area'" class="grid grid-cols-2 gap-4 max-w-2xl">
            <div>
              <label class="mb-1 block text-sm font-medium text-gray-700">Cantidad</label>
              <input v-model.number="newItem.qty" type="number" min="1" class="w-full rounded-lg border border-gray-300 py-2 px-3 text-sm" />
            </div>
            <div>
              <label class="mb-1 block text-sm font-medium text-gray-700">Ancho (mm)</label>
              <input v-model.number="newItem.width" type="number" min="0" class="w-full rounded-lg border border-gray-300 py-2 px-3 text-sm" />
            </div>
            <div>
              <label class="mb-1 block text-sm font-medium text-gray-700">Alto (mm)</label>
              <input v-model.number="newItem.height" type="number" min="0" class="w-full rounded-lg border border-gray-300 py-2 px-3 text-sm" />
            </div>
            <div>
              <label class="mb-1 block text-sm font-medium text-gray-700">Precio por m²</label>
              <input v-model.number="newItem.price_per_m2" type="number" min="0" step="0.01" class="w-full rounded-lg border border-gray-300 py-2 px-3 text-sm" />
            </div>
          </div>
          <!-- Recipe -->
          <div v-if="selectedProduct.product_type === 'Recipe'" class="space-y-4 max-w-2xl">
            <div class="grid grid-cols-2 gap-4">
              <div>
                <label class="mb-1 block text-sm font-medium text-gray-700">Cantidad</label>
                <input v-model.number="newItem.qty" type="number" min="1" class="w-full rounded-lg border border-gray-300 py-2 px-3 text-sm" />
              </div>
              <div>
                <label class="mb-1 block text-sm font-medium text-gray-700">Margen %</label>
                <input v-model.number="newItem.margin_pct" type="number" min="0" step="0.5" class="w-full rounded-lg border border-gray-300 py-2 px-3 text-sm" />
              </div>
              <div>
                <label class="mb-1 block text-sm font-medium text-gray-700">Ancho (mm)</label>
                <input v-model.number="newItem.width" type="number" min="0" class="w-full rounded-lg border border-gray-300 py-2 px-3 text-sm" />
              </div>
              <div>
                <label class="mb-1 block text-sm font-medium text-gray-700">Alto (mm)</label>
                <input v-model.number="newItem.height" type="number" min="0" class="w-full rounded-lg border border-gray-300 py-2 px-3 text-sm" />
              </div>
            </div>
            <div v-if="recipeBreakdown.cost_lines?.length" class="rounded-lg bg-gray-50 p-3 text-sm">
              <p class="font-medium text-gray-700 mb-2">Desglose costo</p>
              <ul class="space-y-1">
                <li v-for="(line, i) in recipeBreakdown.cost_lines" :key="i" class="flex justify-between">
                  <span>{{ line.description }}</span>
                  <span>{{ formatCurrency(line.amount) }}</span>
                </li>
              </ul>
              <p class="mt-2 flex justify-between font-medium">
                <span>Total venta</span>
                <span>{{ formatCurrency(recipeBreakdown.sale_total) }}</span>
              </p>
            </div>
          </div>
        </template>
        <div class="mt-4">
          <button
            type="button"
            :disabled="!canAddItem"
            class="rounded-lg bg-indigo-600 px-4 py-2.5 text-sm font-medium text-white hover:bg-indigo-700 disabled:opacity-50"
            @click="addToCart"
          >
            Agregar al carrito
          </button>
        </div>
      </template>
    </div>

    <!-- Carrito y totales -->
    <div class="mb-6 rounded-xl border border-gray-200 bg-white p-6 shadow-sm">
      <h2 class="mb-4 text-base font-semibold text-gray-900">Carrito ({{ cart.length }} ítems)</h2>
      <div v-if="cart.length === 0" class="py-6 text-center text-sm text-gray-500">No hay ítems. Agregá productos arriba.</div>
      <template v-else>
        <table class="min-w-full text-sm">
          <thead class="border-b border-gray-200 text-left text-gray-600">
            <tr>
              <th class="pb-2 pr-4">Producto / Tipo</th>
              <th class="pb-2 pr-4">Cant.</th>
              <th class="pb-2 pr-4">Total</th>
              <th class="w-16"></th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="(item, idx) in cart" :key="idx" class="border-b border-gray-100">
              <td class="py-2 pr-4">{{ item.item_name }}{{ item.product_template ? " (plantilla)" : "" }} ({{ item.product_type }})</td>
              <td class="py-2 pr-4">{{ item.qty }}</td>
              <td class="py-2 pr-4">{{ formatCurrency(item.sale_total) }}</td>
              <td class="py-2">
                <button type="button" class="text-red-600 hover:text-red-800" @click="removeFromCart(idx)">Quitar</button>
              </td>
            </tr>
          </tbody>
        </table>
        <div class="mt-4 flex flex-wrap items-center gap-4 border-t border-gray-200 pt-4">
          <p class="text-base font-semibold text-gray-900">Total venta: {{ formatCurrency(totals.sale_total) }}</p>
          <p v-if="totals.cost_total > 0" class="text-sm text-gray-600">Costo total: {{ formatCurrency(totals.cost_total) }} · Margen: {{ totals.margin_pct }}%</p>
        </div>
      </template>
    </div>

    <!-- Acciones -->
    <div class="flex flex-wrap gap-3">
      <button
        type="button"
        :disabled="!canSaveQuote || saving"
        class="rounded-xl bg-indigo-600 px-5 py-2.5 text-base font-semibold text-white hover:bg-indigo-700 disabled:opacity-50"
        @click="saveQuote"
      >
        {{ saving ? "Guardando..." : "Guardar Cotización" }}
      </button>
      <button
        type="button"
        :disabled="!canConvert || submitting"
        class="rounded-xl bg-green-600 px-5 py-2.5 text-base font-semibold text-white hover:bg-green-700 disabled:opacity-50"
        @click="convertToOrder"
      >
        {{ submitting ? "Creando orden..." : "Convertir a Orden" }}
      </button>
      <button type="button" class="rounded-lg border border-gray-300 bg-white px-4 py-2.5 text-sm font-medium text-gray-700 hover:bg-gray-50" @click="router.push('/dashboard')">
        Volver al Dashboard
      </button>
    </div>
    <p v-if="submitError" class="mt-4 text-sm text-red-600">{{ submitError }}</p>

    <!-- Modal Nuevo Cliente -->
    <Teleport to="body">
      <div v-if="showNewCustomerModal" class="fixed inset-0 z-50 flex items-center justify-center bg-black/50 p-4" @click.self="closeNewCustomerModal">
        <div class="w-full max-w-md rounded-xl border border-gray-200 bg-white p-6 shadow-xl">
          <h2 class="mb-4 text-lg font-semibold text-gray-900">Crear Cliente Rápido</h2>
          <form @submit.prevent="createNewCustomer">
            <div class="mb-4">
              <label class="mb-1 block text-sm font-medium text-gray-700">Razón Social / Nombre *</label>
              <input v-model="newCustomerName" type="text" required placeholder="Ej: Gráfica López S.A." class="w-full rounded-lg border border-gray-300 py-2.5 px-4 text-sm focus:border-indigo-500 focus:outline-none focus:ring-2 focus:ring-indigo-500" />
            </div>
            <div class="flex justify-end gap-3">
              <button type="button" class="rounded-lg border border-gray-300 bg-white px-4 py-2.5 text-sm font-medium text-gray-700 hover:bg-gray-50" @click="closeNewCustomerModal">Cancelar</button>
              <button type="submit" :disabled="isCreatingCustomer" class="rounded-lg bg-indigo-600 px-4 py-2.5 text-sm font-medium text-white hover:bg-indigo-700 disabled:opacity-50">Guardar</button>
            </div>
          </form>
        </div>
      </div>
    </Teleport>

    <!-- Toast -->
    <Teleport to="body">
      <div v-if="toastVisible" class="fixed bottom-6 left-1/2 z-[60] -translate-x-1/2 rounded-lg bg-indigo-600 px-4 py-2.5 text-sm font-medium text-white shadow-lg" role="status">
        {{ toastMessage }}
      </div>
    </Teleport>
  </div>
</template>

<script setup>
import { ref, reactive, computed, watch, onMounted } from "vue";
import { useRouter } from "vue-router";
import { Loader2, UserPlus } from "lucide-vue-next";
import { call } from "@/api/frappe";

const router = useRouter();

function defaultDeliveryDate() {
  const d = new Date();
  d.setDate(d.getDate() + 3);
  return d.toISOString().slice(0, 10);
}

const deliveryDate = ref(defaultDeliveryDate());
const customerQuery = ref("");
const selectedCustomer = ref(null);
const customerOptions = ref([]);
const customerOpen = ref(false);
const showNewCustomerModal = ref(false);
const newCustomerName = ref("");
const isCreatingCustomer = ref(false);
const toastVisible = ref(false);
const toastMessage = ref("");
let customerDebounce = null;
let customerAbortController = null;

const loadingCatalog = ref(true);
const catalog = ref([]);
const cart = ref([]);
const savedQuoteId = ref(null);
const saving = ref(false);
const submitting = ref(false);
const submitError = ref("");

const productTemplates = ref([]);
const templateItem = reactive({
  product_template: "",
  qty: 1,
  width: 0,
  height: 0,
  margin_pct: null,
});
const selectedTemplateMeta = ref(null);
const templateBreakdown = ref({});
const templateBreakdownLoading = ref(false);
let templateBreakdownDebounce = null;

const newItem = reactive({
  product: "",
  product_type: "Fixed",
  qty: 1,
  width: 0,
  height: 0,
  unit_price: 0,
  price_per_m2: 0,
  margin_pct: 0,
});
const recipeBreakdown = ref({});
let recipeDebounce = null;

const selectedProduct = computed(() => {
  if (!newItem.product) return null;
  return catalog.value.find((p) => p.item_code === newItem.product);
});

const totals = computed(() => {
  let cost_total = 0;
  let sale_total = 0;
  for (const item of cart.value) {
    cost_total += item.cost_total || 0;
    sale_total += item.sale_total || 0;
  }
  let margin_pct = 0;
  if (cost_total > 0 && sale_total > 0) margin_pct = Math.round(((sale_total - cost_total) / cost_total) * 1000) / 10;
  return { cost_total, sale_total, margin_pct };
});

const canAddItem = computed(() => {
  if (!selectedProduct.value || (newItem.qty || 0) <= 0) return false;
  if (selectedProduct.value.product_type === "Fixed") return (newItem.unit_price || 0) >= 0;
  if (selectedProduct.value.product_type === "Area") return (newItem.price_per_m2 || 0) >= 0 && (newItem.width || 0) > 0 && (newItem.height || 0) > 0;
  return true;
});

const canSaveQuote = computed(() => selectedCustomer.value && cart.value.length > 0 && deliveryDate.value);
const canConvert = computed(() => selectedCustomer.value && cart.value.length > 0 && deliveryDate.value);

function formatCurrency(v) {
  if (v == null || v === "") return "—";
  return new Intl.NumberFormat("es-AR", { style: "currency", currency: "ARS", minimumFractionDigits: 0, maximumFractionDigits: 2 }).format(v);
}

function onCustomerInput() {
  clearTimeout(customerDebounce);
  customerDebounce = setTimeout(async () => {
    const txt = customerQuery.value.trim();
    if (txt.length < 2) {
      customerOptions.value = [];
      return;
    }
    customerAbortController?.abort();
    customerAbortController = new AbortController();
    try {
      const res = await call("mathipe_ui.api.search_customers", { txt }, { signal: customerAbortController.signal });
      customerOptions.value = res?.message ?? res ?? [];
    } catch (e) {
      if (e.name === "AbortError") return;
      customerOptions.value = [];
    }
  }, 300);
}

function selectCustomer(c) {
  selectedCustomer.value = c;
  customerQuery.value = c.customer_name || c.name;
  customerOptions.value = [];
  customerOpen.value = false;
}

function openNewCustomerModal() {
  newCustomerName.value = "";
  showNewCustomerModal.value = true;
  customerOpen.value = false;
}
function closeNewCustomerModal() {
  showNewCustomerModal.value = false;
}

function showToast(message) {
  toastMessage.value = message;
  toastVisible.value = true;
  setTimeout(() => {
    toastVisible.value = false;
  }, 3500);
}

async function createNewCustomer() {
  const name = newCustomerName.value?.trim();
  if (!name || isCreatingCustomer.value) return;
  isCreatingCustomer.value = true;
  try {
    const res = await call("mathipe_ui.api.create_simple_customer", { customer_name: name });
    const data = res?.message ?? res ?? {};
    if (data.ok && data.name) {
      selectedCustomer.value = { name: data.name, customer_name: name };
      customerQuery.value = name;
      closeNewCustomerModal();
      showToast("Cliente creado y seleccionado.");
    } else {
      showToast(data.error || "Error al crear el cliente.");
    }
  } catch (e) {
    showToast(e.message || "Error al crear el cliente.");
  } finally {
    isCreatingCustomer.value = false;
  }
}

function onProductSelect() {
  newItem.qty = 1;
  newItem.width = 0;
  newItem.height = 0;
  newItem.unit_price = 0;
  newItem.price_per_m2 = 0;
  newItem.margin_pct = selectedProduct.value?.product_type === "Recipe" ? 30 : 0;
  recipeBreakdown.value = {};
  fetchRecipeBreakdown();
}

function onTemplateSelect() {
  templateItem.qty = 1;
  templateItem.width = 0;
  templateItem.height = 0;
  templateItem.margin_pct = null;
  templateBreakdown.value = {};
  selectedTemplateMeta.value = null;
  if (!templateItem.product_template) return;
  const t = productTemplates.value.find((p) => p.name === templateItem.product_template);
  selectedTemplateMeta.value = t ? { allow_qty: t.allow_qty !== false, allow_dimensions: !!t.allow_dimensions } : null;
  fetchTemplateBreakdown();
}

async function fetchTemplateBreakdown() {
  clearTimeout(templateBreakdownDebounce);
  templateBreakdownDebounce = setTimeout(async () => {
    if (!templateItem.product_template || (templateItem.qty || 0) <= 0) {
      templateBreakdown.value = {};
      return;
    }
    templateBreakdownLoading.value = true;
    try {
      const payload = {
        product_template: templateItem.product_template,
        qty: templateItem.qty,
        width: templateItem.width || 0,
        height: templateItem.height || 0,
      };
      if (templateItem.margin_pct != null && templateItem.margin_pct !== "") payload.margin_pct = templateItem.margin_pct;
      const res = await call("mathipe_ui.api.calculate_quote_item_from_template", { payload });
      templateBreakdown.value = res?.message ?? res ?? {};
    } catch (e) {
      templateBreakdown.value = {};
    } finally {
      templateBreakdownLoading.value = false;
    }
  }, 200);
}

function addTemplateToCart() {
  if (!templateItem.product_template || !templateBreakdown.value.sale_total) return;
  const t = productTemplates.value.find((p) => p.name === templateItem.product_template);
  const name = t?.product_name || templateItem.product_template;
  cart.value.push({
    product_type: "Fixed",
    product: null,
    item_name: name,
    product_template: templateItem.product_template,
    qty: templateItem.qty,
    width: templateItem.width,
    height: templateItem.height,
    unit_price: templateBreakdown.value.unit_price ?? 0,
    sale_total: templateBreakdown.value.sale_total ?? 0,
    cost_total: templateBreakdown.value.cost_total ?? 0,
    margin_pct: templateBreakdown.value.margin_pct ?? 0,
    area_total: templateBreakdown.value.area_total ?? 0,
    description: "",
    breakdown_json: templateBreakdown.value.breakdown_json || "",
    margin_pct_override: templateItem.margin_pct != null && templateItem.margin_pct !== "" ? templateItem.margin_pct : undefined,
  });
  showToast("Ítem por plantilla agregado al carrito.");
}

function fetchRecipeBreakdown() {
  clearTimeout(recipeDebounce);
  recipeDebounce = setTimeout(async () => {
    if (!selectedProduct.value || selectedProduct.value.product_type !== "Recipe" || (newItem.qty || 0) <= 0) {
      recipeBreakdown.value = {};
      return;
    }
    try {
      const res = await call("mathipe_ui.api.calculate_quote_item", {
        product_type: "Recipe",
        product: newItem.product,
        qty: newItem.qty,
        width: newItem.width,
        height: newItem.height,
        margin_pct: newItem.margin_pct,
      });
      recipeBreakdown.value = res?.message ?? res ?? {};
    } catch (e) {
      recipeBreakdown.value = {};
    }
  }, 300);
}

watch(
  () => [newItem.qty, newItem.width, newItem.height, newItem.margin_pct],
  () => {
    if (selectedProduct.value?.product_type === "Recipe") fetchRecipeBreakdown();
  },
  { deep: true }
);

async function addToCart() {
  if (!selectedProduct.value || !canAddItem.value) return;
  const p = selectedProduct.value;
  let calc = {};
  try {
    const res = await call("mathipe_ui.api.calculate_quote_item", {
      product_type: p.product_type,
      product: newItem.product,
      qty: newItem.qty,
      width: newItem.width,
      height: newItem.height,
      unit_price: newItem.unit_price,
      price_per_m2: newItem.price_per_m2,
      margin_pct: newItem.margin_pct,
    });
    calc = res?.message ?? res ?? {};
  } catch (e) {
    showToast("Error al calcular el ítem.");
    return;
  }
  cart.value.push({
    product_type: p.product_type,
    product: newItem.product,
    item_name: p.item_name,
    qty: newItem.qty,
    width: newItem.width,
    height: newItem.height,
    unit_price: calc.computed_fields?.unit_price ?? newItem.unit_price,
    price_per_m2: p.product_type === "Area" ? (newItem.price_per_m2 ?? 0) : undefined,
    sale_total: calc.sale_total ?? 0,
    cost_total: calc.cost_total ?? 0,
    margin_pct: calc.margin_pct ?? 0,
    area_total: calc.area_total ?? 0,
    description: "",
  });
  showToast("Ítem agregado al carrito.");
}

function removeFromCart(idx) {
  cart.value.splice(idx, 1);
}

function cartItemToPayload(it) {
  if (it.product_template) {
    return {
      product_template: it.product_template,
      qty: it.qty,
      width: it.width ?? 0,
      height: it.height ?? 0,
      unit_price: it.unit_price,
      sale_total: it.sale_total,
      cost_total: it.cost_total,
      area_total: it.area_total,
      margin_pct: it.margin_pct,
      description: it.description,
      breakdown_json: it.breakdown_json,
      margin_pct_override: it.margin_pct_override,
    };
  }
  return {
    product_type: it.product_type,
    product: it.product,
    qty: it.qty,
    width: it.width,
    height: it.height,
    unit_price: it.unit_price,
    price_per_m2: it.product_type === "Area" ? (it.price_per_m2 ?? it.unit_price) : undefined,
    margin_pct: it.margin_pct,
    description: it.description,
  };
}

async function saveQuote() {
  if (!canSaveQuote.value || saving.value) return;
  submitError.value = "";
  saving.value = true;
  try {
    const items = cart.value.map(cartItemToPayload);
    const res = await call("mathipe_ui.api.create_quote", {
      customer: selectedCustomer.value.name,
      delivery_date: deliveryDate.value,
      items,
      notes: "",
    });
    const data = res?.message ?? res ?? {};
    if (data.name) {
      savedQuoteId.value = data.name;
      showToast("Cotización guardada: " + data.name);
    } else {
      showToast("Error al guardar.");
    }
  } catch (e) {
    submitError.value = e.message || "Error al guardar cotización.";
    showToast(submitError.value);
  } finally {
    saving.value = false;
  }
}

async function convertToOrder() {
  if (!canConvert.value || submitting.value) return;
  submitError.value = "";
  submitting.value = true;
  try {
    let qid = savedQuoteId.value;
    if (!qid && cart.value.length > 0) {
      const items = cart.value.map(cartItemToPayload);
      const createRes = await call("mathipe_ui.api.create_quote", {
        customer: selectedCustomer.value.name,
        delivery_date: deliveryDate.value,
        items,
        notes: "",
      });
      const created = createRes?.message ?? createRes ?? {};
      qid = created.name;
      if (!qid) throw new Error("No se pudo crear la cotización");
    }
    const res = await call("mathipe_ui.api.convert_quote_to_sales_order", { quote_id: qid });
    const data = res?.message ?? res ?? {};
    if (data.name) {
      showToast(data.already_converted ? "Orden ya existente: " + data.name : "Orden creada: " + data.name);
      router.push("/orden/" + data.name);
      return;
    }
    throw new Error(data.message || "No se devolvió el ID de la orden");
  } catch (e) {
    submitError.value = e.message || "Error al convertir a orden.";
    showToast(submitError.value);
  } finally {
    submitting.value = false;
  }
}

onMounted(async () => {
  loadingCatalog.value = true;
  try {
    const [catRes, tplRes] = await Promise.all([
      call("mathipe_ui.api.get_quote_products_catalog", {}),
      call("mathipe_ui.api.list_product_templates", {}),
    ]);
    const data = catRes?.message ?? catRes ?? [];
    catalog.value = Array.isArray(data) ? data : [];
    const tpl = tplRes?.message ?? tplRes ?? [];
    productTemplates.value = Array.isArray(tpl) ? tpl : [];
  } catch (e) {
    console.error("Cotizador: error catálogo", e);
    catalog.value = [];
    productTemplates.value = [];
  } finally {
    loadingCatalog.value = false;
  }
  document.addEventListener("click", () => {
    customerOpen.value = false;
  });
});
</script>

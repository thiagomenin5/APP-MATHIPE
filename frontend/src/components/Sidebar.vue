<template>
  <aside class="fixed left-0 top-0 z-40 flex h-screen w-64 flex-col bg-slate-900">
    <!-- Cabecera: branding por site -->
    <div class="flex h-14 shrink-0 items-center gap-2 border-b border-slate-700 px-4">
      <div v-if="branding.logo_url" class="flex h-9 w-9 shrink-0 items-center justify-center overflow-hidden rounded-lg bg-white">
        <img :src="branding.logo_url" alt="" class="h-full w-full object-contain" />
      </div>
      <div v-else class="flex h-9 w-9 shrink-0 items-center justify-center rounded-lg text-white" :style="branding.primary_color ? { backgroundColor: branding.primary_color } : { backgroundColor: '#4f46e5' }">
        <Printer class="h-5 w-5" />
      </div>
      <span class="truncate text-base font-semibold text-white">{{ branding.display_name }}</span>
    </div>

    <nav class="flex-1 overflow-y-auto p-3">
      <!-- Favoritos: link directo sin acordeón -->
      <div class="mb-2">
        <router-link
          v-for="item in favoritos"
          :key="item.to"
          :to="item.to"
          class="flex cursor-pointer items-center gap-3 rounded-lg px-3 py-2.5 text-sm font-medium transition-colors hover:bg-slate-800 hover:text-white"
          :class="isActive(item.to) ? 'bg-slate-700 text-white' : 'text-slate-300'"
        >
          <component :is="item.icon" class="h-5 w-5 shrink-0" />
          {{ item.label }}
        </router-link>
      </div>

      <!-- Secciones tipo acordeón -->
      <div v-for="section in secciones" :key="section.name" class="mb-1">
        <!-- Header del grupo (clicable) -->
        <button
          type="button"
          class="flex w-full cursor-pointer items-center justify-between rounded-lg px-3 py-2.5 text-left text-sm font-medium transition-colors hover:bg-slate-800 text-slate-300 hover:text-white"
          :class="{ 'bg-slate-800/50': openSections[section.name] }"
          @click="toggleSection(section.name)"
        >
          <span class="truncate">{{ section.titulo }}</span>
          <ChevronDown
            class="h-4 w-4 shrink-0 transition-transform duration-200"
            :class="{ 'rotate-180': openSections[section.name] }"
          />
        </button>

        <!-- Submenú (solo si está abierto) -->
        <transition
          enter-active-class="transition-all duration-200 ease-out"
          enter-from-class="max-h-0 opacity-0"
          enter-to-class="max-h-[500px] opacity-100"
          leave-active-class="transition-all duration-150 ease-in"
          leave-from-class="max-h-[500px] opacity-100"
          leave-to-class="max-h-0 opacity-0"
        >
          <div
            v-show="openSections[section.name]"
            class="overflow-hidden rounded-b-lg bg-slate-950/60"
          >
            <div class="border-l-2 border-slate-700/80 pl-1 py-1">
              <router-link
                v-for="item in visibleSectionItems(section)"
                :key="item.to"
                :to="item.to"
                class="flex cursor-pointer items-center gap-3 rounded-lg px-3 py-2 text-sm font-medium transition-colors hover:bg-slate-800 hover:text-white"
                :class="isActive(item.to) ? 'bg-slate-700 text-white' : 'text-slate-300'"
              >
                <component :is="item.icon" class="h-4 w-4 shrink-0" />
                <span class="flex-1 truncate">{{ item.label }}</span>
                <Lock v-if="item.lock" class="h-3.5 w-3.5 shrink-0 text-slate-500" />
              </router-link>
            </div>
          </div>
        </transition>
      </div>
    </nav>
  </aside>
</template>

<script setup>
import { ref, watch, onMounted } from "vue";
import { useRoute } from "vue-router";
import { getBranding, call } from "@/api/frappe";
import {
  Printer,
  LayoutDashboard,
  FolderKanban,
  FileSearch,
  ShoppingBag,
  Users,
  Heart,
  ListOrdered,
  LayoutGrid,
  ShoppingCart,
  Package,
  CheckSquare,
  CalendarDays,
  ListTodo,
  TrendingUp,
  Store,
  CreditCard,
  Banknote,
  BookOpen,
  Building2,
  User,
  Tag,
  Truck,
  Coins,
  Settings,
  Lock,
  ChevronDown,
  BarChart2,
  PieChart,
  AlertTriangle,
  Cog,
  Wrench,
  Route,
  FileText,
} from "lucide-vue-next";

const route = useRoute();

const branding = ref({ display_name: "APP Mathipe", logo_url: null, primary_color: null });
const subscription = ref({ plan: "Internal", status: "Active", enabled_modules: [] });

onMounted(async () => {
  try {
    const b = await getBranding();
    branding.value = b;
  } catch (_) {}
  try {
    const res = await call("mathipe_ui.api.get_subscription_context");
    const s = res?.message ?? res;
    subscription.value = s && typeof s === "object" ? s : { plan: "Internal", status: "Active", enabled_modules: [] };
  } catch (_) {}
});

function moduleEnabled(key) {
  const mods = subscription.value.enabled_modules || [];
  if (subscription.value.plan === "Internal") return true;
  if ((subscription.value.status || "Active") !== "Active") return false;
  if (mods.length === 0) return ["Pro", "Enterprise"].includes(subscription.value.plan);
  const k = key.toLowerCase();
  return mods.some((m) => (m || "").toLowerCase() === k);
}

function visibleSectionItems(section) {
  const items = section.items || [];
  return items.filter((item) => {
    if (!item.feature) return true;
    return moduleEnabled(item.feature);
  });
}

const favoritos = [
  { to: "/dashboard", label: "Dashboard", icon: LayoutDashboard },
];

const secciones = [
  {
    name: "comercial",
    titulo: "📈 Comercial",
    items: [
      { to: "/comercial/proyectos", label: "Proyectos", icon: FolderKanban },
      { to: "/comercial/consultas", label: "Consultas", icon: FileSearch },
      { to: "/comercial/ecommerce", label: "E-commerce", icon: ShoppingBag },
      { to: "/comercial/clientes", label: "Clientes", icon: Users },
      { to: "/comercial/satisfaccion", label: "Satisfacción", icon: Heart, lock: true },
    ],
  },
  {
    name: "operaciones",
    titulo: "📋 Operaciones",
    items: [
      { to: "/operaciones/ordenes", label: "Orden de trabajo", icon: ListOrdered },
      { to: "/operaciones/tablero", label: "Tablero", icon: LayoutGrid },
      { to: "/operaciones/sector/printing", label: "Sector Impresión", icon: LayoutGrid },
      { to: "/operaciones/sector/finishing", label: "Sector Terminación", icon: LayoutGrid },
      { to: "/operaciones/sector/cutting", label: "Sector Guillotina", icon: LayoutGrid },
      { to: "/operaciones/sector/dispatch", label: "Sector Despacho", icon: LayoutGrid },
      { to: "/operaciones/tercerizacion", label: "Tercerización", icon: Package },
      { to: "/operaciones/compras", label: "Orden de compra", icon: ShoppingCart },
      { to: "/operaciones/inventario", label: "Inventario", icon: Package },
      { to: "/operaciones/despacho", label: "Despacho", icon: Package },
      { to: "/operaciones/visto-bueno", label: "Visto bueno", icon: CheckSquare },
    ],
  },
  {
    name: "calendario",
    titulo: "📅 Calendario",
    items: [
      { to: "/calendario/agendamiento", label: "Agendamiento", icon: CalendarDays },
      { to: "/calendario/tareas", label: "Mis Tareas", icon: ListTodo },
    ],
  },
  {
    name: "admin",
    titulo: "💰 Administración",
    items: [
      { to: "/admin/ventas", label: "Ventas", icon: TrendingUp },
      { to: "/admin/pos", label: "Punto de Venta", icon: Store },
      { to: "/admin/compras", label: "Compras", icon: ShoppingCart },
      { to: "/admin/pagos", label: "Pagos", icon: CreditCard },
      { to: "/admin/cobros", label: "Cobros", icon: Banknote },
      { to: "/admin/cuentas", label: "Cuentas", icon: BookOpen },
      { to: "/admin/finanzas", label: "Finanzas", icon: BarChart2, feature: "finanzas" },
      { to: "/admin/alertas", label: "Alertas", icon: AlertTriangle, feature: "alertas" },
      { to: "/admin/analitica", label: "Analítica", icon: PieChart, feature: "analitica" },
    ],
  },
  {
    name: "empresa",
    titulo: "🏢 Mi empresa",
    items: [
      { to: "/empresa/configuracion", label: "Configuración", icon: Settings },
      { to: "/empresa/maquinas", label: "Máquinas", icon: Cog },
      { to: "/empresa/materiales", label: "Materiales", icon: Package },
      { to: "/empresa/operaciones", label: "Operaciones", icon: Wrench },
      { to: "/empresa/rutas", label: "Rutas", icon: Route },
      { to: "/empresa/plantillas-producto", label: "Plantillas de producto", icon: FileText },
      { to: "/empresa/perfil", label: "Mi perfil", icon: User },
      { to: "/empresa/usuarios", label: "Usuarios", icon: Users },
      { to: "/empresa/productos", label: "Productos / Servicios", icon: Package },
      { to: "/empresa/precios", label: "Listas de precios", icon: Tag },
      { to: "/empresa/proveedores", label: "Proveedores", icon: Truck },
      { to: "/empresa/monedas", label: "Monedas", icon: Coins },
      { to: "/empresa/configuraciones", label: "Configuraciones", icon: Settings },
    ],
  },
];

// Estado: qué secciones están abiertas. Por defecto todas cerradas.
const sectionNames = secciones.map((s) => s.name);
const openSections = ref(
  Object.fromEntries(sectionNames.map((name) => [name, false]))
);

/** Devuelve el name de la sección que contiene esta ruta, o null. */
function getSectionForPath(path) {
  if (!path || path === "/") return null;
  const segment = path.split("/").filter(Boolean)[0];
  if (sectionNames.includes(segment)) return segment;
  // /orden/:id no tiene sección en el sidebar; no abrimos nada por eso
  return null;
}

function toggleSection(name) {
  openSections.value[name] = !openSections.value[name];
}

/** Abre la sección que contiene la ruta actual (y deja el resto como esté). */
function ensureSectionOpenForPath(path) {
  const name = getSectionForPath(path);
  if (name && !openSections.value[name]) {
    openSections.value = { ...openSections.value, [name]: true };
  }
}

onMounted(() => {
  ensureSectionOpenForPath(route.path);
});

watch(
  () => route.path,
  (newPath) => {
    ensureSectionOpenForPath(newPath);
  }
);

function isActive(to) {
  if (to === "/dashboard") return route.path === "/dashboard";
  return route.path.startsWith(to);
}
</script>

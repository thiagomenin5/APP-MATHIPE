import { createRouter, createWebHistory } from "vue-router";
import { getSession, call } from "@/api/frappe";
import MainLayout from "@/layouts/MainLayout.vue";

const EnConstruccion = () => import("@/views/EnConstruccion.vue");
const PlanNoDisponible = () => import("@/views/PlanNoDisponible.vue");

const router = createRouter({
  history: createWebHistory("/"),
  routes: [
    { path: "/", redirect: "/dashboard" },
    { path: "/login", name: "Login", component: () => import("@/views/Login.vue"), meta: { public: true } },
    {
      path: "/",
      component: MainLayout,
      children: [
        { path: "dashboard", name: "Dashboard", component: () => import("@/views/DashboardOperativo.vue") },
        // Comercial
        { path: "comercial/proyectos", name: "ComercialProyectos", component: EnConstruccion, meta: { label: "Proyectos" } },
        { path: "comercial/consultas", name: "Cotizador", component: () => import("@/views/Cotizador.vue"), meta: { label: "Consultas" } },
        { path: "comercial/ecommerce", name: "ComercialEcommerce", component: EnConstruccion, meta: { label: "E-commerce" } },
        { path: "comercial/clientes", name: "ComercialClientes", component: () => import("@/views/Clientes.vue"), meta: { label: "Clientes" } },
        { path: "comercial/satisfaccion", name: "ComercialSatisfaccion", component: EnConstruccion, meta: { label: "Satisfacción" } },
        // Operaciones
        { path: "operaciones/ordenes", name: "OrdenesList", component: () => import("@/views/OrdenesList.vue"), meta: { label: "Orden de trabajo" } },
        { path: "operaciones/tablero", name: "Produccion", component: () => import("@/views/Produccion.vue"), meta: { label: "Tablero" } },
        { path: "operaciones/tercerizacion", name: "Tercerizacion", component: () => import("@/views/OutsourcingBoard.vue"), meta: { label: "Tercerización" } },
        { path: "operaciones/sector/:sectorKey", name: "SectorBoard", component: () => import("@/views/SectorBoard.vue"), meta: { label: "Tablero por sector" } },
        { path: "operaciones/compras", name: "OperacionesCompras", component: EnConstruccion, meta: { label: "Orden de compra" } },
        { path: "operaciones/inventario", name: "OperacionesInventario", component: () => import("@/views/Inventario.vue"), meta: { label: "Inventario" } },
        { path: "operaciones/despacho", name: "DispatchBoard", component: () => import("@/views/DispatchBoard.vue"), meta: { label: "Despacho" } },
        { path: "operaciones/visto-bueno", name: "OperacionesVistoBueno", component: () => import("@/views/VistoBueno.vue"), meta: { label: "Visto bueno" } },
        // Calendario
        { path: "calendario/agendamiento", name: "CalendarioAgendamiento", component: EnConstruccion, meta: { label: "Agendamiento" } },
        { path: "calendario/tareas", name: "CalendarioTareas", component: EnConstruccion, meta: { label: "Mis Tareas" } },
        // Administración
        { path: "admin/ventas", name: "AdminVentas", component: EnConstruccion, meta: { label: "Ventas" } },
        { path: "admin/pos", name: "AdminPOS", component: EnConstruccion, meta: { label: "Punto de Venta" } },
        { path: "admin/compras", name: "AdminCompras", component: EnConstruccion, meta: { label: "Compras" } },
        { path: "admin/pagos", name: "AdminPagos", component: EnConstruccion, meta: { label: "Pagos" } },
        { path: "admin/cobros", name: "AdminCobros", component: () => import("@/views/Cobros.vue"), meta: { label: "Cobros" } },
        { path: "admin/cuentas", name: "AdminCuentas", component: EnConstruccion, meta: { label: "Cuentas" } },
        { path: "admin/finanzas", name: "AdminFinanzas", component: () => import("@/views/Finanzas.vue"), meta: { label: "Finanzas", requiresFeature: "finanzas", planMessage: "Tu plan no incluye Finanzas." } },
        { path: "admin/alertas", name: "AdminAlertas", component: () => import("@/views/Alertas.vue"), meta: { label: "Alertas", requiresFeature: "alertas", planMessage: "Tu plan no incluye Alertas." } },
        { path: "admin/analitica", name: "AdminAnalitica", component: () => import("@/views/Analitica.vue"), meta: { label: "Analítica", requiresFeature: "analitica", planMessage: "Tu plan no incluye Analítica." } },
        { path: "plan-no-disponible", name: "PlanNoDisponible", component: PlanNoDisponible, meta: { label: "No disponible" } },
        // Mi empresa
        { path: "empresa/configuracion", name: "CompanySetup", component: () => import("@/views/CompanySetup.vue"), meta: { label: "Configuración" } },
        { path: "empresa/maquinas", name: "Machines", component: () => import("@/views/Machines.vue"), meta: { label: "Máquinas" } },
        { path: "empresa/materiales", name: "Materials", component: () => import("@/views/Materials.vue"), meta: { label: "Materiales" } },
        { path: "empresa/operaciones", name: "Operations", component: () => import("@/views/Operations.vue"), meta: { label: "Operaciones" } },
        { path: "empresa/rutas", name: "Routes", component: () => import("@/views/Routes.vue"), meta: { label: "Rutas" } },
        { path: "empresa/plantillas-producto", name: "ProductTemplates", component: () => import("@/views/ProductTemplates.vue"), meta: { label: "Plantillas de producto" } },
        { path: "empresa/perfil", name: "EmpresaPerfil", component: EnConstruccion, meta: { label: "Mi perfil" } },
        { path: "empresa/usuarios", name: "EmpresaUsuarios", component: EnConstruccion, meta: { label: "Usuarios" } },
        { path: "empresa/productos", name: "EmpresaProductos", component: () => import("@/views/Productos.vue"), meta: { label: "Productos / Servicios" } },
        { path: "empresa/precios", name: "EmpresaPrecios", component: EnConstruccion, meta: { label: "Listas de precios" } },
        { path: "empresa/proveedores", name: "EmpresaProveedores", component: EnConstruccion, meta: { label: "Proveedores" } },
        { path: "empresa/monedas", name: "EmpresaMonedas", component: EnConstruccion, meta: { label: "Monedas" } },
        { path: "empresa/configuraciones", name: "EmpresaConfiguraciones", component: EnConstruccion, meta: { label: "Configuraciones" } },
        // Detalle de orden (ruta existente)
        { path: "orden/:id", name: "OrderDetail", component: () => import("@/views/OrderDetail.vue") },
      ],
    },
    // Vista impresión OT — fuera del MainLayout, pública
    { path: "/print/ot/:id", name: "OTPrint", component: () => import("@/views/OTPrint.vue"), meta: { public: true } },
  ],
});

router.beforeEach(async (to, _from, next) => {
  if (to.meta.public) return next();
  const user = await getSession();
  if (!user) return next({ name: "Login", query: { redirect: to.fullPath } });
  if (to.meta.requiresFeature) {
    try {
      const res = await call("mathipe_ui.api.get_feature_flags");
      const flags = res?.message ?? res;
      const enabled = flags && flags[to.meta.requiresFeature];
      if (!enabled) {
        return next({
          name: "PlanNoDisponible",
          query: { feature: to.meta.requiresFeature, planMessage: to.meta.planMessage || "" },
          replace: true,
        });
      }
    } catch (_) {
      return next({
        name: "PlanNoDisponible",
        query: { feature: to.meta.requiresFeature, planMessage: to.meta.planMessage || "" },
        replace: true,
      });
    }
  }
  next();
});

export default router;

# Resumen detallado del proyecto Mathipe UI

**Para uso interno y para pasar contexto a una IA.**

---

## 1. Qué es el proyecto

- **Nombre:** Mathipe UI (App Mathipe).
- **Propósito:** SPA (Single Page Application) para la imprenta Gráfica Mathipe. Interfaz tipo Twist Print: flujo de ventas → diseño/preimpresión → producción → cobros, con mínima dependencia del Frappe Desk.
- **URL de entrada:** `https://app.graficamathipe.com.ar/` (o la URL del site) → login → SPA.
- **Stack:**
  - **Frontend:** Vue 3, Vite, Vue Router, Tailwind CSS, lucide-vue-next (iconos). Build → archivos estáticos en `mathipe_ui/public/spa/`.
  - **Backend:** Frappe/ERPNext. APIs vía `frappe.call()` (RPC). DocTypes estándar: Sales Order, Customer, Payment Entry, etc.; custom: Mathipe Print Product, Mathipe Print Material.
- **Autenticación:** Sesión Frappe; si no hay sesión el router redirige a `/login`. Tras login, redirect a `/dashboard` (no al Desk).

---

## 2. Mapa de rutas y estado de cada módulo

| Ruta | Vista (componente) | Estado | Descripción breve |
|------|-------------------|--------|--------------------|
| `/` | redirect | ✅ | Redirige a `/dashboard`. |
| `/login` | Login.vue | ✅ | Formulario de login; post-login → `/dashboard`. |
| `/dashboard` | Dashboard.vue | ✅ | Panel de control: KPIs, órdenes recientes, "Nueva Orden" → Cotizador. |
| `/comercial/proyectos` | EnConstruccion | 🔲 | Placeholder. |
| `/comercial/consultas` | Cotizador.vue | ✅ | Cotizador paramétrico + crear cliente rápido; "Convertir en Orden" → Sales Order. |
| `/comercial/ecommerce` | EnConstruccion | 🔲 | Placeholder. |
| `/comercial/clientes` | Clientes.vue | ✅ | ABM simplificado de clientes (Customer): listado, búsqueda, modal "Nuevo Cliente". |
| `/comercial/satisfaccion` | EnConstruccion | 🔲 | Placeholder. |
| `/operaciones/ordenes` | OrdenesList.vue | ✅ | Listado de Sales Orders con filtros (estado, búsqueda). |
| `/operaciones/tablero` | Produccion.vue | ✅ | Tablero Kanban Producción: Pendientes (Visto Bueno) / En Máquina / Finalizado. |
| `/operaciones/compras` | EnConstruccion | 🔲 | Placeholder. |
| `/operaciones/inventario` | Inventario.vue | ✅ | Listado de materiales (Mathipe Print Material) con costo editable. |
| `/operaciones/visto-bueno` | VistoBueno.vue | ✅ | Tablero Kanban Diseño: Bandeja de Entrada / Preimpresión / Visto Bueno. |
| `/calendario/agendamiento` | EnConstruccion | 🔲 | Placeholder. |
| `/calendario/tareas` | EnConstruccion | 🔲 | Placeholder. |
| `/admin/ventas` | EnConstruccion | 🔲 | Placeholder. |
| `/admin/pos` | EnConstruccion | 🔲 | Placeholder. |
| `/admin/compras` | EnConstruccion | 🔲 | Placeholder. |
| `/admin/pagos` | EnConstruccion | 🔲 | Placeholder. |
| `/admin/cobros` | Cobros.vue | ✅ | Cuentas por cobrar: tabla de órdenes con saldo pendiente, modal "Registrar Pago" (Payment Entry). |
| `/admin/cuentas` | EnConstruccion | 🔲 | Placeholder. |
| `/empresa/perfil` | EnConstruccion | 🔲 | Placeholder. |
| `/empresa/usuarios` | EnConstruccion | 🔲 | Placeholder. |
| `/empresa/productos` | Productos.vue | ✅ | Catálogo Mathipe Print Product: listado, crear/editar/eliminar. |
| `/empresa/precios` | EnConstruccion | 🔲 | Placeholder. |
| `/empresa/proveedores` | EnConstruccion | 🔲 | Placeholder. |
| `/empresa/monedas` | EnConstruccion | 🔲 | Placeholder. |
| `/empresa/configuraciones` | EnConstruccion | 🔲 | Placeholder. |
| `/orden/:id` | OrderDetail.vue | ✅ | Detalle de una Sales Order: cabecera, ítems, archivos, acciones Iniciar Producción / Terminar. |

**Leyenda:** ✅ Implementado con lógica y APIs; 🔲 Placeholder (EnConstruccion).

---

## 3. Módulos implementados (detalle)

### 3.1 Login y sesión

- **Ruta:** `/login`.
- **Vista:** `Login.vue`. Formulario usuario/contraseña.
- **APIs:** `get_session_data` (opcional), login vía `frappe.login()` (api/frappe).
- **Comportamiento:** Si ya hay sesión y se entra a `/login`, se puede redirigir a dashboard. Post-login el backend (`auth_redirect`) redirige a `/dashboard`.

---

### 3.2 Dashboard

- **Ruta:** `/dashboard`.
- **Vista:** `Dashboard.vue`.
- **API:** `get_dashboard_data()`.
  - Devuelve: `sales_total`, `orders_pending`, `orders_in_production`, `recent_orders` (lista con name, customer_name, delivery_date, status, items_preview, etc.).
- **UI:** KPIs (En Producción, Para Entregar, Atrasados, Ventas del mes), tabla de órdenes recientes.
- **Acciones:** Botón "Nueva Orden" → `/comercial/consultas` (Cotizador). Clic en fila → `/orden/:id`.

---

### 3.3 Cotizador (Consultas)

- **Ruta:** `/comercial/consultas`.
- **Vista:** `Cotizador.vue`.
- **APIs usadas:**
  - `search_customers(txt)` — búsqueda de clientes para el select.
  - `get_print_products()`, `get_print_materials()` — catálogo para producto y material.
  - `calculate_print_quote(product_id, material_id, qty, sides, width, height)` — precio sugerido en tiempo real.
  - `create_simple_customer(customer_name)` — crear cliente desde el cotizador (modal "Crear Cliente Rápido").
  - `create_quick_order(customer, items, delivery_date, remarks)` — crea Sales Order en Draft con ítem COTIZACION-IMPRESION y descripción paramétrica.
- **Flujo:** El usuario elige cliente (o crea uno nuevo), fecha de entrega, producto, material, cantidad, caras (1/2), opcional ancho/alto. Ve receta y precio. "Convertir en Orden" → orden creada → redirección a `/orden/:name`.
- **DocTypes:** Sales Order, Customer; Mathipe Print Product, Mathipe Print Material (cálculo).

---

### 3.4 Clientes

- **Ruta:** `/comercial/clientes`.
- **Vista:** `Clientes.vue`.
- **APIs:**
  - `get_all_customers(search_term)` — listado con name, customer_name, customer_group, territory; filtro por búsqueda; límite 50; orden modified desc.
  - `create_simple_customer(customer_name, customer_group, territory)` — crea Customer (customer_type Company). Por defecto usa grupo/territorio "Clientes"/"General" o los del cliente de referencia "Cliente Prueba" si existe.
- **UI:** Título "Directorio de Clientes", botón "+ Nuevo Cliente", búsqueda con debounce 300 ms, tabla (ID/Razón Social, Grupo, Territorio), modal con solo Razón Social obligatorio. Toast y recarga al crear.
- **DocType:** Customer (ERPNext).

---

### 3.5 Listado de órdenes

- **Ruta:** `/operaciones/ordenes`.
- **Vista:** `OrdenesList.vue`.
- **API:** `get_sales_orders_list(status, search_term)` — lista Sales Orders con name, customer_name, grand_total, transaction_date, delivery_date, status, workflow_state, items_preview.
- **UI:** Filtros por estado y búsqueda, tabla de órdenes, clic fila → `/orden/:id`.

---

### 3.6 Visto Bueno (Preimpresión / Diseño)

- **Ruta:** `/operaciones/visto-bueno`.
- **Vista:** `VistoBueno.vue`. Tablero Kanban 3 columnas.
- **APIs:**
  - `get_design_board()` — devuelve `inbox`, `working`, `approved` (listas de tarjetas con name, customer_name, delivery_date, item_summary, time_since). Clasificación por tags en Sales Order.
  - `update_design_status(order_id, action)` — acciones: `start_design` (En Diseño), `wait_client` (Esperando OK), `approve` (Visto Bueno + comentario "Visto Bueno Aprobado. Listo para Taller.").
- **Tags usados:** "En Diseño", "Esperando OK", "Visto Bueno". Las órdenes sin tags de diseño/producción entran en Bandeja de Entrada.
- **UI:** Columnas: Bandeja de Entrada (Tomar Diseño, Subir Archivo), Preimpresión (Pedir OK, Aprobar, Subir Archivo), Visto Bueno (Ver detalle, Subir Archivo). Auto-refresco 30 s.
- **DocType:** Sales Order (`_user_tags`).

---

### 3.7 Tablero de Producción

- **Ruta:** `/operaciones/tablero`.
- **Vista:** `Produccion.vue`. Kanban 3 columnas.
- **APIs:**
  - `get_production_board()` — devuelve `pending`, `in_progress`, `completed`. **Pending solo incluye órdenes con tag "Visto Bueno"** (no canceladas/cerradas). Tarjetas: name, customer_name, delivery_date, item_summary, time_since.
  - `update_production_status(order_id, action)` — `start` → "En Producción", `finish` → "Terminado".
- **Tags:** "En Producción", "Terminado". Pending = tiene "Visto Bueno" y no tiene En Producción ni Terminado.
- **UI:** Pendientes (Iniciar, Ver detalle), En Máquina (Terminar, Ver detalle), Finalizado (Ver detalle). Auto-refresco 30 s.
- **DocType:** Sales Order (`_user_tags`).

---

### 3.8 Detalle de orden

- **Ruta:** `/orden/:id`.
- **Vista:** `OrderDetail.vue`.
- **APIs:**
  - `get_order_details(order_id)` — cabecera, ítems, archivos adjuntos (File vinculados a la orden).
  - `update_order_workflow(order_id, action)` — acciones: `start_production` (To Deliver), `finish_production` (Completed).
- **UI:** Datos del pedido, tabla de ítems, sección "Archivos de Producción" (links a PDFs/archivos). Botones según estado: Iniciar Producción / Marcar Terminado.
- **DocType:** Sales Order, File.

---

### 3.9 Inventario (materiales)

- **Ruta:** `/operaciones/inventario`.
- **Vista:** `Inventario.vue`.
- **APIs:**
  - `get_inventory_materials()` — listado de Mathipe Print Material con nombre, costo, etc.
  - `update_material_cost(material_name, new_cost)` — actualiza costo del material.
- **UI:** Tabla de materiales, edición de costo (y recarga).
- **DocType:** Mathipe Print Material (custom).

---

### 3.10 Cobros (Panel de cobros)

- **Ruta:** `/admin/cobros`.
- **Vista:** `Cobros.vue`.
- **APIs:**
  - `get_pending_collections()` — Sales Orders no canceladas/cerradas con `advance_paid < grand_total`. Campos: name, customer_name, grand_total, advance_paid, status, pending_amount (= grand_total - advance_paid). Orden transaction_date desc.
  - `register_payment(order_id, paid_amount, mode_of_payment)` — crea Payment Entry (Receive) contra la Sales Order, con referencia y allocated_amount; insert + submit. Resolución de cuenta: Mode of Payment → cuenta por defecto compañía → primera Cash/Bank (con fallback ignore_permissions si hace falta).
- **UI:** Tabla "Cuentas por Cobrar (Señas y Saldos)": Orden, Cliente, Total, Pagado, Saldo Pendiente (en rojo si > 0), botón Cobrar. Modal "Registrar Pago": Monto a Cobrar (por defecto saldo pendiente), Medio de Pago (Efectivo, Transferencia, Tarjeta), Cancelar / Guardar Pago. Toast y recarga.
- **DocTypes:** Sales Order, Payment Entry (ERPNext).

---

### 3.11 Productos / Servicios (catálogo impresión)

- **Ruta:** `/empresa/productos`.
- **Vista:** `Productos.vue`.
- **APIs:**
  - `get_print_products()` o `get_all_print_products()` — listado Mathipe Print Product.
  - `save_print_product(name, product_name, base_setup_cost, print_cost_per_side)` — crear o actualizar.
  - `delete_print_product(name)` — eliminar.
- **UI:** Listado de productos, formulario crear/editar (nombre, costo setup, costo impresión por cara), eliminar. Diseño consistente con el resto (tabla, modales/toast).
- **DocType:** Mathipe Print Product (custom).

---

### 3.12 EnConstruccion

- **Componente:** `EnConstruccion.vue`. Página placeholder para rutas aún no implementadas (Proyectos, E-commerce, Satisfacción, Compras, Agendamiento, Ventas, POS, Pagos, Cuentas, Perfil, Usuarios, Precios, Proveedores, Monedas, Configuraciones).

---

## 4. Flujo de negocio (resumen)

1. **Ventas:** Cotizador → cliente (existente o nuevo) → producto/material/cantidad → "Convertir en Orden" → Sales Order en Draft.
2. **Diseño:** Órdenes nuevas aparecen en Visto Bueno (Bandeja de Entrada). Diseñador: Tomar Diseño → Preimpresión; Pedir OK o Aprobar → Visto Bueno. Subir archivos desde "Subir Archivo" (va a `/orden/:id`).
3. **Producción:** Solo órdenes con tag "Visto Bueno" entran en la cola del Tablero. Operario: Iniciar → En Máquina; Terminar → Finalizado. Detalle y archivos en `/orden/:id`.
4. **Cobros:** En Admin → Cobros se listan órdenes con saldo pendiente; "Cobrar" abre modal para registrar pago (Payment Entry) como seña o pago total.

---

## 5. Backend: APIs (mathipe_ui/api.py)

Todas las que se llaman desde la SPA están decoradas con `@frappe.whitelist()`.

### Sesión y dashboard

- `get_session_data()` — user, csrf; para SPA.
- `get_dashboard_data()` — KPIs y órdenes recientes.

### Órdenes y detalle

- `get_order_details(order_id)` — cabecera, ítems, archivos de la Sales Order.
- `update_order_workflow(order_id, action)` — start_production / finish_production.
- `get_sales_orders_list(status, search_term)` — listado para OrdenesList.

### Tableros (tags en Sales Order)

- `get_production_board()` — pending (solo con tag Visto Bueno), in_progress, completed; tarjetas con item_summary, time_since.
- `update_production_status(order_id, action)` — start / finish.
- `get_design_board()` — inbox, working, approved.
- `update_design_status(order_id, action)` — start_design / wait_client / approve.

### Cotizador y órdenes rápidas

- `get_print_products()`, `get_all_print_products()` — productos impresión.
- `get_print_materials()` — materiales impresión.
- `calculate_print_quote(product_id, material_id, qty, sides, width, height)` — cálculo de precio.
- `search_customers(txt)` — búsqueda clientes.
- `create_quick_order(customer, items, delivery_date, remarks)` — crea Sales Order con ítem COTIZACION-IMPRESION.

### Clientes

- `get_all_customers(search_term)` — listado filtrado; límite 50.
- `create_simple_customer(customer_name, customer_group, territory)` — crea Customer (defaults: grupo "Clientes", territorio "General", o los de "Cliente Prueba").
- `ensure_customer_group_and_territory()` — crea DocTypes Customer Group "Clientes" y Territory "General" si no existen (para Desk/consola).

### Catálogo productos impresión

- `save_print_product(name, product_name, base_setup_cost, print_cost_per_side)` — crear/actualizar Mathipe Print Product.
- `delete_print_product(name)` — borrar producto.

### Inventario materiales

- `get_inventory_materials()` — listado materiales.
- `update_material_cost(material_name, new_cost)` — actualizar costo.

### Cobros

- `get_pending_collections()` — órdenes con saldo pendiente (grand_total - advance_paid).
- `register_payment(order_id, paid_amount, mode_of_payment)` — crea y envía Payment Entry contra Sales Order; resuelve cuenta Caja/Banco (Mode of Payment, compañía, Cash/Bank).

### Otros

- `get_sale_items(txt)` — búsqueda ítems de venta (prefijo).

---

## 6. DocTypes y datos involucrados

- **Estándar ERPNext:** Sales Order, Customer, Payment Entry, File, Account, Company, Mode of Payment, Mode of Payment Account.
- **Custom (mathipe_ui):** Mathipe Print Product, Mathipe Print Material. Ítem estándar: COTIZACION-IMPRESION (para líneas de cotización en la orden).
- **Tags en Sales Order (_user_tags):** En Diseño, Esperando OK, Visto Bueno, En Producción, Terminado.

---

## 7. Estructura de archivos (referencia)

```
mathipe_ui/
├── mathipe_ui/
│   ├── api.py              # Todas las APIs whitelisted
│   ├── spa_serve.py        # Sirve SPA en rutas /, /login, /dashboard, /orden/...
│   ├── auth_redirect.py    # Redirect post-login a /dashboard
│   ├── fix_install.py      # Reparar/instalar DocTypes y datos de prueba
│   ├── setup_data.py       # Datos demo (ítem, material, producto)
│   └── public/
│       └── spa/            # Build del frontend (index.html + assets/)
├── frontend/
│   ├── src/
│   │   ├── api/frappe.js   # call(), getSession(), login()
│   │   ├── router/index.js # Rutas y guard de sesión
│   │   ├── views/          # Login, Dashboard, Cotizador, Clientes, OrdenesList, VistoBueno, Produccion, OrderDetail, Inventario, Cobros, Productos, EnConstruccion, etc.
│   │   ├── components/     # Sidebar.vue (navegación por secciones)
│   │   └── layouts/        # MainLayout.vue
│   └── index.html
└── RESUMEN_PROYECTO.md     # Este archivo
```

---

## 8. Comandos útiles

```bash
# Build frontend
cd apps/mathipe_ui/frontend && npm run build

# Desarrollo con proxy al backend
cd apps/mathipe_ui/frontend && npm run dev

# Limpiar caché
bench --site all clear-cache

# Reiniciar (tras cambios en api.py)
bench restart

# Instalar/reparar DocTypes y datos demo (una vez por site)
bench --site <site> execute mathipe_ui.fix_install.fix_install
bench --site <site> execute mathipe_ui.setup_data.install_demo_data
```

---

## 9. Notas para la IA

- Las vistas usan **Tailwind** y **lucide-vue-next**; estilo coherente: fondos `bg-slate-50`, tablas blancas con sombra, botones primarios indigo.
- Las llamadas al backend son con **`call("mathipe_ui.api.<nombre_funcion>", { ... })`**; la respuesta suele estar en `res.message` o `res`.
- **Router:** rutas bajo MainLayout excepto `/login` (pública). Guard verifica sesión con `getSession()`.
- **Cobros:** Si no hay cuenta Caja/Banco, `register_payment` devuelve error indicando configurar Plan de cuentas y Cuenta de caja en la Compañía.
- **Clientes:** Nuevos clientes se crean con grupo/territorio por defecto (Clientes/General o los de "Cliente Prueba"); no se usan literales "All Customer Groups" / "All Territories" para evitar errores en sitios en español.

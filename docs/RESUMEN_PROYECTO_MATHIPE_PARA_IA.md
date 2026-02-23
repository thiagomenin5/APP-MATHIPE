# Resumen del proyecto ERP Mathipe (para contexto de IA)

Documento de referencia para que una IA entienda qué está implementado, cómo funciona y dónde está cada cosa. **Responder siempre en español.** No usar Frappe Desk: todo por APIs whitelisted en `mathipe_ui/api.py`. Work Order es la fuente de verdad operativa; Sales Order es documento comercial.

---

## 1. Visión y arquitectura

- **Objetivo:** ERP para imprenta (estilo Twist Print): digitalizar cotizaciones, seguimiento, producción, tercerización, aprobaciones y clientes.
- **Flujo:** Cotización → Work Order → Diseño → Aprobación → Producción → Entrega → Cobro → Análisis.
- **Frontend:** SPA Vue 3 + Tailwind; rutas bajo `/` con MainLayout; login y sesión vía `getSession()`.
- **Backend:** Frappe; lógica expuesta solo por **APIs whitelisted** en `mathipe_ui/api.py` (módulo `mathipe_ui` dentro del app). No depender del Desk.
- **Convenciones:** Cambios pequeños y verificables; no refactors masivos; UI coherente con Tailwind actual.

---

## 2. Stack técnico

| Capa | Tecnología |
|------|------------|
| Backend | Frappe (Python), DB MySQL/MariaDB |
| API | `mathipe_ui.api` – todas las funciones expuestas con `@frappe.whitelist()` |
| Frontend | Vue 3 (Composition API), Vue Router, Tailwind CSS |
| Iconos | lucide-vue-next |
| Llamadas API | Cliente en `@/api/frappe` (call, uploadFile, getSession) |

---

## 3. DocTypes del módulo (Frappe)

- **Mathipe Quote** – Cotización (customer, delivery_date, status, totales). Child: Mathipe Quote Item.
- **Mathipe Quote Item** – Ítems de cotización (product_type Fixed/Area/Recipe, qty, width, height, unit_price, cost/sale totals, breakdown persistente, is_outsourced, supplier, recipe_reference).
- **Mathipe Product Recipe** – Receta de producto (product_name, default_margin_pct, allow_dimensions, allow_qty). Child: Mathipe Recipe Component.
- **Mathipe Recipe Component** – Componentes de receta (component_type, costing_mode, qty_per_unit, qty_per_m2, etc.).
- **Mathipe Work Order** – **Entidad central operativa.** Campos: naming_series (MWO-.YYYY.-), sales_order (Link Sales Order), customer, customer_name, delivery_date, status (New, Design, WaitingApproval, Approved, Production, Done, Delivered, Cancelled), tags, notes, revenue_total, estimated_cost_total, real_cost_total, gross_margin, gross_margin_pct, items (child), assigned_users, checklist_items, status_log. La OT se crea al convertir la cotización a Sales Order.
- **Mathipe WO Item** – Ítems de la OT (quote_item, item_code, description, product_type, qty, width, height, area_total, cost_total, sale_total, is_outsourced, supplier, outsource_status, outsource_sent_at, outsource_received_at, outsource_cost, outsource_notes, breakdown_version, source).
- **Mathipe WO Status Log** – Historial de cambios de estado (from_status, to_status, changed_by, changed_at, comment).
- **Mathipe WO Assigned User** – Usuarios asignados a la OT.
- **Mathipe WO Checklist Item** – Checklist de control (title, done, done_by, done_at).
- **Mathipe Print Product** / **Mathipe Print Material** – Catálogo de productos y materiales de impresión (cotizador legacy/alternativo).
- **Mathipe Settings** (Single) – Configuración global: default_customer, default_selling_price_list, vat_rate, currency, external_invoicing; **Fase 5:** umbrales de alertas (alerts_enabled, low_margin_pct_threshold, warning_margin_pct_threshold, waiting_approval_days_threshold, outsource_sent_days_threshold, overdue_delivery_days_threshold).

Campos en estándar Frappe: Sales Order tiene Custom Field `mathipe_quote` (Link Mathipe Quote). Mathipe Quote tiene `sales_order` (Link Sales Order). Item puede tener `mathipe_product_type`.

---

## 4. Patches (migraciones)

Archivo: `mathipe_ui/patches.txt`. Orden de ejecución (post_model_sync):

1. import_mathipe_workspace  
2. add_mathipe_product_type_to_item  
3. add_mathipe_quote_links (Quote ↔ SO)  
4. ensure_fase1_indexes  
5. install_mathipe_wo_item_and_status_log  
6. ensure_fase2_outsourcing_indexes  
7. ensure_wo_item_quote_item_index  
8. add_fase3_financial_fields (revenue_total, estimated_cost_total, real_cost_total, gross_margin, gross_margin_pct en WO)  
9. add_fase5_alert_settings (Custom Fields de alertas en Mathipe Settings)

---

## 5. APIs whitelisted (api.py) – por dominio

### Sesión y dashboard

- `get_session_data()` – user, csrf_token.
- `get_dashboard_data()` – KPIs (sales_total, orders_pending, orders_in_production), recent_orders.

### Órdenes (Sales Order) y detalle

- `get_order_details(order_id)` – Orden + ítems + attachments/tags para OrderDetail.
- `update_order_workflow(order_id, action)` – Acciones de flujo sobre la orden.
- `get_sales_orders_list(status, search_term)` – Listado de SO.

### Tableros “legacy” (basados en Sales Order + tags)

- `get_production_board()` – Kanban por tags (Pending, En Producción, Terminado).
- `get_design_board()` – Kanban Diseño (inbox, working, approved).
- `update_design_status(order_id, action)` – start_design, wait_client, approve.
- `update_production_status(order_id, action)` – start, finish.

### Impresión / productos (catálogo)

- `get_print_materials()`, `get_all_print_products()`, `save_print_product()`, `delete_print_product()`, `get_print_products()`.
- `get_inventory_materials()`, `update_material_cost()`.
- `calculate_print_quote(...)` – Cotización por producto de impresión.

### Cotizador (Mathipe Quote)

- `get_quote_products_catalog()`, `calculate_quote_item(payload)` – Cálculo por ítem (Fixed/Area/Recipe).
- `create_quote(customer, delivery_date, items, notes)` – Crea Mathipe Quote con ítems.
- `get_quote(quote_id)` – Quote con ítems y cost_lines (breakdown); opcional sales_order, breakdown_version.
- `convert_quote_to_sales_order(quote_id)` – Crea Sales Order + Mathipe Work Order; idempotente si ya convertida.

### Clientes

- `search_customers(txt)`, `get_all_customers(search_term)`.
- `create_simple_customer(...)`, `ensure_customer_group_and_territory()`.
- `get_sale_items(txt)`.
- `create_quick_order(customer, items, delivery_date, remarks)` – Orden rápida sin cotización.

### Cobros / pagos

- `get_pending_collections()` – Cobros pendientes.
- `register_payment(order_id, paid_amount, mode_of_payment)` – Registrar pago.

### Work Order (núcleo operativo)

- `create_or_get_work_order(sales_order_id)` – Devuelve OT existente o crea una nueva; serialización vía `_get_wo_detail`.
- `get_work_order(work_order_id)`, `get_work_order_by_so(sales_order_id)`.
- `get_work_order_details(work_order_id)` – Detalle completo (alias/envoltorio que usa _get_wo_detail).
- `get_work_order_items(work_order_id)`.
- `update_work_order_assignments(work_order_id, user_ids)`.
- `update_work_order_tags(work_order_id, tags)`.
- `update_work_order_checklist(work_order_id, checklist_items)`.
- `update_work_order_status(work_order_id, to_status, comment)` – Con registro en Mathipe WO Status Log; reglas de transición y bloqueos (ej. ítems tercerizados no recibidos).
- `request_client_approval(work_order_id, message)` – Pone estado WaitingApproval.
- `approve_work_order(work_order_id, comment)` – Pone Approved.
- `update_work_order_notes(work_order_id, notes)`.
- `resync_work_order_items_from_quote(work_order_id)` – Sincroniza ítems WO desde la Quote.
- `update_work_order_item(work_order_id, item_row_id, patch_fields)` – Actualiza ítem (supplier, is_outsourced, outsource_cost, etc.).
- `update_outsource_status(work_order_id, item_row_id, action, comment)` – Marca Sent/Received; action: sent | received.
- `get_wo_board()` – Tablero Kanban por WO.status (new, design, waiting_approval, approved, production, done); cada tarjeta incluye alerts_summary y top_alert_* (Fase 5).
- `get_outsource_board(filters)` – Ítems tercerizados agrupados en pending_vendor, sent, received; filtros supplier, date_from, date_to, only_overdue; incluye alerts_summary por WO (Fase 5).
- `get_my_work_orders(user)` – OTs asignadas al usuario.

### Alertas (Fase 5)

- `get_work_order_alerts(work_order_id)` – Lista de alertas + summary (danger, warning, info).
- `get_alerts_board(date_from, date_to, only_open, level)` – Lista de OTs con alertas para vista Admin; filtro por delivery_date y nivel; incluye sales_order para enlace a detalle.

### Finanzas y analítica (Fase 3 / 4)

- `get_financial_dashboard(date_from, date_to, include_without_sales_order)` – KPIs (total_revenue, total_real_cost, total_margin, avg_margin_pct), top/bottom 5 OTs por margen; filtro por transaction_date (o fallback DATE(wo.creation)); costo real por ítem: tercerizado Received → outsource_cost, sino cost_total.
- `get_profitability_breakdown(date_from, date_to, include_without_sales_order, min_revenue)` – Analítica por cliente, por tipo de ítem (product_type), por proveedor; bottom_by_margin_pct con min_revenue.

### Utilidades

- `get_system_users()` – Usuarios habilitados (para asignación).

Funciones internas (no whitelisted) relevantes: `_get_wo_detail(work_order_id)` (serializa WO para frontend, incluye items, status_log, financials, valid_next_statuses, alerts y alerts_summary en Fase 5), `get_mathipe_settings()`, `_compute_alerts(wo_doc, settings)`, `_compute_alerts_summary(wo_doc, settings)`, `_wo_valid_next_statuses(status, user)` (retrocesos y Cancelled solo System Manager / Gerencia), `_require_login()`.

---

## 6. Frontend – Rutas y vistas

Raíz SPA: `/`. Login: `/login` (público). Detalle orden: `/orden/:id` (OrderDetail.vue; :id = Sales Order name).

### Implementadas (componentes reales)

- **Dashboard** – `/dashboard` – Dashboard.vue  
- **Cotizador** – `/comercial/consultas` – Cotizador.vue  
- **Clientes** – `/comercial/clientes` – Clientes.vue  
- **Orden de trabajo (lista)** – `/operaciones/ordenes` – OrdenesList.vue  
- **Tablero producción (WO)** – `/operaciones/tablero` – Produccion.vue (get_wo_board; badges de alertas)  
- **Tercerización** – `/operaciones/tercerizacion` – OutsourcingBoard.vue (get_outsource_board; badges de alertas)  
- **Inventario** – `/operaciones/inventario` – Inventario.vue  
- **Visto bueno** – `/operaciones/visto-bueno` – VistoBueno.vue (get_wo_board; badges de alertas)  
- **Cobros** – `/admin/cobros` – Cobros.vue  
- **Finanzas** – `/admin/finanzas` – Finanzas.vue (get_financial_dashboard)  
- **Alertas** – `/admin/alertas` – Alertas.vue (get_alerts_board; filtros nivel, solo abiertas, fechas; tabla con clic a /orden/:id)  
- **Analítica** – `/admin/analitica` – Analitica.vue (get_profitability_breakdown)  
- **Productos / Servicios** – `/empresa/productos` – Productos.vue  
- **OrderDetail** – `/orden/:id` – OrderDetail.vue: pestañas Detalle y “Workspace OT” (asignaciones, tags, checklist, estado, tercerización por ítem, historial, notas, **panel Alertas** arriba del resumen financiero, resumen financiero).  
- **OTPrint** – `/print/ot/:id` – OTPrint.vue (público, impresión OT)

### En construcción (placeholder)

EnConstruccion.vue: comercial/proyectos, comercial/ecommerce, comercial/satisfaccion, operaciones/compras, calendario/agendamiento, calendario/tareas, admin/ventas, admin/pos, admin/compras, admin/pagos, admin/cuentas, empresa/perfil, empresa/usuarios, empresa/precios, empresa/proveedores, empresa/monedas, empresa/configuraciones.

---

## 7. Fases implementadas (resumen)

### Fase 1 – Núcleo operativo

- Mathipe Quote + Quote Item; Mathipe Work Order como centro; conversión Quote → Sales Order + Work Order.
- Tableros basados en WO.status (no en tags de SO).
- Workspace OT en OrderDetail: asignaciones, tags, checklist, cambio de estado, impresión OT.
- Cotizador multi-ítem (Fixed, Area, Recipe) con breakdown y totales.

### Fase 2 – Flujo y tercerización

- Estados: New → Design → WaitingApproval → Approved → Production → Done → Delivered / Cancelled.
- Mathipe WO Item con is_outsourced, supplier, outsource_status (PendingVendor, Sent, Received); bloqueo a Production hasta ítems tercerizados Received.
- Mathipe WO Status Log en cada cambio de estado; retrocesos y Cancelled solo para System Manager / Gerencia (comentario OVERRIDE en log).
- Tablero Visto Bueno y Tablero Producción con get_wo_board; Tablero Tercerización con get_outsource_board.

### Fase 3 – Finanzas

- Campos en WO: revenue_total, estimated_cost_total, real_cost_total, gross_margin, gross_margin_pct (patch add_fase3_financial_fields).
- get_financial_dashboard: KPIs y top/bottom OTs por margen; filtro por transaction_date.
- Resumen financiero en OrderDetail (Workspace OT).

### Fase 4 (parcial) – Analítica

- get_profitability_breakdown: por cliente, por tipo de ítem, por proveedor; bottom_by_margin_pct con min_revenue.
- Vista Admin → Analítica.

### Fase 5 – Alertas inteligentes (sin emails/WhatsApp)

- Mathipe Settings: umbrales de alertas (patch add_fase5_alert_settings); get_mathipe_settings() con defaults.
- Reglas: LOW_MARGIN, WAITING_APPROVAL_TOO_LONG (status_log), OUTSOURCE_SENT_TOO_LONG, OUTSOURCE_PENDING_VENDOR, DELIVERY_OVERDUE.
- get_work_order_alerts(work_order_id); get_alerts_board(...).
- _get_wo_detail y tableros (get_wo_board, get_outsource_board) incluyen alerts_summary y top_alert_*.
- OrderDetail: panel Alertas (chips, lista, “Ver en Alertas”); tableros: badge rojo/amarillo por tarjeta; vista Admin → Alertas (filtros, tabla, clic a /orden/:id); ítem “Alertas” en sidebar.

---

## 8. Reglas de negocio importantes

- **Conversión idempotente:** Si la Quote ya tiene sales_order, convert_quote_to_sales_order devuelve esa SO y WO sin duplicar.
- **Transiciones de estado WO:** Definidas en código; solo se permiten los “valid_next_statuses” según estado actual y rol (retroceso/Cancelled solo Gerencia/System Manager).
- **Tercerización:** No se puede pasar a Production si hay ítems con is_outsourced y outsource_status != Received.
- **Costo real en finanzas/analítica:** Por ítem: si is_outsourced y outsource_status == Received → outsource_cost; si no → cost_total (estimado).
- **Alertas:** Solo si alerts_enabled en Mathipe Settings; umbrales configurables; en tableros solo se expone summary (counts + top alert).

---

## 9. Estructura de carpetas relevante

```
mathipe_ui/
├── mathipe_ui/
│   ├── api.py                    # Todas las APIs whitelisted + helpers
│   ├── patches/
│   │   ├── add_fase3_financial_fields.py
│   │   ├── add_fase5_alert_settings.py
│   │   ├── add_mathipe_quote_links.py
│   │   ├── install_mathipe_wo_item_and_status_log.py
│   │   └── ...
│   ├── patches.txt
│   ├── doctype/
│   │   ├── mathipe_work_order/
│   │   ├── mathipe_wo_item/
│   │   ├── mathipe_wo_status_log/
│   │   ├── mathipe_quote/
│   │   ├── mathipe_quote_item/
│   │   ├── mathipe_settings/
│   │   └── ...
│   └── scripts/
│       ├── test_fase1.py
│       ├── test_alertas.py
│       ├── test_outsourcing.py
│       └── test_analitica.py
├── frontend/
│   └── src/
│       ├── api/frappe.js
│       ├── router/index.js
│       ├── views/           # OrderDetail, Produccion, VistoBueno, OutsourcingBoard, Alertas, Finanzas, Analitica, Cotizador, Clientes, Cobros, etc.
│       ├── components/     # Sidebar.vue, ...
│       └── layouts/        # MainLayout.vue
├── docs/
│   ├── IMPLEMENTACION_FASE_5_ALERTAS.md
│   ├── IMPLEMENTACION_FASE_2_SPRINT_B_OUTSOURCING.md
│   └── RESUMEN_PROYECTO_MATHIPE_PARA_IA.md  # este archivo
├── IMPLEMENTACION_COMPLETA.MD
├── IMPLEMENTACION_FASE_1_MATHIPE.MD
├── IMPLEMENTACION_FASE_2_MATHIPE.MD
├── IMPLEMENTACION_FASE_3_MATHIPE.MD
└── IMPLEMENTACION_FASE_4_MATHIPE.MD
```

---

## 10. Cómo probar (resumen)

- **Migrar:** `bench --site [site] migrate`
- **Tests:**  
  - Fase 1: `bench --site [site] execute mathipe_ui.scripts.test_fase1.run_tests`  
  - Tercerización: `mathipe_ui.scripts.test_outsourcing.run_tests`  
  - Analítica: `mathipe_ui.scripts.test_analitica.run_tests`  
  - Alertas: `mathipe_ui.scripts.test_alertas.run_tests`
- **UI:** Crear cotización → convertir a orden → abrir orden → pestaña Workspace OT (estado, ítems, tercerización, alertas, finanzas); tableros Producción / Visto Bueno / Tercerización; Admin → Finanzas, Alertas, Analítica.

---

Este resumen debe bastar para que una IA entienda el alcance implementado, la arquitectura y dónde tocar para nuevas funcionalidades o correcciones.

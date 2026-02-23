# Fase 5 – Alertas inteligentes (Mathipe)

Objetivo: que el ERP “avise” en tableros y detalle cuando haya riesgos (margen bajo, aprobaciones demoradas, tercerizados atrasados). Sin integraciones externas (emails/WhatsApp en Fase 5.1).

---

## 1. Configuración (Mathipe Settings)

Umbrales configurables en **Mathipe Settings** (Single DocType). Si no existe el documento o faltan campos, se añaden vía patch idempotente y se usan defaults en código.

| Campo | Default | Descripción |
|-------|--------|-------------|
| `alerts_enabled` | 1 | Activar/desactivar alertas en tableros y detalle |
| `low_margin_pct_threshold` | 15 | Margen bruto por debajo → nivel **danger** |
| `warning_margin_pct_threshold` | 25 | Margen por debajo → nivel **warning** (y ≥ low_margin) |
| `waiting_approval_days_threshold` | 3 | Días en WaitingApproval sin cambio → alerta |
| `outsource_sent_days_threshold` | 5 | Días desde envío a proveedor (Sent) → alerta |
| `overdue_delivery_days_threshold` | 0 | Si delivery_date &lt; hoy → atrasado (danger si ≥ 3 días) |

**Helper backend:** `get_mathipe_settings()` en `mathipe_ui.api` devuelve un dict con los valores anteriores; si no existe el doc o falta un campo, se usa el default.

---

## 2. Reglas de alertas

Función central: **`_compute_alerts(wo_doc, settings)`** → `list[alert]`.

Cada alerta:

- `code`: `LOW_MARGIN` | `WAITING_APPROVAL_TOO_LONG` | `OUTSOURCE_SENT_TOO_LONG` | `OUTSOURCE_PENDING_VENDOR` | `DELIVERY_OVERDUE`
- `level`: `danger` | `warning` | `info`
- `title`: string
- `message`: string
- `meta`: dict opcional (days, threshold, supplier, margin_pct, etc.)

### Reglas

- **LOW_MARGIN**: Si `revenue_total > 0` y `gross_margin_pct < low_margin_pct_threshold` → danger; si `gross_margin_pct < warning_margin_pct_threshold` (y ≥ low) → warning.
- **WAITING_APPROVAL_TOO_LONG**: `status == "WaitingApproval"` y días desde última transición a WaitingApproval (vía `status_log`: última fila con `to_status == "WaitingApproval"`, `changed_at`) ≥ `waiting_approval_days_threshold`. Fallback: `wo.modified` o `wo.creation`.
- **OUTSOURCE_SENT_TOO_LONG**: Algún ítem con `is_outsourced=1`, `outsource_status == "Sent"` y días desde `outsource_sent_at` ≥ `outsource_sent_days_threshold`. Una alerta por proveedor (agrupada).
- **OUTSOURCE_PENDING_VENDOR**: Algún ítem tercerizado con estado PendingVendor → info.
- **DELIVERY_OVERDUE**: `delivery_date < hoy` y `status` no in (`Delivered`, `Cancelled`). Danger si atraso ≥ 3 días, warning si 1–2 días.

---

## 3. Endpoints (api.py)

| Endpoint | Descripción |
|----------|-------------|
| **get_work_order_alerts(work_order_id)** | Devuelve `{ "alerts": [...], "summary": { "danger", "warning", "info" } }`. |
| **get_alerts_board(date_from, date_to, only_open=1, level=None)** | Lista de OTs con alertas para vista Admin. Filtro por `delivery_date`, `only_open` (excluye Delivered/Cancelled), `level` (danger/warning/info). Campos: `work_order_id`, `sales_order`, `customer_name`, `delivery_date`, `status`, `margin_pct`, `alerts_summary`, `top_alert_title`. |

Serialización WO:

- **\_get_wo_detail**: Incluye `alerts`, `alerts_summary`, `top_alert_level`, `top_alert_code`, `top_alert_title`.
- **get_wo_board** y **get_outsource_board**: Cada tarjeta/fila incluye `alerts_summary`, `top_alert_level`, `top_alert_code`, `top_alert_title` (solo resumen; no lista completa).

Para tableros se usa **`_compute_alerts_summary(wo_doc, settings)`** (counts + top alert); para detalle, **`_compute_alerts`** completo.

---

## 4. Pantallas

- **OrderDetail.vue**: Panel “Alertas” arriba del Resumen Financiero: chips por nivel (rojo/amarillo/azul), lista de alertas (título + mensaje), botón “Ver en Alertas” → `/admin/alertas`.
- **Tableros** (Produccion.vue, VistoBueno.vue, OutsourcingBoard.vue): Badge en la tarjeta si `alerts_summary.danger > 0` (rojo) o `warning > 0` (amarillo); tooltip “Hay alertas”.
- **Admin → Alertas** (`/admin/alertas`, Alertas.vue): Filtros nivel, solo abiertas, rango de fechas (delivery_date). Tabla: OT, Cliente, Entrega, Estado, Margen %, Alertas (count), Top alerta. Clic en fila → `/orden/:id` (Sales Order).
- **Sidebar**: Ítem “Alertas” en sección Administración.

---

## 5. Archivos modificados/creados

- **Backend**
  - `mathipe_ui/patches/add_fase5_alert_settings.py` (nuevo)
  - `mathipe_ui/patches.txt` (añadida línea del patch)
  - `mathipe_ui/api.py`: `get_mathipe_settings`, `_compute_alerts`, `_compute_alerts_summary`, `get_work_order_alerts`, `get_alerts_board`; cambios en `_get_wo_detail`, `get_wo_board`, `get_outsource_board`
- **Frontend**
  - `frontend/src/views/OrderDetail.vue`: panel Alertas, import AlertTriangle
  - `frontend/src/views/Produccion.vue`: badges en tarjetas
  - `frontend/src/views/VistoBueno.vue`: badges en tarjetas
  - `frontend/src/views/OutsourcingBoard.vue`: badges en tarjetas
  - `frontend/src/views/Alertas.vue` (nuevo)
  - `frontend/src/router/index.js`: ruta `admin/alertas`
  - `frontend/src/components/Sidebar.vue`: ítem Alertas, import AlertTriangle
- **Tests y doc**
  - `mathipe_ui/scripts/test_alertas.py` (nuevo)
  - `docs/IMPLEMENTACION_FASE_5_ALERTAS.md` (este archivo)

---

## 6. Migración y validación

1. **Migrar**
   - `bench --site [site] migrate`
   - Verificar que el patch `add_fase5_alert_settings` se ejecutó y que en **Mathipe Settings** aparecen los campos de alertas (o Custom Fields en el formulario).

2. **Reiniciar / reconstruir frontend** si aplica:
   - `npm run build` en `apps/mathipe_ui/frontend` o según el flujo del proyecto.

3. **Ejecutar tests**
   - `bench --site [site] execute mathipe_ui.scripts.test_alertas.run_tests`
   - Revisar que pasen: LOW_MARGIN, WAITING_APPROVAL_TOO_LONG (si aplica), OUTSOURCE_SENT_TOO_LONG (si WO tiene ítems), y que `get_work_order_alerts` devuelve niveles y counts correctos.

---

## 7. Checklist QA manual

- [ ] Mathipe Settings: se ven y guardan umbrales de alertas; al desmarcar “Alertas habilitadas” no se muestran alertas en detalle ni tableros.
- [ ] OrderDetail (pestaña Workspace OT): con una OT que tenga margen bajo y/o aprobación demorada y/o ítem Sent hace días, se muestra el panel Alertas con chips y lista; “Ver en Alertas” lleva a `/admin/alertas`.
- [ ] Tablero Producción / Visto Bueno: tarjetas con alertas muestran punto rojo (danger) o amarillo (warning) y tooltip “Hay alertas”.
- [ ] Tablero Tercerización: ítems con WO que tiene alertas muestran el mismo badge.
- [ ] Admin → Alertas: filtros por fechas, “Solo abiertas” y nivel; tabla con OT, cliente, entrega, estado, margen %, conteo de alertas y top alerta; clic en fila abre detalle de la orden (`/orden/:id`).
- [ ] Sidebar: en Administración aparece el ítem “Alertas”.

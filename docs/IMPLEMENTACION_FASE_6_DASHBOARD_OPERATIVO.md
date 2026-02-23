# Fase 6 – Dashboard operativo central (estilo Twist Print)

Objetivo: home real con KPIs accionables y listas con foco operativo; navegación rápida a OT vía `/orden/:sales_order`.

---

## 1. Backend: get_operational_dashboard(date_from=None, date_to=None)

**Archivo:** `mathipe_ui/api.py`

**Respuesta:**

- **kpis** (counts):
  - `wo_active_count`: WOs no Cancelled ni Delivered
  - `wo_waiting_approval_count`: status = WaitingApproval
  - `wo_in_production_count`: status = Production
  - `wo_outsourcing_pending_count`: WOs con al menos un ítem is_outsourced=1 y outsource_status en ('PendingVendor','Sent')
  - `deliveries_today_count`: delivery_date = hoy y activa
  - `overdue_deliveries_count`: delivery_date < hoy y activa
  - `danger_alerts_count` / `warning_alerts_count`: muestreo sobre primeras 200 OTs activas (por _compute_alerts_summary)
- **kpis financieros:** `monthly_revenue`, `avg_margin_pct`, `total_margin` (reutilizando get_financial_dashboard con date_from/date_to e include_without_sales_order=0)
- **Listas (máx 8 cada una):**
  - `urgent_work_orders`: activas, orden delivery_date asc
  - `critical_alerts`: activas con alerts_summary.danger > 0, orden delivery_date asc luego danger desc
  - `waiting_approval`: status = WaitingApproval, orden por tiempo en estado desc (status_log)
  - `outsourcing_overdue`: WOs con ítem Sent y (hoy - outsource_sent_at) >= outsource_sent_days_threshold, orden días desc

Cada ítem de lista incluye: work_order_id, sales_order, customer_name, delivery_date, status, gross_margin_pct, alerts_summary, top_alert_title, top_alert_level.

---

## 2. Frontend: DashboardOperativo.vue

**Archivo:** `frontend/src/views/DashboardOperativo.vue`

- Header "Dashboard" y filtros de período (date_from, date_to) para KPIs financieros.
- Grid de KPIs: 8 operativos + 2 financieros (ingresos período, margen período + promedio %).
- Cuatro secciones: Urgentes, Alertas críticas, Esperando aprobación, Tercerización vencida.
- Cada fila clickable → `/orden/:sales_order`.
- Chips de estado, fecha entrega, badge rojo/amarillo de alertas, margen % con color (verde/amarillo/rojo).
- Estado vacío: "Sin datos para el período / no hay pendientes" (o mensaje por sección).

---

## 3. Router y Sidebar

- Ruta `/dashboard` usa `DashboardOperativo.vue` (reemplaza el anterior Dashboard.vue en la ruta).
- Post-login redirige a `/` que hace redirect a `/dashboard`.
- Sidebar: ítem "Dashboard" en favoritos (arriba), icono LayoutDashboard; activo cuando `route.path === '/dashboard'`.

---

## 4. Archivos tocados

| Tipo     | Archivo |
|----------|---------|
| Backend  | `mathipe_ui/api.py` (get_operational_dashboard, _enrich_wo_row) |
| Frontend | `frontend/src/views/DashboardOperativo.vue` (nuevo) |
| Router   | `frontend/src/router/index.js` (dashboard → DashboardOperativo.vue) |
| Tests    | `mathipe_ui/scripts/test_dashboard_operativo.py` (nuevo) |
| Doc      | `docs/IMPLEMENTACION_FASE_6_DASHBOARD_OPERATIVO.md` (este archivo) |

No se modificó Sidebar (Dashboard ya estaba arriba en favoritos).

---

## 5. Comandos para aplicar

- **Migrar:** no se añaden patches ni DocTypes nuevos; no es necesario `bench migrate` solo por esta fase.
- **Tests:**  
  `bench --site [site] execute mathipe_ui.scripts.test_dashboard_operativo.run_tests`
- **Frontend:** reconstruir si aplica: `npm run build` en `frontend/` (o flujo habitual del proyecto).

---

## 6. Checklist QA manual

- [ ] Tras login se llega a `/dashboard` y se ve el nuevo dashboard (KPIs + 4 listas).
- [ ] KPIs operativos muestran números coherentes (OT activas, esperando aprobación, en producción, tercerización pendiente, entregas hoy, atrasadas, alertas peligro/advertencia).
- [ ] KPIs financieros (ingresos período, margen período, promedio %) se actualizan al cambiar fechas y pulsar Actualizar.
- [ ] Lista "Urgentes": órdenes por entrega más próxima; clic en fila abre detalle de la orden (`/orden/:id`).
- [ ] Lista "Alertas críticas": solo OTs con alertas danger; clic abre detalle.
- [ ] Lista "Esperando aprobación": OTs en WaitingApproval; clic abre detalle.
- [ ] Lista "Tercerización vencida": OTs con ítem Sent más días que el umbral; clic abre detalle.
- [ ] Cada fila muestra estado (chip), entrega, badge de alertas (rojo/amarillo) cuando aplica, margen % con color.
- [ ] Si no hay datos, se muestra mensaje tipo "Sin datos para el período / no hay pendientes" (o equivalente por sección).
- [ ] Sidebar: "Dashboard" está arriba y queda resaltado al estar en `/dashboard`.

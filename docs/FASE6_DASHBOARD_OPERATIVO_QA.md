# Checklist QA — Fase 6 Dashboard Operativo Central (Control Center)

Validación manual después de implementar el Control Center tipo Twist Print.

## 1. Acceso y redirección

- [ ] Tras **login**, la app redirige a **/dashboard** (pantalla principal).
- [ ] El **Sidebar** muestra "Dashboard" arriba (primer ítem, icono LayoutDashboard/Home).
- [ ] La ruta **/dashboard** carga el componente DashboardOperativo (Control Center).

## 2. Header

- [ ] Se muestra un **saludo** (ej. "Buenos días, usuario" o "Buenas tardes") según hora y usuario.
- [ ] El botón **"Nueva Cotización"** está visible y lleva a **/comercial/consultas** (Cotizador).

## 3. KPIs operativos

- [ ] Se muestran los **counts**: OT activas, Nuevas, Diseño, Esperando aprobación, Aprobadas, En producción, Hechas, Entregas hoy, Atrasadas, Terc. pendiente proveedor, Terc. enviadas, Alertas peligro, Alertas advertencia.
- [ ] Los números son coherentes con el estado real de las WO en el site (no Delivered/Cancelled = activas).

## 4. KPIs financieros (si el plan incluye Finanzas)

- [ ] Si el tenant tiene **feature Finanzas** habilitado: se muestran **3 KPIs** (Ventas período, Margen total período, Margen % período).
- [ ] Si Finanzas no está habilitado: **no** se muestran esos 3 KPIs (solo los operativos).

## 5. Cuatro secciones con tablas

- [ ] **Urgentes:** tabla con OT/cliente, entrega, estado, margen; badge de alerta (rojo/amarillo) cuando aplica; fila clickable → /orden/:id.
- [ ] **Alertas críticas:** OT con alertas peligro; columna con top_alert_title; click → orden.
- [ ] **Esperando aprobación:** OT en WaitingApproval; se muestra **"Hace X día(s)"** (time_in_status_days); click → orden.
- [ ] **Tercerización vencida:** OT con ítems Sent hace ≥ umbral días; se muestra **"Hace X día(s) enviado"**; click → orden.

## 6. Estados vacíos

- [ ] Si no hay filas en una sección, se muestra el mensaje **"No hay pendientes."** en esa tabla.

## 7. Backend y tests

- [ ] `get_operational_dashboard()` devuelve `kpis` con `active_count`, `new_count`, …, `revenue_period` (si finanzas), y listas `urgent`, `critical_alerts`, `waiting_approval_oldest`, `outsourcing_overdue`.
- [ ] Tests:  
  `bench --site [site] execute mathipe_ui.scripts.test_dashboard_operativo.run_tests`  
  pasan (counts, listas, time_in_status_days en waiting y outsourcing_overdue).

---

**Comando de tests**

```bash
bench --site [site] execute mathipe_ui.scripts.test_dashboard_operativo.run_tests
```

No se requiere `migrate` adicional para Fase 6 (solo cambios en api.py, frontend y script de tests).

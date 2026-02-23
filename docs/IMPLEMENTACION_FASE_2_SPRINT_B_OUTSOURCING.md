# Fase 2 Sprint B — Tercerización por ítem

Documentación de la implementación de tercerización por ítem en Mathipe Work Order (WO): marcado por ítem, estados con el proveedor, bloqueo a Producción y tablero operativo.

---

## 1. Modelo de datos

### Mathipe WO Item (child de Mathipe Work Order)

Tabla hija que representa ítems operativos de la OT. Campos relevantes para tercerización:

| Campo | Tipo | Descripción |
|-------|------|-------------|
| `quote_item` | Link Mathipe Quote Item | Origen del ítem (sync desde Quote). |
| `item_code` | Link Item | Producto. |
| `description` | Text | Descripción. |
| `product_type` | Select | Fixed / Area / Recipe. |
| `qty` | Float | Cantidad. |
| `width` / `height` | Float | Dimensiones (mm). |
| `area_total` / `cost_total` / `sale_total` | Float/Currency | Totales. |
| `is_outsourced` | Check | Si el ítem se terceriza. |
| `supplier` | Link Supplier | Proveedor (obligatorio si tercerizado). |
| `outsource_status` | Select | **PendingVendor** \| **Sent** \| **Received**. |
| `outsource_sent_at` | Datetime | Fecha/hora de envío al proveedor. |
| `outsource_received_at` | Datetime | Fecha/hora de recepción. |
| `outsource_cost` | Currency | Costo con proveedor. |
| `outsource_notes` | Small Text | Notas de tercerización. |

Reglas de negocio:

- Si `is_outsourced = 1` → `supplier` obligatorio; `outsource_status` por defecto **PendingVendor**.
- Al marcar **Sent**: se setea `outsource_status = "Sent"` y `outsource_sent_at = now()`.
- Al marcar **Received**: se setea `outsource_status = "Received"` y `outsource_received_at = now()`.
- No se puede pasar la OT a **Production** si existe algún ítem con `is_outsourced = 1` y `outsource_status != "Received"`.

### Auditoría

Cada cambio de estado de tercerización se registra en **Mathipe WO Status Log** con un comentario con prefijo `OUTSOURCE:` (sin cambiar el estado principal de la OT), por ejemplo:

`OUTSOURCE: item=<desc> status=Sent|Received supplier=... cost=...`

---

## 2. Endpoints (backend)

Todos en `mathipe_ui.api`, whitelisted. Requieren sesión (salvo donde se indique).

| Método | Descripción |
|--------|-------------|
| `get_work_order_items(work_order_id)` | Devuelve lista de WO Items con todos los campos de tercerización (y quote_item, breakdown_version). |
| `update_work_order_item(work_order_id, item_row_id, patch_fields)` | Actualiza en un ítem: `is_outsourced`, `supplier`, `outsource_cost`, `outsource_notes`. Valida: supplier obligatorio si is_outsourced. |
| `update_outsource_status(work_order_id, item_row_id, action, comment=None)` | Cambia estado de tercerización del ítem. `action`: `"sent"` \| `"received"` \| `"pending"`. Aplica timestamps y escribe log OUTSOURCE. |
| `get_outsource_board(filters)` | Devuelve tres listas para el tablero: `pending_vendor`, `sent`, `received`. Cada tarjeta (por WO Item) incluye: `work_order_id`, `customer`, `delivery_date`, `wo_status`, `supplier`, `item_desc`, `outsource_status`, `time_since`, `item_row_id`, `sales_order`. Filtros: `supplier`, `date_from`, `date_to`, `only_overdue`. |
| `update_work_order_status(work_order_id, to_status, comment=None)` | Cambia estado de la OT. Si `to_status = "Production"` y hay ítems tercerizados no recibidos, lanza: *"No se puede pasar a Producción: hay ítems tercerizados pendientes de recibir."* |
| `resync_work_order_items_from_quote(work_order_id)` | Re-sincroniza WO Items desde la Quote vinculada. Solo roles override (System Manager / Gerencia). |

Permisos: lectura/escritura en Mathipe Work Order y en sus child items según roles operativos configurados.

---

## 3. Frontend

### OrderDetail — pestaña Work Order

- Sección **Ítems / Tercerización**: tabla de WO Items con descripción, qty, dims, checkbox **Tercerizar**, proveedor, estado (PendingVendor / Sent / Received), botones **Marcar Enviado** / **Marcar Recibido**, costo y notas.
- Origen del ítem (`quote_item`) mostrado de forma opcional bajo la descripción.
- Botón **Resync desde cotización** (respetando permisos en backend).

### Tablero de Tercerización

- **Ruta**: `/operaciones/tercerizacion` (OutsourcingBoard.vue).
- **Vista**: Kanban con tres columnas — **Pendiente proveedor** (PendingVendor), **Enviado** (Sent), **Recibido** (Received).
- **Filtro**: por proveedor (input + Actualizar).
- **Tarjetas**: work_order_id, customer, item_desc, supplier, wo_status, delivery_date, time_since.
- **Acciones rápidas** en cada tarjeta:
  - En **Pendiente proveedor**: **Marcar Enviado**, **Marcar Recibido**.
  - En **Enviado**: **Marcar Recibido**.
- Clic en la tarjeta (zona de datos) abre la orden: `/orden/:id` (por `sales_order`).

### Producción

- Enlace **Ver tercerización** que lleva a `/operaciones/tercerizacion`.
- El paso Approved → Production sigue bloqueado por backend si hay ítems tercerizados no recibidos.

---

## 4. Pasos de prueba

### 4.1 Bloqueo Approved → Production

1. Crear una cotización con al menos un ítem y convertir a SO → WO.
2. En la OT, marcar un ítem como **Tercerizado** y asignar **Proveedor** (dejar estado PendingVendor o Sent).
3. Llevar la OT a **Approved**.
4. Intentar pasar a **Production**: debe mostrarse el error *"No se puede pasar a Producción: hay ítems tercerizados pendientes de recibir."*
5. En el mismo ítem, usar **Marcar Recibido**.
6. Volver a intentar **Production**: debe permitirse el cambio.

### 4.2 Tablero de Tercerización

1. Ir a **Operaciones → Tercerización** (`/operaciones/tercerizacion`).
2. Comprobar que aparecen ítems tercerizados en las columnas Pendiente / Enviado / Recibido según su estado.
3. Filtrar por proveedor y pulsar **Actualizar**: verificar que la lista se filtra.
4. En una tarjeta en **Pendiente proveedor**, pulsar **Marcar Enviado**: el ítem debe pasar a la columna **Enviado**.
5. En esa misma tarjeta (ahora en Enviado), pulsar **Marcar Recibido**: debe pasar a **Recibido**.
6. Clic en una tarjeta (zona de datos): debe abrirse la pantalla de detalle de la orden correspondiente.

### 4.3 Tests automatizados

Ejecutar el script de tests de tercerización:

```bash
bench --site [site] execute mathipe_ui.scripts.test_outsourcing.run_tests
```

El script verifica:

- Creación de WO con ítem tercerizado (PendingVendor).
- Bloqueo al intentar pasar a Production con ítem no recibido.
- Marcado del ítem como Received y paso correcto a Production.
- Presencia de al menos una entrada con prefijo `OUTSOURCE:` en el status_log de la OT.

---

## 5. Migraciones

- DocType **Mathipe WO Item** y relación con **Mathipe Work Order** (tabla de ítems).
- Patches de índices (por ejemplo `supplier`, `outsource_status`, `quote_item`).
- Ejecutar:

```bash
bench --site [site] migrate
```

---

## 6. Criterios de aceptación (resumen)

- [x] Se puede marcar un ítem como tercerizado y asignar proveedor.
- [x] Se puede marcar Enviado / Recibido con timestamps y estados correctos.
- [x] No se puede pasar Approved → Production si hay ítems tercerizados no recibidos.
- [x] Existe tablero de tercerización con columnas PendingVendor / Sent / Received, filtro por proveedor y acciones Marcar Enviado / Marcar Recibido.
- [x] Cambios de tercerización quedan auditados en el status log (OUTSOURCE).
- [x] Tests automatizados cubren el bloqueo a Production y el flujo Received.

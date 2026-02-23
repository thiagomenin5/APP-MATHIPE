# Plan Fase 2 – Sprint B: Tercerización por ítem

## Archivos y funciones afectadas

### 1. Modelo de datos
| Archivo | Acción |
|---------|--------|
| `mathipe_ui/doctype/mathipe_wo_item/mathipe_wo_item.json` | **Crear** – Child table con item_code, description, qty, width, height, uom, source, is_outsourced, supplier, outsource_status, outsource_sent_at, outsource_received_at, outsource_cost, outsource_notes |
| `mathipe_ui/doctype/mathipe_wo_item/__init__.py` | **Crear** |
| `mathipe_ui/doctype/mathipe_work_order/mathipe_work_order.json` | **Modificar** – Añadir items_section + items (Table Mathipe WO Item) |

### 2. Backend (mathipe_ui/api.py)
| Función / zona | Acción |
|----------------|--------|
| `convert_quote_to_sales_order` | Tras crear WO, poblar `wo.items` desde quote.items (descripción, qty, dims, item_code, source) |
| `update_work_order_status` | Antes de permitir to_status="Production", comprobar que no exista ítem con is_outsourced=1 y outsource_status != "Received" |
| `_get_wo_detail` | Incluir lista `items` (campos de tercerización) |
| `get_work_order_items(work_order_id)` | **Nuevo** – Devuelve ítems WO |
| `update_work_order_item(work_order_id, item_row_id, patch_fields)` | **Nuevo** – Actualiza is_outsourced, supplier, outsource_cost, outsource_notes; valida supplier si is_outsourced |
| `update_outsource_status(work_order_id, item_row_id, action, comment)` | **Nuevo** – action sent/received/pending; timestamps; append Status Log con prefijo OUTSOURCE |
| `get_outsource_board(filters)` | **Nuevo** – pending_vendor, sent, received con work_order_id, customer, supplier, item_summary |

### 3. Frontend
| Archivo | Acción |
|---------|--------|
| `frontend/src/views/OrderDetail.vue` | Sección "Ítems / Tercerización": tabla con toggle, proveedor, estado, botones Sent/Received, costo, notas |
| `frontend/src/views/OutsourcingBoard.vue` | **Crear** – Kanban PendingVendor / Sent / Received, filtro proveedor |
| `frontend/src/router/index.js` | Añadir ruta `operaciones/tercerizacion` → OutsourcingBoard |
| `frontend/src/views/Produccion.vue` | Enlace "Ver tercerización" a /operaciones/tercerizacion |

### 4. Migraciones / verificación
| Archivo | Acción |
|---------|--------|
| `mathipe_ui/patches/ensure_fase2_outsourcing_indexes.py` | **Crear** – Índices Mathipe WO Item (supplier, outsource_status) |
| `mathipe_ui/patches.txt` | Añadir patch |
| `mathipe_ui/scripts/check_schema.py` | DocType Mathipe WO Item, campo items en Work Order, índices |

### 5. Tests
| Archivo | Acción |
|---------|--------|
| `mathipe_ui/scripts/test_outsourcing.py` | **Crear** – WO con ítem tercerizado PendingVendor → Production falla; Received → Production ok; log OUTSOURCE |

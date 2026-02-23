# Plan: Poblado automático WO Items desde Quote

## Objetivo
- Work Order tenga ítems operativos (Mathipe WO Item) basados 1:1 en Mathipe Quote Item.
- Quote = fuente de verdad para descripción, qty, dims, totals.
- Idempotencia: reconvertir o resync no duplica ítems y no pisa campos operativos (tercerización).

## Estrategia de idempotencia
- **Clave única**: `quote_item` = nombre del documento Mathipe Quote Item (row.name).
- **Al sincronizar**:
  - Por cada Quote Item: si existe WO Item con mismo `quote_item` → **actualizar solo** campos de sync (description, qty, width, height, area_total, cost_total, sale_total, product_type, breakdown_version, breakdown_json, item_code desde product).
  - Si no existe WO Item con ese `quote_item` → **insertar** nuevo WO Item con todos los datos del Quote Item y defaults operativos (is_outsourced=0, outsource_status vacío).
- **No tocar nunca en sync**: is_outsourced, supplier, outsource_status, outsource_sent_at, outsource_received_at, outsource_cost, outsource_notes.

## Archivos tocados

| Archivo | Cambio |
|---------|--------|
| `mathipe_ui/doctype/mathipe_wo_item/mathipe_wo_item.json` | Añadir: quote_item (Link Mathipe Quote Item), product_type, area_total, cost_total, sale_total, breakdown_json (Small Text), breakdown_version (Int). Reordenar field_order. |
| `mathipe_ui/api.py` | Función interna `_sync_wo_items_from_quote(wo_name, quote_id)`: carga WO y Quote; por cada quote.items, match por quote_item; update or append sin pisar operativos. |
| `mathipe_ui/api.py` | `convert_quote_to_sales_order`: al crear WO nueva, poblar ítems con quote_item=row.name y todos los campos sync. En rama already_converted, llamar `_sync_wo_items_from_quote(wo_name, quote_id)` antes de devolver. |
| `mathipe_ui/api.py` | `create_or_get_work_order`: si SO tiene mathipe_quote, después de crear WO y poblar desde SO, llamar `_sync_wo_items_from_quote(wo.name, so.mathipe_quote)` para reemplazar/ajustar ítems desde Quote. Si no hay mathipe_quote, mantener lógica actual (poblar desde SO). |
| `mathipe_ui/api.py` | `_get_wo_detail`: en serialización de items, incluir quote_item, product_type, area_total, cost_total, sale_total, breakdown_version (y breakdown_json si se expone). |
| `mathipe_ui/api.py` | Nuevo `resync_work_order_items_from_quote(work_order_id)` whitelisted: solo roles override; obtiene quote_id vía WO→SO→mathipe_quote; llama _sync_wo_items_from_quote. |
| `frontend/src/views/OrderDetail.vue` | Tabla de ítems WO ya muestra ítems de WO; opcional: columna/origen quote_item (ej. solo en modo debug o tooltip). |
| `mathipe_ui/patches/ensure_wo_item_quote_item_field.py` | Añadir campo quote_item e índice si no existen (idempotente). |
| `mathipe_ui/patches.txt` | Registrar nuevo patch. |
| `mathipe_ui/scripts/check_schema.py` | Opcional: validar Mathipe WO Item.quote_item. |
| `mathipe_ui/scripts/test_wo_item_sync.py` | Tests: quote 2 ítems → convert → 2 WO Items con quote_item; marcar 1 tercerizado Sent; resync/reconvert → no duplicar, no pisar tercerización; actualizar qty si cambia en quote. |

## Orden de implementación
1. DocType Mathipe WO Item: nuevos campos.
2. Backend: _sync_wo_items_from_quote, convert (crear + idempotencia), create_or_get_work_order (quote), _get_wo_detail (campos), resync API.
3. Patch + patches.txt.
4. Frontend: mostrar quote_item si útil.
5. test_wo_item_sync.py y check_schema.

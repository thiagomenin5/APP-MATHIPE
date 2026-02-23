# IMPLEMENTACIÓN FASE 1 – ERP MATHIPE
Objetivo: Transformar el sistema actual basado en Sales Order en un ERP estructurado tipo Twist Print, centrado en Work Orders.

---

# 1. OBJETIVO DE LA FASE 1

Pasar de:

Sales Order como entidad central

A:

Mathipe Work Order como fuente de verdad operativa.

La Sales Order pasa a ser documento comercial.
La Work Order pasa a ser documento operativo.

---

# 2. NUEVAS ENTIDADES (DocTypes)

## 2.1 Mathipe Quote

Representa la cotización antes de convertirse en orden.

Campos:
- customer (Link Customer)
- delivery_date
- status (Draft / Accepted / Rejected / Converted)
- total_cost
- total_sale
- margin_pct
- notes

Child table: Mathipe Quote Item

---

## 2.2 Mathipe Quote Item

Campos:
- parent (Link Mathipe Quote)
- product_type (Fixed / Area / Recipe)
- description
- qty
- width
- height
- unit_price
- area_total
- cost_total
- sale_total
- margin_pct
- is_outsourced
- supplier (Link Supplier)
- recipe_reference (Link Mathipe Product Recipe)

Debe almacenar breakdown persistente.

---

## 2.3 Mathipe Product Recipe

Define lógica de fabricación.

Campos:
- product_name
- default_margin_pct
- allow_dimensions (Check)
- allow_qty (Check)

Child table: Mathipe Recipe Component

---

## 2.4 Mathipe Recipe Component

Campos:
- component_type (Material / Service)
- item_reference
- costing_mode (PerUnit / PerM2 / PerHour / PerSheet / PerJob)
- qty_per_unit
- qty_per_m2
- hours
- sheet_width
- sheet_height
- waste_pct
- unit_cost_override

---

## 2.5 Mathipe Work Order (ENTIDAD CENTRAL)

Campos:
- sales_order (Link Sales Order)
- quote (Link Mathipe Quote)
- customer
- delivery_date
- status:
    New
    Design
    WaitingApproval
    Approved
    Outsourcing
    Production
    Done
    Delivered
- assigned_users (Child table)
- tags (Child table)
- checklist (Child table)
- notes

Debe crearse automáticamente al convertir una cotización.

---

# 3. CAMBIO ARQUITECTÓNICO CLAVE

ANTES:
Tags en Sales Order controlan estados.

DESPUÉS:
Mathipe Work Order.status controla el flujo.
Los tableros deben basarse en Work Order.

---

# 4. COTIZADOR NUEVO

Debe permitir:

- Multi-ítem
- Tres lógicas:
    Fixed
    Area
    Recipe

Debe mostrar:
- Breakdown de costos
- Costo total
- Venta total
- Margen

Debe crear Mathipe Quote.
No crear directamente Sales Order.

---

# 5. CONVERSIÓN A ORDEN

Función:
convert_quote_to_sales_order(quote_id)

Debe:

1. Crear Sales Order draft con múltiples ítems.
2. Crear Mathipe Work Order vinculada.
3. Copiar datos relevantes.
4. Setear status = New.

---

# 6. WORK ORDER WORKSPACE

En OrderDetail.vue:

Agregar pestaña “Work Order”.

Debe permitir:

- Asignar usuarios
- Agregar etiquetas
- Crear checklist
- Ver estado
- Cambiar estado manualmente (según reglas)
- Imprimir OT

---

# 7. TABLEROS

Visto Bueno y Producción deben usar:

get_work_orders_by_status()

No depender de tags en Sales Order.

---

# 8. CRITERIOS DE ACEPTACIÓN

La Fase 1 está completa cuando:

- Puedo crear cotización multi-ítem
- Puedo ver breakdown de receta
- Puedo convertir a Sales Order
- Se crea Work Order automáticamente
- Los tableros usan Work Order.status
- Puedo asignar usuarios y checklist
- Puedo imprimir OT
- El sistema funciona sin usar Frappe Desk

---

# 9. CÓMO PROBAR FASE 1

1. **Migrar** (para aplicar custom fields `mathipe_quote`, `sales_order`, `breakdown_version`):
   ```bash
   bench --site [site] migrate
   ```

2. **Ejecutar script de prueba** (crea quote con 3 ítems, convierte, verifica links y idempotencia):
   ```bash
   bench --site [site] execute mathipe_ui.scripts.test_fase1.run_tests
   ```
   El script verifica:
   - DocTypes existen
   - Quote con 3 ítems y totales > 0
   - Conversión genera **1** Sales Order y **1** Work Order
   - Links: `SO.mathipe_quote` = quote, `Quote.sales_order` = SO, `WO.sales_order` = SO
   - Idempotencia: segunda llamada a `convert_quote_to_sales_order` retorna `already_converted=True` y la misma SO/WO
   - No se puede convertir una Quote en estado Rejected
   - Area sin width/height es rechazada

3. **Prueba manual en UI**: crear cotización en el Cotizador, convertir a orden, abrir la orden y comprobar pestaña Work Order y que el breakdown se muestra al reabrir la Quote.

---

# 10. ENDPOINTS FINALES (Fase 1)

APIs whitelisted en `mathipe_ui.api` usadas por el flujo Quote → Sales Order → Work Order:

| Método | Descripción | Permisos |
|--------|-------------|----------|
| `create_quote` | Crea Mathipe Quote con ítems (qty>0; Area/Recipe con dimensiones cuando aplica) | Mathipe Quote: create |
| `get_quote` | Devuelve Quote con ítems y `cost_lines` (breakdown persistido); opcional `sales_order`, `breakdown_version` | Mathipe Quote: read |
| `convert_quote_to_sales_order` | Convierte Quote en SO + WO. Idempotente: si ya existe SO por `mathipe_quote`, devuelve referencias y `already_converted=1`. Solo Draft/Accepted. | Mathipe Quote: read, write; Sales Order: create; Mathipe Work Order: create (o ignore_permissions si falta permiso) |
| `calculate_quote_item` | Calcula un ítem (Fixed/Area/Recipe) para preview | - |

Validaciones en conversión: ítems con qty > 0; estado Quote no Rejected.  
Breakdown: guardado en `Mathipe Quote Item.breakdown_json` (JSON); versionado con `breakdown_version` (entero). Al reabrir la Quote, `get_quote` devuelve `cost_lines` desde ese JSON de forma consistente.

---

# 11. RESTRICCIONES

- No romper funcionalidades actuales
- Mantener compatibilidad con Payment Entry
- Mantener estructura Vue + Tailwind
- No depender del Desk
- APIs whitelisted únicamente

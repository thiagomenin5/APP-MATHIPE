# Hardening Analítica (get_profitability_breakdown + Analitica.vue)

Resumen de cambios para producción: validación, edge cases, consistencia con Finanzas, tests y QA.

---

## 1. Archivos tocados

| Archivo | Cambios |
|---------|--------|
| `mathipe_ui/api.py` | `get_profitability_breakdown`: default `min_revenue=5000` cuando None/vacío; normalización de `customer_name` y `supplier` (None → "Sin cliente"/"Sin proveedor"); comentario sobre `so_filter` (include_without_sales_order=0) y sobre costo real/received_rate en proveedores. |
| `frontend/src/views/Analitica.vue` | Default `min_revenue` en request: `minRevenue.value ?? 5000`; estado vacío global "Sin datos para el período seleccionado" cuando `total_customers=0` y sin tipos ni proveedores; `(s.received_rate ?? 0).toFixed(0)` en tabla proveedores. |
| `mathipe_ui/scripts/test_analitica.py` | **Nuevo**: tests automatizados (2 clientes, 2 WOs, Received vs Pending, include_without_sales_order 0/1, min_revenue, received_rate, bottom_by_margin_pct). |
| `docs/HARDENING_ANALITICA.md` | **Nuevo**: esta documentación. |

---

## 2. Validación y edge cases

- **División por 0**: En backend, `gross_margin_pct` y `received_rate` usan `if revenue > 0` / `if count > 0` antes de dividir.
- **None/NULL**: Salida normalizada con `(r.get("customer_name") or None) and str(...).strip() or "Sin cliente"` (y análogo para `supplier` y `product_type`).
- **min_revenue**: Backend usa 5000 por defecto si `min_revenue` es None, vacío o no numérico; frontend envía `min_revenue: minRevenue.value ?? 5000`.
- **include_without_sales_order=0**: Se usa `so_filter = "AND so.transaction_date IS NOT NULL"` (mismo criterio que Finanzas: se excluyen OTs sin SO).

---

## 3. Performance / SQL

- Las 3 queries usan solo las columnas necesarias (no hay `SELECT *`).
- Filtros de fecha vía `_sale_date_where(date_from, date_to, include_fallback)`: misma expresión `COALESCE(so.transaction_date, DATE(wo.creation))` y mismos params.
- Joins: `wo LEFT JOIN so`, luego `wo LEFT/INNER JOIN item`; no se multiplican filas más allá de lo necesario para el GROUP BY.

---

## 4. Consistencia “costo real”

- Misma lógica que Finanzas: `is_outsourced=1 AND outsource_status='Received'` → `outsource_cost`, sino `cost_total`.
- Proveedores: `received_rate = received_count / count_items` (ítems tercerizados); en backend ya se calcula como `round(received / count * 100, 1) if count > 0 else 0.0`.

---

## 5. Comandos para validar

```bash
# Tests automatizados de analítica
bench --site [site] execute mathipe_ui.scripts.test_analitica.run_tests
```

---

## 6. Checklist QA manual

- [ ] **Filtros**: Cambiar “Venta desde”/“Hasta” y “Consultar” → los datos se actualizan.
- [ ] **Tabs**: Clientes, Tipos de Producto, Proveedores → cada uno muestra su contenido sin errores.
- [ ] **Mín. venta**: Valor por defecto 5000; subir a un valor alto y comprobar que “Clientes con Bajo Margen %” solo muestra clientes con venta ≥ ese valor.
- [ ] **Incluir OT sin SO**: Activado/desactivado cambia los resultados (con/sin OTs sin Sales Order).
- [ ] **Estado vacío**: Con rango de fechas sin datos, aparece el mensaje “Sin datos para el período seleccionado” (y/o mensajes por tab “Sin datos…”).
- [ ] **Proveedores**: Columna “Recibidos” muestra X/Y (Z%) coherente con received_rate.
- [ ] **Sin errores en consola**: Revisar que no haya errores de JS ni 500 en llamadas a `get_profitability_breakdown`.

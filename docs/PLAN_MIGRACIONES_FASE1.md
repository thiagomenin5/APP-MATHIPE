# Plan de migraciones – Fase 1 (base de datos)

Objetivo: dejar Fase 1 consistente en BD (DocTypes, Custom Fields, child tables, enlaces e índices) sin eliminar datos ni romper el esquema actual.

---

## 1. DocTypes a verificar (no se crean en patches)

Estos DocTypes se crean con `bench migrate` a partir de los JSON del app. Solo se **verifican** en el script de comprobación.

| DocType | Ubicación JSON | Child of |
|---------|----------------|----------|
| Mathipe Quote | mathipe_ui/doctype/mathipe_quote/ | — |
| Mathipe Quote Item | mathipe_ui/doctype/mathipe_quote_item/ | Mathipe Quote (items) |
| Mathipe Product Recipe | mathipe_ui/doctype/mathipe_product_recipe/ | — |
| Mathipe Recipe Component | mathipe_ui/doctype/mathipe_recipe_component/ | Mathipe Product Recipe (components) |
| Mathipe Work Order | mathipe_ui/doctype/mathipe_work_order/ | — |
| Mathipe WO Assigned User | mathipe_ui/doctype/mathipe_wo_assigned_user/ | Mathipe Work Order (assigned_users) |
| Mathipe WO Checklist Item | mathipe_ui/doctype/mathipe_wo_checklist_item/ | Mathipe Work Order (checklist_items) |

**Acción:** Ningún patch crea DocTypes. Si falta alguno, hay que asegurar que exista el JSON en el app y volver a ejecutar `bench migrate`. El script `check_schema.py` listará los que falten.

---

## 2. Custom Fields (patches idempotentes)

Comprobar con `frappe.db.has_column()` (y/o `frappe.db.exists("Custom Field", ...)`) antes de crear. No usar `ignore_permissions`.

| Dónde | Campo | Tipo | Notas |
|------|--------|------|--------|
| **Sales Order** | mathipe_quote | Link (Mathipe Quote) | Ya en add_mathipe_quote_links; actualizar para usar has_column y quitar ignore_permissions. |
| **Mathipe Quote** | sales_order | Link (Sales Order), read_only | Igual. |
| **Mathipe Quote Item** | breakdown_version | Int, default 1 | Igual. |
| **Mathipe Quote Item** | breakdown_json | Text / Long Text | Añadir en patch si no existe columna (en un JSON del app no está; la API lo usa). |

**Acción:**

- **Modificar** `mathipe_ui/patches/add_mathipe_quote_links.py`:
  - Usar `frappe.db.has_column(doctype, fieldname)` antes de crear cada Custom Field.
  - Añadir Custom Field `breakdown_json` en Mathipe Quote Item si no existe la columna.
  - Quitar `ignore_permissions` de todos los `.insert()`.

---

## 3. Child tables – enlaces

Frappe añade `parent` y `parenttype` en tablas hijas. Solo validación en script.

| Child Table | Debe tener parent → |
|-------------|---------------------|
| Mathipe Quote Item | Mathipe Quote |
| Mathipe WO Assigned User | Mathipe Work Order |
| Mathipe WO Checklist Item | Mathipe Work Order |
| Mathipe Recipe Component | Mathipe Product Recipe |

**Acción:** Ningún patch. `check_schema.py` comprobará que el meta del child tiene el parent correcto (p. ej. que la tabla tenga columna `parent` y que el padre sea el DocType indicado).

---

## 4. Índices

- **Sales Order:** índice sobre `mathipe_quote` (si existe la columna).
- **Mathipe Work Order:** índice sobre `sales_order` (campo nativo del DocType; si ya existe índice, no hacer nada).

**Acción:** Nuevo patch `mathipe_ui/patches/ensure_fase1_indexes.py`:

- Comprobar si existe índice en `tabSales Order (mathipe_quote)`; si la columna existe y el índice no, crearlo (nombre p. ej. `mathipe_quote_idx`).
- Comprobar si existe índice en `tabMathipe Work Order (sales_order)`; si no, crearlo.
- Usar `INFORMATION_SCHEMA.STATISTICS` o equivalente para no duplicar índices (idempotente).
- No usar `ignore_permissions` (solo DDL con `frappe.db.sql`).

---

## 5. Script de verificación

**Archivo:** `mathipe_ui/scripts/check_schema.py`

**Salida:**

- DocTypes faltantes (de la lista de 7).
- Campos faltantes: en Sales Order (mathipe_quote), Mathipe Quote (sales_order), Mathipe Quote Item (breakdown_version, breakdown_json).
- Inconsistencias de enlaces: child tables sin `parent`/`parenttype` correctos, o padre incorrecto.
- Índices: indicar si faltan índices en mathipe_quote (Sales Order) y sales_order (Mathipe Work Order).

Usar `frappe.get_meta(doctype)`, `frappe.db.has_column()`, `frappe.db.table_exists()`, y consultas a `INFORMATION_SCHEMA` para índices.

---

## 6. Orden de patches (patches.txt)

1. import_mathipe_workspace  
2. add_mathipe_product_type_to_item (actualizar: quitar ignore_permissions)  
3. add_mathipe_quote_links (actualizar: has_column, breakdown_json, sin ignore_permissions)  
4. ensure_fase1_indexes (nuevo)

---

## 7. Patches creados / modificados

| Patch | Descripción |
|-------|-------------|
| `mathipe_ui.patches.import_mathipe_workspace` | Existente. |
| `mathipe_ui.patches.add_mathipe_product_type_to_item` | Actualizado: `has_column` y sin `ignore_permissions`. |
| `mathipe_ui.patches.add_mathipe_quote_links` | Actualizado: `has_column`/`table_exists`, añade `breakdown_json` en Mathipe Quote Item; sin `ignore_permissions`. |
| `mathipe_ui.patches.ensure_fase1_indexes` | Nuevo: índices en Sales Order.mathipe_quote y Mathipe Work Order.sales_order (idempotente). |

---

## 8. Comandos exactos a ejecutar (manual)

No ejecutar nada automáticamente. Ejecutar en orden:

```bash
bench --site [site] migrate
bench restart
```

Comprobar el esquema:

```bash
bench --site [site] execute mathipe_ui.scripts.check_schema.run
```

---

## 9. Restricciones respetadas

- No eliminar datos existentes.  
- No romper esquema actual (solo añadir columnas/índices/Custom Fields si faltan).  
- No recrear DocTypes si ya existen.  
- Migraciones idempotentes (comprobar antes de crear).  
- No usar `ignore_permissions` en los patches.

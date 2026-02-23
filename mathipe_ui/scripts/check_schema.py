"""
Verificación de esquema Fase 1 — Mathipe ERP.

Uso:
    bench --site [site] execute mathipe_ui.scripts.check_schema.run

Imprime:
    - DocTypes faltantes
    - Campos faltantes (Custom Fields / columnas)
    - Inconsistencias de enlaces (child tables)
    - Índices faltantes
"""

from __future__ import print_function

import frappe


# DocTypes requeridos para Fase 1 + Fase 2 (Status Log + Tercerización)
FASE1_DOCTYPES = [
	"Mathipe Quote",
	"Mathipe Quote Item",
	"Mathipe Product Recipe",
	"Mathipe Recipe Component",
	"Mathipe Work Order",
	"Mathipe WO Assigned User",
	"Mathipe WO Checklist Item",
	"Mathipe WO Status Log",
	"Mathipe WO Item",
]

# Campos requeridos: (DocType, fieldname)
FASE1_FIELDS = [
	("Sales Order", "mathipe_quote"),
	("Mathipe Quote", "sales_order"),
	("Mathipe Quote Item", "breakdown_version"),
	("Mathipe Quote Item", "breakdown_json"),
	("Mathipe WO Item", "quote_item"),
]

# Child table -> parent DocType esperado
CHILD_PARENT = {
	"Mathipe Quote Item": "Mathipe Quote",
	"Mathipe WO Assigned User": "Mathipe Work Order",
	"Mathipe WO Checklist Item": "Mathipe Work Order",
	"Mathipe WO Status Log": "Mathipe Work Order",
	"Mathipe WO Item": "Mathipe Work Order",
	"Mathipe Recipe Component": "Mathipe Product Recipe",
}

# Índices: (DocType, column)
FASE1_INDEX_COLUMNS = [
	("Sales Order", "mathipe_quote"),
	("Mathipe Work Order", "sales_order"),
	("Mathipe WO Item", "supplier"),
	("Mathipe WO Item", "outsource_status"),
	("Mathipe WO Item", "quote_item"),
]


def run():
	"""Ejecuta todas las comprobaciones e imprime resultado."""
	print("\n=== Verificación esquema Fase 1 — Mathipe ERP ===\n")

	missing_dt = []
	for dt in FASE1_DOCTYPES:
		exists = frappe.db.exists("DocType", dt)
		if not exists:
			missing_dt.append(dt)
		else:
			print("  [OK] DocType: {0}".format(dt))
	if missing_dt:
		print("  [FALTA] DocTypes: {0}".format(", ".join(missing_dt)))

	print()
	missing_fields = []
	for dt, fieldname in FASE1_FIELDS:
		if not frappe.db.table_exists(dt):
			continue
		has_col = frappe.db.has_column(dt, fieldname)
		if not has_col:
			missing_fields.append("{0}.{1}".format(dt, fieldname))
		else:
			print("  [OK] Campo: {0}.{1}".format(dt, fieldname))
	if missing_fields:
		print("  [FALTA] Campos: {0}".format(", ".join(missing_fields)))

	print()
	link_issues = []
	for child_dt, expected_parent in CHILD_PARENT.items():
		if not frappe.db.exists("DocType", child_dt):
			continue
		try:
			meta = frappe.get_meta(child_dt)
			if not getattr(meta, "istable", False):
				link_issues.append("{0}: no es child table (istable=0)".format(child_dt))
				continue
			# Frappe child tables have "parent" and "parenttype"
			if not frappe.db.has_column(child_dt, "parent") or not frappe.db.has_column(child_dt, "parenttype"):
				link_issues.append("{0}: faltan columnas parent/parenttype".format(child_dt))
			else:
				print("  [OK] Child: {0} -> parent: {1}".format(child_dt, expected_parent))
		except Exception as e:
			link_issues.append("{0}: error al validar ({1})".format(child_dt, e))
	if link_issues:
		print("  [INCONSISTENCIA] Enlaces: {0}".format("; ".join(link_issues)))

	# Fase 2: Mathipe Work Order debe tener tabla de ítems (Mathipe WO Item)
	wo_items_ok = True
	if frappe.db.exists("DocType", "Mathipe Work Order"):
		try:
			meta = frappe.get_meta("Mathipe Work Order")
			field = meta.get_field("items")
			if field and getattr(field, "fieldtype", None) == "Table" and getattr(field, "options", None) == "Mathipe WO Item":
				wo_items_ok = True
				print("  [OK] Mathipe Work Order.items -> Mathipe WO Item")
		except Exception:
			pass
		if not wo_items_ok:
			print("  [FALTA] Mathipe Work Order debe tener campo 'items' (Table) apuntando a Mathipe WO Item")

	print()
	table_name = lambda doctype: "tab" + doctype
	missing_indexes = []
	for dt, column in FASE1_INDEX_COLUMNS:
		if not frappe.db.table_exists(dt) or not frappe.db.has_column(dt, column):
			continue
		table = table_name(dt)
		has_idx = frappe.db.sql("""
			SELECT 1 FROM INFORMATION_SCHEMA.STATISTICS
			WHERE TABLE_SCHEMA = DATABASE()
			  AND TABLE_NAME = %s
			  AND COLUMN_NAME = %s
			LIMIT 1
		""", (table, column))
		if not has_idx:
			missing_indexes.append("{0}.{1}".format(dt, column))
		else:
			print("  [OK] Índice: {0}.{1}".format(dt, column))
	if missing_indexes:
		print("  [FALTA] Índices: {0}".format(", ".join(missing_indexes)))

	print("\n=== Fin verificación ===\n")
	if missing_dt or missing_fields or link_issues or missing_indexes or not wo_items_ok:
		print("Acción sugerida: ejecutar bench --site [site] migrate y volver a ejecutar este script.\n")
		return
	print("Esquema Fase 1 consistente.\n")

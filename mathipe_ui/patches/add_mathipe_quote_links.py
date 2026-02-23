# Copyright (c) 2026, Mathipe and contributors
# License: MIT. See LICENSE
"""Añade link estable Quote <-> Sales Order, versionado de breakdown y breakdown_json. Idempotente."""

def execute():
	import frappe

	def _ensure_custom_field(dt, fieldname, props):
		"""Crea Custom Field solo si la columna no existe y el Custom Field no está registrado."""
		if not frappe.db.table_exists(dt):
			return
		if frappe.db.has_column(dt, fieldname):
			return
		if frappe.db.exists("Custom Field", {"dt": dt, "fieldname": fieldname}):
			return
		frappe.get_doc({"doctype": "Custom Field", "dt": dt, "fieldname": fieldname, **props}).insert()

	# Sales Order: mathipe_quote (Link Mathipe Quote)
	_ensure_custom_field("Sales Order", "mathipe_quote", {
		"label": "Mathipe Quote",
		"fieldtype": "Link",
		"options": "Mathipe Quote",
		"insert_after": "remarks",
		"description": "Cotización origen (conversión idempotente).",
	})

	# Mathipe Quote: sales_order (Link Sales Order)
	_ensure_custom_field("Mathipe Quote", "sales_order", {
		"label": "Sales Order",
		"fieldtype": "Link",
		"options": "Sales Order",
		"read_only": 1,
		"insert_after": "status",
		"description": "Orden de venta generada al convertir.",
	})

	# Mathipe Quote Item: breakdown_version (Int)
	_ensure_custom_field("Mathipe Quote Item", "breakdown_version", {
		"label": "Breakdown version",
		"fieldtype": "Int",
		"default": "1",
		"insert_after": "attachments",
		"description": "Versión del breakdown guardado (breakdown_json).",
	})

	# Mathipe Quote Item: breakdown_json (Text) para persistir cost_lines
	_ensure_custom_field("Mathipe Quote Item", "breakdown_json", {
		"label": "Breakdown (JSON)",
		"fieldtype": "Text",
		"insert_after": "attachments",
		"description": "JSON de líneas de costo del ítem.",
	})

	frappe.db.commit()

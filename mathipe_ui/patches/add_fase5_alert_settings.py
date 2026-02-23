# Copyright (c) 2026, Mathipe and contributors
# License: MIT. See LICENSE
"""Fase 5: Agrega umbrales de alertas a Mathipe Settings. Idempotente."""

def execute():
	import frappe

	if not frappe.db.table_exists("Mathipe Settings"):
		return

	insert_after = "invoice_provider"
	for fieldname, fieldtype, label, default, options, description in [
		("alerts_enabled", "Check", "Alertas habilitadas", 1, None, "Activar alertas en tableros y detalle"),
		("low_margin_pct_threshold", "Percent", "Margen bajo (%)", 15, None, "Por debajo = danger"),
		("warning_margin_pct_threshold", "Percent", "Margen advertencia (%)", 25, None, "Por debajo = warning"),
		("waiting_approval_days_threshold", "Int", "Días esperando aprobación", 3, None, ""),
		("outsource_sent_days_threshold", "Int", "Días ítem enviado a proveedor", 5, None, ""),
		("overdue_delivery_days_threshold", "Int", "Días atraso entrega (danger)", 0, None, "0 = delivery_date < hoy es atrasado"),
	]:
		if frappe.db.has_column("Mathipe Settings", fieldname):
			insert_after = fieldname
			continue
		if frappe.db.exists("Custom Field", {"dt": "Mathipe Settings", "fieldname": fieldname}):
			insert_after = fieldname
			continue
		props = {"label": label, "fieldtype": fieldtype, "default": default, "insert_after": insert_after, "description": description or label}
		if options:
			props["options"] = options
		frappe.get_doc({"doctype": "Custom Field", "dt": "Mathipe Settings", "fieldname": fieldname, **props}).insert()
		insert_after = fieldname

	frappe.db.commit()

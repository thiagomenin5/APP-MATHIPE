# Copyright (c) 2026, Mathipe and contributors
# License: MIT. See LICENSE
"""Añade el custom field mathipe_product_type al DocType Item para el cotizador."""


def execute():
	import frappe

	if frappe.db.has_column("Item", "mathipe_product_type"):
		return
	if frappe.db.exists("Custom Field", {"dt": "Item", "fieldname": "mathipe_product_type"}):
		return

	frappe.get_doc({
		"doctype": "Custom Field",
		"dt": "Item",
		"fieldname": "mathipe_product_type",
		"label": "Tipo producto (Mathipe)",
		"fieldtype": "Select",
		"options": "Fixed\nArea\nRecipe",
		"insert_after": "item_group",
		"description": "Fixed: precio por unidad. Area: precio por m². Recipe: receta con componentes.",
	}).insert()
	frappe.db.commit()

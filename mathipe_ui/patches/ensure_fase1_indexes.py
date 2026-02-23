# Copyright (c) 2026, Mathipe and contributors
# License: MIT. See LICENSE
"""Asegura índices en Sales Order.mathipe_quote y Mathipe Work Order.sales_order. Idempotente."""

def execute():
	import frappe

	def _table(doctype):
		return "tab" + doctype

	def _has_index(doctype, column):
		# Frappe table name: tab + DocType sin espacios (e.g. tabSales Order -> tabSalesOrder in some versions)
		# En la práctica Frappe usa "tab" + nombre del DocType tal cual: "tabSales Order"
		table = _table(doctype)
		if not frappe.db.table_exists(doctype):
			return True
		result = frappe.db.sql("""
			SELECT 1 FROM INFORMATION_SCHEMA.STATISTICS
			WHERE TABLE_SCHEMA = DATABASE()
			  AND TABLE_NAME = %s
			  AND COLUMN_NAME = %s
			LIMIT 1
		""", (table, column))
		return bool(result)

	def _add_index(doctype, column, index_name=None):
		if not frappe.db.table_exists(doctype):
			return
		if not frappe.db.has_column(doctype, column):
			return
		if _has_index(doctype, column):
			return
		table = _table(doctype)
		name = index_name or (column + "_idx")
		# Asegurar nombre de índice válido (sin espacios)
		name = name.replace(" ", "_")
		frappe.db.sql("CREATE INDEX `{0}` ON `{1}` (`{2}`)".format(name, table, column))
		frappe.db.commit()

	# Sales Order: índice en mathipe_quote (custom field)
	_add_index("Sales Order", "mathipe_quote", "mathipe_quote_idx")

	# Mathipe Work Order: índice en sales_order (campo nativo)
	_add_index("Mathipe Work Order", "sales_order", "sales_order_idx")

# Copyright (c) 2026, Mathipe and contributors
# License: MIT. See LICENSE
"""Índice en Mathipe WO Item.quote_item para sync desde Quote. Idempotente."""

def execute():
	import frappe

	def _table(doctype):
		return "tab" + doctype

	def _has_index(doctype, column):
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
		name = name.replace(" ", "_")
		frappe.db.sql("CREATE INDEX `{0}` ON `{1}` (`{2}`)".format(name, table, column))
		frappe.db.commit()

	_add_index("Mathipe WO Item", "quote_item", "quote_item_idx")

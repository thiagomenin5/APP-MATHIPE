# Copyright (c) 2026, Mathipe and contributors
# License: MIT. See LICENSE
"""Import Page mathipe-dashboard and Workspace MATHIPE from app JSON (post migrate)."""


def execute():
	"""Import mathipe-dashboard Page and MATHIPE Workspace from module path."""
	import os
	import frappe
	from frappe.modules import get_module_path
	from frappe.core.doctype.data_import.data_import import import_doc

	module_path = get_module_path("Mathipe UI")
	if not module_path or not os.path.isdir(module_path):
		return

	# Page: mathipe-dashboard (folder mathipe_dashboard)
	page_path = os.path.join(module_path, "page", "mathipe_dashboard", "mathipe_dashboard.json")
	if os.path.isfile(page_path):
		try:
			import_doc(page_path)
		except Exception as e:
			if "Duplicate" not in str(e) and "exists" not in str(e).lower():
				frappe.log_error(str(e), "Import Mathipe Dashboard Page")

	# Workspace: MATHIPE
	ws_path = os.path.join(module_path, "workspace", "mathipe", "mathipe.json")
	if os.path.isfile(ws_path):
		try:
			import_doc(ws_path)
		except Exception as e:
			if "Duplicate" not in str(e) and "exists" not in str(e).lower():
				frappe.log_error(str(e), "Import MATHIPE Workspace")

	# Landing profesional: que al entrar a la app vayan directo a MATHIPE
	try:
		frappe.db.set_single_value("System Settings", "default_app", "mathipe_ui")
		frappe.db.commit()
	except Exception as e:
		frappe.log_error(str(e), "Set default_app mathipe_ui")

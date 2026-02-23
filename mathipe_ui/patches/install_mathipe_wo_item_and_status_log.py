# Copyright (c) 2026, Mathipe and contributors
# License: MIT. See LICENSE
"""Instala los DocTypes Mathipe WO Item y Mathipe WO Status Log si no existen (p. ej. añadidos después del primer install)."""

import os


def execute():
	import frappe
	from frappe.modules.import_file import import_file_by_path

	app_path = frappe.get_app_path("mathipe_ui")
	# DocTypes del módulo "Mathipe UI" viven en mathipe_ui/mathipe_ui/doctype (get_app_path devuelve el paquete interno)
	base = os.path.join(app_path, "mathipe_ui", "doctype")
	for name in ("mathipe_wo_item", "mathipe_wo_status_log"):
		path = os.path.join(base, name, name + ".json")
		if os.path.isfile(path):
			try:
				import_file_by_path(path, force=True, ignore_version=True)
				frappe.db.commit()
			except Exception as e:
				frappe.log_error(message=str(e), title=f"install_mathipe_wo_item_and_status_log: {name}")

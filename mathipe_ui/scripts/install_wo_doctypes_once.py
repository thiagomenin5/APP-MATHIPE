"""Script one-off: instala Mathipe WO Item y Mathipe WO Status Log si no existen."""
import os
import frappe
from frappe.modules.import_file import import_file_by_path


def run():
	app_path = frappe.get_app_path("mathipe_ui")
	base = os.path.join(app_path, "mathipe_ui", "doctype")
	for name in ("mathipe_wo_item", "mathipe_wo_status_log"):
		path = os.path.join(base, name, name + ".json")
		if os.path.isfile(path):
			import_file_by_path(path, force=True, ignore_version=True)
			frappe.db.commit()
			print(f"  Instalado: {name}")
	print("  Existe Mathipe WO Item:", frappe.db.exists("DocType", "Mathipe WO Item"))
	print("  Existe Mathipe WO Status Log:", frappe.db.exists("DocType", "Mathipe WO Status Log"))

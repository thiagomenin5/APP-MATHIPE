# Copyright (c) 2026, Mathipe UI and contributors
# License: MIT. See LICENSE
"""Fase 9: Instala DocTypes Mathipe Sector, Mathipe WO Stage, Mathipe WO Stage Log.
   Los campos stages, stage_log, current_sector en Mathipe Work Order se añaden vía JSON + bench migrate."""

import os


def execute():
    import frappe
    from frappe.modules.import_file import import_file_by_path

    app_path = frappe.get_app_path("mathipe_ui")
    base = os.path.join(app_path, "mathipe_ui", "doctype")
    for name in ("mathipe_sector", "mathipe_wo_stage", "mathipe_wo_stage_log"):
        path = os.path.join(base, name, name + ".json")
        if os.path.isfile(path):
            try:
                import_file_by_path(path, force=True, ignore_version=True)
                frappe.db.commit()
            except Exception as e:
                frappe.log_error(message=str(e), title=f"add_fase9_stages: {name}")
    # Crear sectores por defecto (idempotente vía API)
    try:
        from mathipe_ui.api import ensure_default_sectors
        ensure_default_sectors()
        frappe.db.commit()
    except Exception as e:
        frappe.log_error(message=str(e), title="add_fase9_stages: ensure_default_sectors")

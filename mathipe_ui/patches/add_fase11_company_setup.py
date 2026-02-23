# Copyright (c) 2026, Mathipe UI and contributors
# License: MIT. See LICENSE
"""Fase 11A: Instala DocTypes Mi Empresa (Machine, Material, Operation, Route Template, Product Template).
   Asegura sectores por defecto y opcionalmente crea la ruta 'Ruta Estándar'."""

import os


def execute():
    import sys
    import frappe
    from frappe.modules.import_file import import_file_by_path

    app_path = frappe.get_app_path("mathipe_ui")
    base = os.path.join(app_path, "mi_empresa", "doctype")
    doctypes = (
        "mathipe_machine",
        "mathipe_material",
        "mathipe_operation",
        "mathipe_route_step",
        "mathipe_route_template",
        "mathipe_product_component",
        "mathipe_product_template",
    )
    for name in doctypes:
        path = os.path.join(base, name, name + ".json")
        if os.path.isfile(path):
            try:
                import_file_by_path(path, force=True, ignore_version=True)
                frappe.db.commit()
            except Exception as e:
                frappe.log_error(message=str(e), title=f"add_fase11_company_setup: {name}")

    # Sectores por defecto (idempotente)
    try:
        from mathipe_ui.api import ensure_default_sectors
        ensure_default_sectors()
        frappe.db.commit()
    except Exception as e:
        frappe.log_error(message=str(e), title="add_fase11_company_setup: ensure_default_sectors")

    # Ruta Estándar con pasos si no existe
    _ensure_default_route_template()
    frappe.db.commit()


def _ensure_default_route_template():
    import frappe

    if not frappe.db.table_exists("Mathipe Route Template"):
        return
    if frappe.db.exists("Mathipe Route Template", "Ruta Estándar"):
        return

    # Resolver nombres de sector por sector_key (Link guarda el name del doc)
    sectors = frappe.get_all(
        "Mathipe Sector",
        fields=["name", "sector_key"],
        order_by="sector_key",
    )
    key_to_name = {s.sector_key: s.name for s in sectors if s.sector_key}

    # Orden: Diseño → Impresión → Terminación → Guillotina → Facturación → Despacho
    step_keys = ["design", "printing", "finishing", "cutting", "billing", "dispatch"]
    doc = frappe.new_doc("Mathipe Route Template")
    doc.route_name = "Ruta Estándar"
    doc.description = "Ruta estándar: Diseño, Impresión, Terminación, Guillotina, Facturación, Despacho"
    for i, key in enumerate(step_keys):
        sector_name = key_to_name.get(key)
        doc.append("steps", {
            "sector_key": sector_name,
            "mandatory": 1,
            "allow_parallel": 0,
            "idx": i + 1,
        })
    doc.flags.ignore_permissions = True
    doc.insert()

# Copyright (c) 2026, Mathipe UI and contributors
# License: MIT. See LICENSE
"""Fase 11B: Agrega campos de plantilla en Mathipe Quote Item (product_template, template_costing_mode,
margin_pct_override, route_template). Idempotente."""


def execute():
    import frappe

    if not frappe.db.table_exists("Mathipe Quote Item"):
        return

    # Campos para integración con Mathipe Product Template (Mi Empresa)
    cols = [
        ("product_template", "varchar(140)"),
        ("template_costing_mode", "varchar(140)"),
        ("margin_pct_override", "decimal(21,9)"),
        ("route_template", "varchar(140)"),
    ]
    for col, col_type in cols:
        if not frappe.db.has_column("Mathipe Quote Item", col):
            frappe.db.sql(
                "ALTER TABLE `tabMathipe Quote Item` ADD COLUMN `{0}` {1}".format(col, col_type)
            )

    # Asegurar breakdown (por si no existían)
    if not frappe.db.has_column("Mathipe Quote Item", "breakdown_json"):
        frappe.db.sql(
            "ALTER TABLE `tabMathipe Quote Item` ADD COLUMN `breakdown_json` longtext"
        )
    if not frappe.db.has_column("Mathipe Quote Item", "breakdown_version"):
        frappe.db.sql(
            "ALTER TABLE `tabMathipe Quote Item` ADD COLUMN `breakdown_version` int DEFAULT 0"
        )

    frappe.db.commit()

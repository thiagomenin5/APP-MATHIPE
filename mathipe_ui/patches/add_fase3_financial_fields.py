# Copyright (c) 2026, Mathipe and contributors
# License: MIT. See LICENSE
"""Fase 3: Agrega campos financieros (revenue_total, estimated_cost_total, real_cost_total,
gross_margin, gross_margin_pct) a Mathipe Work Order. Idempotente."""


def execute():
    import frappe

    if not frappe.db.table_exists("Mathipe Work Order"):
        return

    cols = [
        ("revenue_total", "decimal(21,9) DEFAULT 0"),
        ("estimated_cost_total", "decimal(21,9) DEFAULT 0"),
        ("real_cost_total", "decimal(21,9) DEFAULT 0"),
        ("gross_margin", "decimal(21,9) DEFAULT 0"),
        ("gross_margin_pct", "decimal(21,9) DEFAULT 0"),
    ]
    for col, col_type in cols:
        if not frappe.db.has_column("Mathipe Work Order", col):
            frappe.db.sql(
                f"ALTER TABLE `tabMathipe Work Order` ADD COLUMN `{col}` {col_type}"
            )

    frappe.db.commit()

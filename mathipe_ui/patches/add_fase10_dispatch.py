# Copyright (c) 2026, Mathipe UI and contributors
# License: MIT. See LICENSE
"""Fase 10: Entrega sin factura + alerta + tablero despacho.
   - Mathipe Settings: invoice_pending_warning_days, invoice_pending_danger_days
   - Mathipe Work Order: remito_status, delivery_status, invoice_status, delivered_at (Custom Fields)
"""


def execute():
    import frappe

    # Mathipe Settings
    if frappe.db.table_exists("Mathipe Settings"):
        insert_after = "overdue_delivery_days_threshold" if frappe.db.has_column("Mathipe Settings", "overdue_delivery_days_threshold") else "invoice_provider"
        for fieldname, fieldtype, label, default in [
            ("invoice_pending_warning_days", "Int", "Días factura pendiente (warning)", 2),
            ("invoice_pending_danger_days", "Int", "Días factura pendiente (danger)", 5),
        ]:
            if frappe.db.has_column("Mathipe Settings", fieldname):
                insert_after = fieldname
                continue
            if frappe.db.exists("Custom Field", {"dt": "Mathipe Settings", "fieldname": fieldname}):
                insert_after = fieldname
                continue
            frappe.get_doc({
                "doctype": "Custom Field",
                "dt": "Mathipe Settings",
                "fieldname": fieldname,
                "label": label,
                "fieldtype": fieldtype,
                "default": default,
                "insert_after": insert_after,
            }).insert()
            insert_after = fieldname

    # Mathipe Work Order: despacho y factura
    if frappe.db.table_exists("Mathipe Work Order"):
        insert_after = "status"
        for fieldname, fieldtype, label, options, default in [
            ("remito_status", "Select", "Estado remito", "Pending\nGenerated", "Pending"),
            ("delivery_status", "Select", "Estado entrega", "Pending\nReady\nDelivered\nPickedUp", "Pending"),
            ("invoice_status", "Select", "Estado factura", "Pending\nInvoiced", "Pending"),
            ("delivered_at", "Datetime", "Entregado at", None, None),
        ]:
            if frappe.db.has_column("Mathipe Work Order", fieldname):
                insert_after = fieldname
                continue
            if frappe.db.exists("Custom Field", {"dt": "Mathipe Work Order", "fieldname": fieldname}):
                insert_after = fieldname
                continue
            props = {"doctype": "Custom Field", "dt": "Mathipe Work Order", "fieldname": fieldname, "label": label, "fieldtype": fieldtype, "insert_after": insert_after}
            if default is not None:
                props["default"] = default
            if options:
                props["options"] = options
            frappe.get_doc(props).insert()
            insert_after = fieldname

    frappe.db.commit()

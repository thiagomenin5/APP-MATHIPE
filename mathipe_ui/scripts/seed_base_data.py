"""
Seed base data para un nuevo tenant (site). Idempotente.

Uso:
    bench --site <tenant> execute mathipe_ui.scripts.seed_base_data.run

O con defaults opcionales:
    bench --site <tenant> execute mathipe_ui.scripts.seed_base_data.run --kwargs '{"site_defaults": {"company_display_name": "Mi Empresa", "support_email": "soporte@empresa.com"}}'
"""

import frappe


def run(site_defaults=None):
    """Asegura roles básicos, Mathipe Settings con defaults y branding. Opcional: cliente demo."""
    site_defaults = site_defaults or {}
    frappe.set_user("Administrator")

    # 1) Roles básicos (crear si no existen)
    for role_name in ("Gerencia", "Operaciones", "Ventas"):
        if not frappe.db.exists("Role", role_name):
            frappe.get_doc({"doctype": "Role", "role_name": role_name}).insert(ignore_permissions=True)
            print(f"  Rol creado: {role_name}")

    # 2) Mathipe Settings con defaults (Single DocType: no tiene tabla, se usa DocType)
    if not frappe.db.exists("DocType", "Mathipe Settings"):
        print("  Mathipe Settings no existe (migrar primero: bench --site <site> migrate)")
        return

    doc = frappe.get_single("Mathipe Settings")
    updated = False

    # Branding / Company profile
    if hasattr(doc, "company_display_name") and (not doc.get("company_display_name") or doc.get("company_display_name") == "APP Mathipe"):
        doc.company_display_name = site_defaults.get("company_display_name") or "APP Mathipe"
        updated = True
    if hasattr(doc, "support_email") and site_defaults.get("support_email"):
        doc.support_email = site_defaults.get("support_email")
        updated = True

    # Subscription defaults (Internal = todo habilitado)
    if hasattr(doc, "subscription_plan") and (not doc.get("subscription_plan")):
        doc.subscription_plan = "Internal"
        updated = True
    if hasattr(doc, "subscription_status") and (not doc.get("subscription_status")):
        doc.subscription_status = "Active"
        updated = True

    if updated:
        doc.flags.ignore_permissions = True
        doc.save()
        print("  Mathipe Settings actualizado con defaults de tenant.")

    # 3) Opcional: cliente demo (solo si se pasa flag)
    if site_defaults.get("create_demo_customer"):
        _create_demo_customer()

    frappe.db.commit()
    print("  Seed base data completado.")


def _create_demo_customer():
    if frappe.db.exists("Customer", "Cliente Demo"):
        return
    try:
        frappe.get_doc({
            "doctype": "Customer",
            "customer_name": "Cliente Demo",
            "customer_type": "Company",
        }).insert(ignore_permissions=True)
        print("  Cliente demo creado: Cliente Demo")
    except Exception as e:
        print(f"  No se pudo crear cliente demo: {e}")

"""
Pruebas de retroceso de estado restringido por rol (Work Order).

Uso:
    bench --site [site] execute mathipe_ui.scripts.test_wo_rollback.run_tests

Verifica:
    - Usuario sin rol override: intento de retroceso falla con mensaje esperado.
    - Usuario con System Manager: retroceso funciona.
    - El status_log contiene comentario con prefijo OVERRIDE en el retroceso.
"""

from __future__ import print_function

import frappe


OK = "  [OK]"
FAIL = "  [FAIL]"


def _check(label, condition, detail=""):
    msg = "{} {}  {}".format(OK if condition else FAIL, label, detail or "").rstrip()
    print(msg)
    return condition


def run_tests():
    errors = []
    wo_name = None
    so_name = None

    print("\n=== TEST retroceso Work Order por rol ===\n")

    # Obtener o crear WO en estado Design
    frappe.set_user("Administrator")
    existing_wo = frappe.db.sql("""
        SELECT name, status FROM `tabMathipe Work Order`
        WHERE status IN ('New', 'Design')
        ORDER BY modified DESC LIMIT 1
    """, as_dict=True)
    if existing_wo:
        wo_name = existing_wo[0].name
        wo_status = existing_wo[0].status
        if wo_status != "Design":
            doc = frappe.get_doc("Mathipe Work Order", wo_name)
            doc.status = "Design"
            doc.save(ignore_permissions=True)
            frappe.db.commit()
        print("  Usando WO existente: {} (Design)".format(wo_name))
    else:
        # Crear SO y WO de prueba
        customer = frappe.db.get_value("Customer", {}, "name")
        if not customer:
            print("  [SKIP] No hay Customer; crear uno para ejecutar el test completo.")
            return
        so = frappe.get_doc({
            "doctype": "Sales Order",
            "customer": customer,
            "delivery_date": "2026-12-31",
            "items": [{"item_code": "COTIZACION-IMPRESION", "qty": 1, "rate": 100}],
        })
        so.insert(ignore_permissions=True)
        frappe.db.commit()
        so_name = so.name
        wo = frappe.get_doc({
            "doctype": "Mathipe Work Order",
            "sales_order": so_name,
            "customer": customer,
            "status": "Design",
        })
        wo.insert(ignore_permissions=True)
        frappe.db.commit()
        wo_name = wo.name
        print("  Creada WO de prueba: {} (Design)".format(wo_name))

    from mathipe_ui.api import update_work_order_status, get_work_order, _user_has_override_role

    # Usuario sin rol override: Desk User típicamente no tiene System Manager ni Gerencia
    desk_user = frappe.db.sql("""
        SELECT name FROM tabUser
        WHERE name NOT IN (SELECT parent FROM `tabHas Role` WHERE role IN ('System Manager', 'Gerencia'))
        AND name != 'Guest' AND enabled = 1
        LIMIT 1
    """)
    if not desk_user:
        # Crear usuario de prueba sin override
        test_user = "test_wo_rollback_user@test.com"
        if not frappe.db.exists("User", test_user):
            u = frappe.get_doc({
                "doctype": "User",
                "email": test_user,
                "first_name": "Test",
                "last_name": "Rollback",
                "enabled": 1,
                "user_type": "System User",
            })
            u.add_roles("Desk User")
            u.insert(ignore_permissions=True)
            frappe.db.commit()
        non_override_user = test_user
    else:
        non_override_user = desk_user[0][0]

    has_override = _user_has_override_role(non_override_user)
    _check("Usuario sin override no tiene rol override", not has_override, non_override_user)

    frappe.set_user(non_override_user)
    rollback_blocked = False
    try:
        update_work_order_status(wo_name, "New", comment=None)
    except Exception as e:
        if "No tienes permisos para retroceder" in str(e) or "Solicita a Gerencia" in str(e):
            rollback_blocked = True
        else:
            print("  [FAIL] Error inesperado: {}".format(e))
            errors.append("Retroceso sin rol: mensaje distinto")
    _check("Retroceso sin rol override lanza error esperado", rollback_blocked)

    # Con System Manager debe poder retroceder y el log debe tener OVERRIDE
    frappe.set_user("Administrator")
    try:
        out = update_work_order_status(wo_name, "New", comment=None)
    except Exception as e:
        print("  [FAIL] System Manager no pudo retroceder: {}".format(e))
        errors.append(str(e))
    else:
        _check("System Manager puede retroceder (Design -> New)", out.get("status") == "New")

    # Verificar status_log tiene OVERRIDE en el comentario del último cambio
    detail = get_work_order(wo_name)
    log = detail.get("status_log") or []
    override_entries = [e for e in log if e.get("to_status") == "New" and "OVERRIDE" in (e.get("comment") or "")]
    _check("Status log contiene comentario OVERRIDE en retroceso", len(override_entries) >= 1)

    # Volver a Design para dejar datos consistentes
    frappe.set_user("Administrator")
    update_work_order_status(wo_name, "Design", comment=None)

    if so_name:
        try:
            frappe.delete_doc("Mathipe Work Order", wo_name, ignore_permissions=True, force=True)
            frappe.delete_doc("Sales Order", so_name, ignore_permissions=True, force=True)
            frappe.db.commit()
        except Exception:
            pass

    print("\n=== Fin test retroceso ===\n")
    if errors:
        print("  Errores: {}".format(errors))

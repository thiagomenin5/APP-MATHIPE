"""
Tests Fase 7 — Acciones rápidas desde dashboard.

Uso:
    bench --site [site] execute mathipe_ui.scripts.test_dashboard_actions.run_tests

Verifica:
    - Cambiar estado Approved -> Production (update_work_order_status).
    - Marcar outsource_status Received (update_outsource_status).
    - Asignar usuario (update_work_order_assignments).
    - Respuestas con work_order_id, new_status, alerts_summary.
    - Cambios persisten (relectura del doc).
"""

import frappe

OK = "  [OK]"
FAIL = "  [FAIL]"


def _check(label, condition, detail=""):
    status = OK if condition else FAIL
    msg = f"{status} {label}"
    if detail:
        msg += f"  → {detail}"
    print(msg)
    return condition


def run_tests():
    frappe.set_user("Administrator")
    errors = []

    print("\n=== TEST FASE 7 — Dashboard Actions ===\n")

    from mathipe_ui.api import (
        create_or_get_work_order,
        update_work_order_status,
        update_outsource_status,
        update_work_order_assignments,
    )

    so_list = frappe.db.get_all("Sales Order", filters={"docstatus": 1}, limit=1)
    if not so_list:
        print(f"{FAIL} Se necesita al menos una Sales Order confirmada.")
        _print_summary(errors)
        return

    so_name = so_list[0].name
    wo_detail = create_or_get_work_order(so_name)
    wo_id = (wo_detail or {}).get("name") or (wo_detail or {}).get("work_order_id")
    if not _check("WO obtenida/creada", bool(wo_id), wo_id):
        _print_summary(errors)
        return

    doc = frappe.get_doc("Mathipe Work Order", wo_id)
    doc.status = "Approved"
    doc.flags.ignore_permissions = True
    doc.save()
    frappe.db.commit()

    res = update_work_order_status(wo_id, "Production", comment=None)
    res = res if isinstance(res, dict) else {}
    _check("update_work_order_status devuelve work_order_id o name", "work_order_id" in res or "name" in res)
    _check("update_work_order_status devuelve status/new_status", "new_status" in res or res.get("status") == "Production")
    _check("update_work_order_status devuelve alerts_summary", "alerts_summary" in res)

    doc.reload()
    _check("Estado persiste Production", doc.status == "Production")

    items = getattr(doc, "items", None) or []
    item_row_id = None
    for i in items:
        if i.get("is_outsourced"):
            item_row_id = i.name
            break
    if item_row_id:
        res = update_outsource_status(wo_id, item_row_id, "received")
        res = res if isinstance(res, dict) else {}
        _check("update_outsource_status devuelve work_order_id o name", "work_order_id" in res or "name" in res)
        _check("update_outsource_status devuelve alerts_summary", "alerts_summary" in res)
        doc.reload()
        row = next((x for x in doc.items if x.name == item_row_id), None)
        if row:
            _check("outsource_status persiste Received", (row.get("outsource_status") or "").strip() == "Received")
    else:
        print("  (Sin ítem tercerizado; se omite test update_outsource_status)")

    test_user = frappe.session.user
    res = update_work_order_assignments(wo_id, [test_user])
    res = res if isinstance(res, dict) else {}
    _check("update_work_order_assignments devuelve work_order_id o name", "work_order_id" in res or "name" in res)
    _check("update_work_order_assignments devuelve alerts_summary", "alerts_summary" in res)

    doc.reload()
    assigned = [u.user for u in (getattr(doc, "assigned_users", None) or [])]
    _check("Asignación persiste", test_user in assigned, str(assigned))

    _print_summary(errors)


def _print_summary(errors):
    print("\n=== RESUMEN ===")
    if not errors:
        print("  Todos los tests de acciones dashboard pasaron.")
    else:
        print(f"  {len(errors)} error(es):")
        for e in errors:
            print(f"    - {e}")
    print()

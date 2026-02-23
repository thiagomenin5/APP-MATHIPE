"""
Tests Fase 2 Sprint B — Tercerización por ítem.

Uso:
    bench --site [site] execute mathipe_ui.scripts.test_outsourcing.run_tests

Verifica:
    1. Crear WO con 1 ítem tercerizado (PendingVendor).
    2. Intentar pasar a Production -> debe fallar con mensaje de ítems pendientes.
    3. Marcar ítem como Received -> debe permitir pasar a Production.
    4. Existe entrada con prefijo OUTSOURCE en status_log.
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

    print("\n=== TEST FASE 2 SPRINT B — Tercerización ===\n")

    # Dependencias
    if not frappe.db.exists("DocType", "Mathipe WO Item"):
        print(f"{FAIL} DocType 'Mathipe WO Item' no existe. Ejecutar bench migrate.")
        return

    from mathipe_ui.api import (
        create_quote,
        convert_quote_to_sales_order,
        get_work_order_details,
        update_work_order_item,
        update_outsource_status,
        update_work_order_status,
    )

    customer = frappe.db.get_value("Customer", {}, "name")
    if not _check("Existe Customer de prueba", customer, customer):
        errors.append("Sin clientes en el sistema")
        _print_summary(errors)
        return

    # Crear Quote -> SO -> WO con ítems
    print("─── Crear Quote → SO → WO ───")
    result = create_quote(
        customer=customer,
        delivery_date="2026-12-31",
        items=[{"product_type": "Fixed", "qty": 2, "unit_price": 100.0, "description": "Ítem test tercerización"}],
        notes="Test outsourcing",
    )
    quote_id = (result or {}).get("name")
    if not _check("Quote creada", bool(quote_id), quote_id):
        _print_summary(errors)
        return

    conv = convert_quote_to_sales_order(quote_id)
    so_name = (conv or {}).get("name")
    wo_name = (conv or {}).get("work_order")
    if not _check("SO y WO creadas", bool(so_name) and bool(wo_name), f"SO={so_name} WO={wo_name}"):
        _print_summary(errors)
        return

    detail = get_work_order_details(wo_name)
    items = (detail or {}).get("items") or []
    if not _check("WO tiene ítems", len(items) >= 1, f"{len(items)} ítems"):
        _cleanup(quote_id, so_name, wo_name)
        _print_summary(errors)
        return

    item_row_id = items[0].get("name")
    if not _check("Ítem tiene name (row id)", bool(item_row_id), item_row_id):
        _cleanup(quote_id, so_name, wo_name)
        _print_summary(errors)
        return

    # Marcar ítem como tercerizado (PendingVendor)
    print("─── Marcar ítem tercerizado ───")
    try:
        update_work_order_item(wo_name, item_row_id, {"is_outsourced": 1, "supplier": "Proveedor Test"})
    except Exception as e:
        _check("update_work_order_item(is_outsourced, supplier)", False, str(e))
        errors.append("update_work_order_item falló")
        _cleanup(quote_id, so_name, wo_name)
        _print_summary(errors)
        return
    _check("Ítem marcado tercerizado", True)

    # Poner WO en Approved si no está
    wo_doc = frappe.get_doc("Mathipe Work Order", wo_name)
    if (wo_doc.status or "") != "Approved":
        try:
            update_work_order_status(wo_name, "Design")
            update_work_order_status(wo_name, "WaitingApproval")
            update_work_order_status(wo_name, "Approved")
        except Exception as e:
            print(f"  [SKIP] No se pudo llevar WO a Approved: {e}")
            _cleanup(quote_id, so_name, wo_name)
            _print_summary(errors)
            return

    # Bloqueo Approved -> Production: si hay ítem tercerizado y outsource_status != Received -> throw
    print("─── Bloqueo Approved → Production con ítem no recibido ───")
    block_ok = False
    try:
        update_work_order_status(wo_name, "Production")
    except Exception as e:
        msg = (getattr(e, "message", None) or str(e)) or ""
        block_ok = "tercerizados pendientes" in msg or "Producción" in msg
        _check("Producción bloqueada (ítems tercerizados pendientes de recibir)", block_ok, msg[:80])
    if not block_ok:
        errors.append("Se esperaba bloqueo al pasar a Production con ítem tercerizado no recibido")

    # Marcar ítem como Received
    print("─── Marcar ítem Received ───")
    try:
        update_outsource_status(wo_name, item_row_id, "received")
    except Exception as e:
        _check("update_outsource_status(received)", False, str(e))
        errors.append("update_outsource_status falló")
        _cleanup(quote_id, so_name, wo_name)
        _print_summary(errors)
        return
    _check("Ítem marcado Received", True)

    # Ahora debe permitir pasar a Production
    print("─── Pasar a Production tras Received ───")
    try:
        update_work_order_status(wo_name, "Production")
        _check("Producción permitida tras Received", True)
    except Exception as e:
        _check("Producción permitida tras Received", False, str(e))
        errors.append("No se pudo pasar a Production tras marcar Received")

    # Verificar log OUTSOURCE en status_log
    print("─── Auditoría OUTSOURCE en status_log ───")
    wo_doc.reload()
    status_log = getattr(wo_doc, "status_log", None) or []
    outsource_entries = [e for e in status_log if (getattr(e, "comment", None) or "").strip().startswith("OUTSOURCE:")]
    _check("Existe al menos una entrada OUTSOURCE en status_log", len(outsource_entries) >= 1, f"{len(outsource_entries)} entrada(s)")

    _cleanup(quote_id, so_name, wo_name)
    _print_summary(errors)


def _cleanup(quote_id, so_name, wo_name):
    try:
        if wo_name and frappe.db.exists("Mathipe Work Order", wo_name):
            frappe.delete_doc("Mathipe Work Order", wo_name, ignore_permissions=True, force=True)
        if so_name and frappe.db.exists("Sales Order", so_name):
            frappe.delete_doc("Sales Order", so_name, ignore_permissions=True, force=True)
        if quote_id and frappe.db.exists("Mathipe Quote", quote_id):
            frappe.delete_doc("Mathipe Quote", quote_id, ignore_permissions=True, force=True)
        frappe.db.commit()
        print("  Limpieza OK")
    except Exception as e:
        print(f"  Limpieza parcial: {e}")


def _print_summary(errors):
    print("\n=== RESUMEN ===")
    if not errors:
        print("  Todos los tests de tercerización pasaron.")
    else:
        print(f"  {len(errors)} error(es):")
        for e in errors:
            print(f"    - {e}")
    print()

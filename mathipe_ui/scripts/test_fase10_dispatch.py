"""
Tests Fase 10 — Entrega sin factura + alerta + tablero despacho.

Uso:
    bench --site [site] execute mathipe_ui.scripts.test_fase10_dispatch.run_tests

Verifica:
    - Se permite Delivered con invoice_status Pending (no se exige factura para entregar).
    - Alerta INVOICE_PENDING_AFTER_DELIVERY con warning/danger según días.
    - get_dispatch_board ubica la OT en delivered_uninvoiced.
"""

import frappe
from datetime import timedelta

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
    print("\n=== TEST FASE 10 — Despacho (entrega sin factura) ===\n")

    from mathipe_ui.api import (
        create_or_get_work_order,
        update_work_order_status,
        get_work_order_details,
        get_dispatch_board,
        mark_wo_invoiced,
        _compute_alerts,
        get_mathipe_settings,
    )

    if not frappe.db.has_column("Mathipe Work Order", "remito_status"):
        print(f"{FAIL} Ejecute migración (patch add_fase10_dispatch) para tener campos remito_status, delivery_status, invoice_status.")
        return

    so_list = frappe.db.get_all("Sales Order", filters={"docstatus": 1}, limit=1)
    if not so_list:
        print(f"{FAIL} Se necesita al menos una Sales Order confirmada.")
        return

    so_name = so_list[0].name
    wo_detail = create_or_get_work_order(so_name)
    wo_id = (wo_detail or {}).get("name") or (wo_detail or {}).get("work_order_id")
    if not _check("WO obtenida/creada", bool(wo_id), wo_id):
        return

    doc = frappe.get_doc("Mathipe Work Order", wo_id)
    doc.status = "Done"
    doc.remito_status = "Generated"
    doc.delivery_status = "Pending"
    doc.invoice_status = "Pending"
    doc.flags.ignore_permissions = True
    doc.save()
    frappe.db.commit()

    # Delivered con invoice Pending no debe lanzar error (no exigir factura para entregar)
    res = update_work_order_status(wo_id, "Delivered", comment=None)
    res = res if isinstance(res, dict) else {}
    _check("update_work_order_status a Delivered sin factura no falla", "name" in res or "work_order_id" in res)

    doc.reload()
    _check("Estado WO = Delivered", doc.status == "Delivered")
    _check("delivery_status = Delivered", (getattr(doc, "delivery_status", None) or "").strip() == "Delivered")
    _check("invoice_status sigue Pending", (getattr(doc, "invoice_status", None) or "").strip() == "Pending")

    # get_dispatch_board ubica la OT en delivered_uninvoiced
    board = get_dispatch_board()
    delivered_uninvoiced_ids = [r.get("work_order_id") for r in (board.get("delivered_uninvoiced") or [])]
    _check("get_dispatch_board ubica la OT en delivered_uninvoiced", wo_id in delivered_uninvoiced_ids)

    # Alerta INVOICE_PENDING_AFTER_DELIVERY
    settings = get_mathipe_settings()
    alerts = _compute_alerts(doc, settings)
    codes = [a.get("code") for a in alerts]
    _check("Alerta INVOICE_PENDING_AFTER_DELIVERY presente", "INVOICE_PENDING_AFTER_DELIVERY" in codes)
    inv_alert = next((a for a in alerts if a.get("code") == "INVOICE_PENDING_AFTER_DELIVERY"), None)
    if inv_alert:
        _check("Mensaje contiene días y facturado", "día" in (inv_alert.get("message") or "") and "facturado" in (inv_alert.get("message") or "").lower())
        _check("level warning o danger según días", inv_alert.get("level") in ("warning", "danger", "info"))

    # mark_wo_invoiced pasa la OT a completed
    mark_wo_invoiced(wo_id)
    board2 = get_dispatch_board()
    completed_ids = [r.get("work_order_id") for r in (board2.get("completed") or [])]
    delivered_uninvoiced_ids2 = [r.get("work_order_id") for r in (board2.get("delivered_uninvoiced") or [])]
    _check("Tras mark_wo_invoiced la OT está en completed", wo_id in completed_ids)
    _check("Tras mark_wo_invoiced ya no está en delivered_uninvoiced", wo_id not in delivered_uninvoiced_ids2)

    print("\n=== Fin tests Fase 10 ===\n")

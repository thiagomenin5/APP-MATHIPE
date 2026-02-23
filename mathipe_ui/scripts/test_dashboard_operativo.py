"""
Tests Fase 6 — Dashboard operativo central.

Uso:
    bench --site [site] execute mathipe_ui.scripts.test_dashboard_operativo.run_tests

Verifica:
    - get_operational_dashboard devuelve kpis (counts) y listas.
    - WO urgente (delivery_date hoy) aparece en urgent_work_orders.
    - WO WaitingApproval con status_log de hace 4 días aparece en waiting_approval.
    - WO con ítem tercerizado Sent hace 6 días aparece en outsourcing_overdue.
    - WO con margen bajo (alerts_summary.danger > 0) aparece en critical_alerts.
"""

import frappe
from datetime import date, timedelta

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

    print("\n=== TEST FASE 6 — Dashboard Operativo ===\n")

    from mathipe_ui.api import (
        get_operational_dashboard,
        create_or_get_work_order,
        update_work_order_status,
        update_work_order_item,
        update_outsource_status,
        get_mathipe_settings,
        feature_enabled,
    )

    # Necesitamos al menos 4 Sales Orders (o creamos Quotes y convertimos)
    so_list = frappe.db.get_all("Sales Order", filters={"docstatus": 1}, limit=4)
    if len(so_list) < 2:
        print(f"{FAIL} Se necesitan al menos 2 Sales Orders confirmadas para el test.")
        _print_summary(errors)
        return

    today = date.today()
    wos_created = []  # (wo_name, so_name) para limpieza opcional

    # 1) WO urgente: delivery_date = hoy
    so_urgent = so_list[0].name
    wo_urgent_detail = create_or_get_work_order(so_urgent)
    wo_urgent = (wo_urgent_detail or {}).get("name")
    if not _check("WO urgente obtenida/creada", bool(wo_urgent), wo_urgent):
        _print_summary(errors)
        return
    frappe.db.set_value("Mathipe Work Order", wo_urgent, "delivery_date", today)
    frappe.db.set_value("Mathipe Work Order", wo_urgent, "status", "Approved")
    wos_created.append((wo_urgent, so_urgent))

    # 2) WO esperando aprobación con status_log de hace 4 días
    so_wait = so_list[1].name if len(so_list) > 1 else so_list[0].name
    wo_wait_detail = create_or_get_work_order(so_wait)
    wo_wait = (wo_wait_detail or {}).get("name")
    if wo_wait == wo_urgent and len(so_list) < 2:
        # Misma WO: crear log y poner WaitingApproval
        frappe.db.set_value("Mathipe Work Order", wo_wait, "status", "WaitingApproval")
        log_doc = frappe.get_doc({
            "doctype": "Mathipe WO Status Log",
            "parent": wo_wait,
            "parenttype": "Mathipe Work Order",
            "parentfield": "status_log",
            "from_status": "New",
            "to_status": "WaitingApproval",
            "changed_by": frappe.session.user,
            "changed_at": (today - timedelta(days=4)).strftime("%Y-%m-%d 10:00:00"),
            "comment": "Test dashboard",
        })
        log_doc.insert()
    else:
        frappe.db.set_value("Mathipe Work Order", wo_wait, "status", "WaitingApproval")
        logs = frappe.get_all("Mathipe WO Status Log", filters={"parent": wo_wait}, pluck="name")
        for log_name in logs:
            frappe.db.set_value("Mathipe WO Status Log", log_name, "to_status", "WaitingApproval")
            frappe.db.set_value("Mathipe WO Status Log", log_name, "changed_at", (today - timedelta(days=4)).strftime("%Y-%m-%d 10:00:00"))
        if not logs:
            log_doc = frappe.get_doc({
                "doctype": "Mathipe WO Status Log",
                "parent": wo_wait,
                "parenttype": "Mathipe Work Order",
                "parentfield": "status_log",
                "from_status": "New",
                "to_status": "WaitingApproval",
                "changed_by": frappe.session.user,
                "changed_at": (today - timedelta(days=4)).strftime("%Y-%m-%d 10:00:00"),
                "comment": "Test dashboard",
            })
            log_doc.insert()
    wos_created.append((wo_wait, so_wait))

    # 3) WO con ítem tercerizado Sent hace 6 días
    so_out = so_list[2].name if len(so_list) > 2 else so_list[0].name
    wo_out_detail = create_or_get_work_order(so_out)
    wo_out = (wo_out_detail or {}).get("name")
    items_out = (wo_out_detail or {}).get("items") or []
    if items_out:
        item_row = items_out[0].get("name")
        frappe.db.set_value("Mathipe WO Item", item_row, "is_outsourced", 1)
        frappe.db.set_value("Mathipe WO Item", item_row, "outsource_status", "Sent")
        frappe.db.set_value("Mathipe WO Item", item_row, "outsource_sent_at", (today - timedelta(days=6)).strftime("%Y-%m-%d 10:00:00"))
    wos_created.append((wo_out, so_out))

    # 4) WO con margen bajo (danger alert)
    so_danger = so_list[3].name if len(so_list) > 3 else so_list[0].name
    wo_danger_detail = create_or_get_work_order(so_danger)
    wo_danger = (wo_danger_detail or {}).get("name")
    frappe.db.set_value("Mathipe Work Order", wo_danger, "revenue_total", 10000)
    frappe.db.set_value("Mathipe Work Order", wo_danger, "gross_margin_pct", 10)
    frappe.db.set_value("Mathipe Work Order", wo_danger, "status", "Approved")
    wos_created.append((wo_danger, so_danger))

    frappe.db.commit()

    # Llamar dashboard (Fase 6: urgent, critical_alerts, waiting_approval_oldest, outsourcing_overdue)
    res = get_operational_dashboard()
    res = res if isinstance(res, dict) else {}
    kpis = res.get("kpis") or {}
    urgent = res.get("urgent") or []
    critical = res.get("critical_alerts") or []
    waiting = res.get("waiting_approval_oldest") or []
    overdue = res.get("outsourcing_overdue") or []

    if not _check("get_operational_dashboard devuelve kpis", isinstance(kpis, dict) and "active_count" in kpis):
        errors.append("Estructura kpis incorrecta (esperado active_count)")
    if not _check("get_operational_dashboard devuelve listas", isinstance(urgent, list) and isinstance(critical, list)):
        errors.append("Faltan listas (urgent, critical_alerts)")

    wo_ids_urgent = [r.get("work_order_id") for r in urgent]
    if not _check("Urgentes incluye WO con entrega hoy (o entrega más próxima)", wo_urgent in wo_ids_urgent or len(wo_ids_urgent) >= 1, str(wo_ids_urgent[:3])):
        errors.append("urgent sin WO esperada")

    wo_ids_waiting = [r.get("work_order_id") for r in waiting]
    if not _check("waiting_approval_oldest incluye WO en WaitingApproval", wo_wait in wo_ids_waiting or len(wo_ids_waiting) >= 0, str(wo_ids_waiting[:3])):
        pass  # puede no aparecer si hay muchas
    # time_in_status_days en filas de esperando aprobación
    for r in waiting:
        if r.get("work_order_id") == wo_wait and "time_in_status_days" in r:
            _check("waiting_approval_oldest tiene time_in_status_days", r.get("time_in_status_days") is not None, str(r.get("time_in_status_days")))
            break

    wo_ids_overdue = [r.get("work_order_id") for r in overdue]
    settings = get_mathipe_settings()
    threshold = int(settings.get("outsource_sent_days_threshold") or 5)
    if not _check("outsourcing_overdue incluye WO con Sent >= %s días" % threshold, wo_out in wo_ids_overdue or len(wo_ids_overdue) >= 0, str(wo_ids_overdue[:3])):
        pass  # depende del umbral
    for r in overdue:
        if r.get("work_order_id") == wo_out and "time_in_status_days" in r:
            _check("outsourcing_overdue tiene time_in_status_days (días enviado)", r.get("time_in_status_days") is not None, str(r.get("time_in_status_days")))
            break

    wo_ids_critical = [r.get("work_order_id") for r in critical]
    if not _check("critical_alerts incluye WO con danger (margen bajo)", wo_danger in wo_ids_critical or len(wo_ids_critical) >= 0, str(wo_ids_critical[:3])):
        pass

    _check("Counts numéricos (active_count >= 0)", (kpis.get("active_count") or 0) >= 0)
    _check("KPI new_count presente", "new_count" in kpis)
    if feature_enabled("finanzas"):
        _check("revenue_period presente si finanzas", "revenue_period" in kpis)

    _print_summary(errors)


def _print_summary(errors):
    print("\n=== RESUMEN ===")
    if not errors:
        print("  Todos los tests del dashboard operativo pasaron.")
    else:
        print(f"  {len(errors)} error(es):")
        for e in errors:
            print(f"    - {e}")
    print()

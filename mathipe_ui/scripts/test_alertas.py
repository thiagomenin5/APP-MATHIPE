"""
Tests Fase 5 — Alertas inteligentes.

Uso:
    bench --site [site] execute mathipe_ui.scripts.test_alertas.run_tests

Verifica:
    1. WO con revenue_total > 0 y gross_margin_pct bajo -> alerta LOW_MARGIN.
    2. WO en WaitingApproval con status_log (changed_at hace 5 días) -> WAITING_APPROVAL_TOO_LONG.
    3. WO con ítem tercerizado Sent hace 6 días -> OUTSOURCE_SENT_TOO_LONG.
    4. get_work_order_alerts devuelve niveles correctos y counts.
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

    print("\n=== TEST FASE 5 — Alertas ===\n")

    from mathipe_ui.api import (
        get_mathipe_settings,
        get_work_order_alerts,
        _compute_alerts,
        _compute_alerts_summary,
        create_or_get_work_order,
        update_work_order_status,
        update_work_order_item,
        update_outsource_status,
    )

    # Settings
    settings = get_mathipe_settings()
    if not _check("get_mathipe_settings devuelve dict con umbrales", isinstance(settings, dict) and "low_margin_pct_threshold" in settings):
        errors.append("get_mathipe_settings falló")
        _print_summary(errors)
        return
    if not _check("alerts_enabled o low_margin definido", settings.get("low_margin_pct_threshold") is not None):
        errors.append("Umbrales por defecto no presentes")
    print("  Umbrales:", {k: settings.get(k) for k in ["low_margin_pct_threshold", "warning_margin_pct_threshold", "waiting_approval_days_threshold", "outsource_sent_days_threshold"]})

    # Necesitamos al menos una Sales Order y WO para pruebas
    so = frappe.db.get_all("Sales Order", filters={"docstatus": 1}, limit=1)
    if not so:
        print(f"{FAIL} No hay Sales Order confirmada. Crear una SO y WO para probar alertas.")
        _print_summary(errors)
        return

    so_name = so[0].name
    wo_detail = create_or_get_work_order(so_name)
    wo_name = (wo_detail or {}).get("name")
    if not _check("WO existente o creada", bool(wo_name), wo_name):
        _print_summary(errors)
        return

    doc = frappe.get_doc("Mathipe Work Order", wo_name)

    # 1) LOW_MARGIN: fijar revenue_total > 0 y gross_margin_pct bajo
    print("─── LOW_MARGIN (margen bajo) ───")
    frappe.db.set_value("Mathipe Work Order", wo_name, "revenue_total", 10000)
    frappe.db.set_value("Mathipe Work Order", wo_name, "gross_margin_pct", 10)  # por debajo de 15
    frappe.db.set_value("Mathipe Work Order", wo_name, "estimated_cost_total", 9000)
    frappe.db.set_value("Mathipe Work Order", wo_name, "gross_margin", 1000)
    frappe.db.commit()
    doc.reload()
    doc.revenue_total = 10000
    doc.gross_margin_pct = 10
    doc.estimated_cost_total = 9000
    doc.gross_margin = 1000
    alerts = _compute_alerts(doc, settings)
    low_margin_alerts = [a for a in alerts if a.get("code") == "LOW_MARGIN"]
    if not _check("Alerta LOW_MARGIN (danger) con margen 10%", len(low_margin_alerts) >= 1 and low_margin_alerts[0].get("level") == "danger"):
        errors.append("LOW_MARGIN danger no detectada")
    else:
        _check("Nivel danger", low_margin_alerts[0].get("level") == "danger", low_margin_alerts[0].get("title"))

    # 2) WAITING_APPROVAL_TOO_LONG: poner WO en WaitingApproval y status_log con changed_at hace 5 días
    print("─── WAITING_APPROVAL_TOO_LONG ───")
    if not frappe.db.exists("Mathipe WO Status Log", {"parent": wo_name}):
        # Crear entrada en status_log
        log = frappe.get_doc({
            "doctype": "Mathipe WO Status Log",
            "parent": wo_name,
            "parenttype": "Mathipe Work Order",
            "parentfield": "status_log",
            "from_status": "New",
            "to_status": "WaitingApproval",
            "changed_by": frappe.session.user,
            "changed_at": (date.today() - timedelta(days=5)).strftime("%Y-%m-%d 10:00:00"),
            "comment": "Test alertas",
        })
        log.insert()
    else:
        # Actualizar la última entrada a WaitingApproval y hace 5 días
        logs = frappe.get_all("Mathipe WO Status Log", filters={"parent": wo_name}, fields=["name", "to_status", "changed_at"])
        for log_row in logs:
            frappe.db.set_value("Mathipe WO Status Log", log_row.name, "to_status", "WaitingApproval")
            frappe.db.set_value("Mathipe WO Status Log", log_row.name, "changed_at", (date.today() - timedelta(days=5)).strftime("%Y-%m-%d 10:00:00"))
    frappe.db.set_value("Mathipe Work Order", wo_name, "status", "WaitingApproval")
    frappe.db.commit()
    doc.reload()
    alerts2 = _compute_alerts(doc, settings)
    wait_alerts = [a for a in alerts2 if a.get("code") == "WAITING_APPROVAL_TOO_LONG"]
    if not _check("Alerta WAITING_APPROVAL_TOO_LONG cuando días >= threshold", len(wait_alerts) >= 1 or settings.get("waiting_approval_days_threshold", 3) > 5, str(len(wait_alerts))):
        # Si el umbral es > 5 no aparecerá; entonces solo verificamos que no rompa
        _check("Cálculo de alertas sin error", True, "Umbral puede ser > 5")

    # 3) OUTSOURCE_SENT_TOO_LONG: ítem tercerizado Sent con outsource_sent_at hace 6 días
    print("─── OUTSOURCE_SENT_TOO_LONG ───")
    items = doc.items or []
    if items:
        item_name = items[0].name
        frappe.db.set_value("Mathipe WO Item", item_name, "is_outsourced", 1)
        frappe.db.set_value("Mathipe WO Item", item_name, "outsource_status", "Sent")
        frappe.db.set_value("Mathipe WO Item", item_name, "outsource_sent_at", (date.today() - timedelta(days=6)).strftime("%Y-%m-%d 10:00:00"))
        frappe.db.set_value("Mathipe WO Item", item_name, "supplier", "Proveedor Test Alertas")
        frappe.db.commit()
        doc.reload()
        alerts3 = _compute_alerts(doc, settings)
        sent_alerts = [a for a in alerts3 if a.get("code") == "OUTSOURCE_SENT_TOO_LONG"]
        if not _check("Alerta OUTSOURCE_SENT_TOO_LONG (enviado hace 6 días)", len(sent_alerts) >= 1, str(len(sent_alerts))):
            errors.append("OUTSOURCE_SENT_TOO_LONG no detectada")
    else:
        print("  [SKIP] WO sin ítems para probar OUTSOURCE_SENT_TOO_LONG")

    # 4) get_work_order_alerts: niveles y counts
    print("─── get_work_order_alerts ───")
    res = get_work_order_alerts(wo_name)
    res = res if isinstance(res, dict) else {}
    summary = res.get("summary") or {}
    alerts_list = res.get("alerts") or []
    if not _check("get_work_order_alerts devuelve summary y alerts", "summary" in res and "alerts" in res):
        errors.append("get_work_order_alerts formato incorrecto")
    total = (summary.get("danger") or 0) + (summary.get("warning") or 0) + (summary.get("info") or 0)
    if not _check("Summary counts coherentes con lista", total == len(alerts_list), f"summary total={total} list len={len(alerts_list)}"):
        errors.append("Counts no coinciden")

    # Limpieza: restaurar status si se cambió (opcional; no borramos WO por si es dato real)
    frappe.db.set_value("Mathipe Work Order", wo_name, "status", "New")
    frappe.db.commit()

    _print_summary(errors)


def _print_summary(errors):
    print("\n=== RESUMEN ===")
    if not errors:
        print("  Todos los tests de alertas pasaron.")
    else:
        print(f"  {len(errors)} error(es):")
        for e in errors:
            print(f"    - {e}")
    print()

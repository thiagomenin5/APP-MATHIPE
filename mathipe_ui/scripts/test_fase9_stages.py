"""
Tests Fase 9 — Producción por sectores (ruteo).

Uso:
    bench --site [site] execute mathipe_ui.scripts.test_fase9_stages.run_tests

Verifica:
    - WO Approved -> Production genera stages por defecto (sin duplicar).
    - Stage log se registra al hacer take/finish.
    - current_sector se calcula (primer Pending/In Progress).
    - Usuario sin rol de sector no puede take/finish (permiso).
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

    print("\n=== TEST FASE 9 — Stages por sector ===\n")

    from mathipe_ui.api import (
        create_or_get_work_order,
        update_work_order_status,
        get_work_order_details,
        init_wo_stages_from_template,
        update_wo_stage,
        get_sector_board,
        _user_can_operate_sector,
        _wo_current_sector,
    )

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
    if getattr(doc, "stages", None):
        doc.stages = []
        doc.run_method("before_save")
        doc.db_update()
        frappe.db.commit()
    doc.status = "Approved"
    doc.flags.ignore_permissions = True
    doc.save()
    frappe.db.commit()

    # Pasar a Production debe crear stages
    res = update_work_order_status(wo_id, "Production", comment=None)
    res = res if isinstance(res, dict) else {}
    _check("update_work_order_status devuelve detail", "name" in res or "work_order_id" in res)
    stages = res.get("stages") or []
    _check("Stages creados al pasar a Production", len(stages) >= 1, f"count={len(stages)}")

    # Idempotencia: llamar de nuevo no duplica
    prev_len = len(stages)
    init_wo_stages_from_template(wo_id, template_key=None)
    detail2 = get_work_order_details(wo_id)
    stages2 = detail2.get("stages") or []
    _check("init_wo_stages_from_template no duplica", len(stages2) == prev_len, f"prev={prev_len} now={len(stages2)}")

    # current_sector: primer Pending o In Progress
    current = detail2.get("current_sector")
    has_pending = any((s.get("stage_status") or "").strip() == "Pending" for s in stages2)
    _check("current_sector presente o stages vacíos", current is not None or not has_pending or len(stages2) == 0)

    # Tomar primera etapa (Pending -> In Progress)
    first_row = None
    for s in stages2:
        if (s.get("stage_status") or "").strip() == "Pending":
            first_row = s.get("name")
            break
    if first_row:
        res_take = update_wo_stage(wo_id, first_row, "take", comment=None)
        res_take = res_take if isinstance(res_take, dict) else {}
        stages_after = res_take.get("stages") or []
        row_after = next((x for x in stages_after if x.get("name") == first_row), None)
        _check("take: etapa pasa a In Progress", row_after and (row_after.get("stage_status") or "").strip() == "In Progress")
        stage_log = res_take.get("stage_log") or []
        _check("stage_log registra cambio", len(stage_log) >= 1)
    else:
        print(f"  [SKIP] No hay etapa Pending para probar take")

    # get_sector_board devuelve listas
    board = get_sector_board("printing", only_open=1)
    _check("get_sector_board devuelve pending/in_progress/done", "pending" in board and "in_progress" in board and "done" in board)

    # Permiso: usuario sin rol de sector no puede operar (Administrator tiene override)
    can = _user_can_operate_sector("Administrator", "printing")
    _check("Administrator puede operar sector (override)", can)
    can_guest = _user_can_operate_sector("Guest", "printing")
    _check("Guest no puede operar sector", not can_guest)

    print("\n=== Fin tests Fase 9 ===\n")

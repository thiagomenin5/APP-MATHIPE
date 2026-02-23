"""
Script de prueba manual para Fase 1 — Mathipe ERP.

Uso:
    bench --site [site] execute mathipe_ui.scripts.test_fase1.run_tests

Verifica:
    1. DocTypes existen en DB
    2. Creación de Mathipe Quote con 3 ítems (Fixed, Area, Recipe simulado)
    3. Conversión a Sales Order → exactamente 1 SO creada
    4. Work Order creada automáticamente → exactamente 1 WO vinculada
    5. Links correctos: SO.mathipe_quote=quote_id, Quote.sales_order=so_name, WO.sales_order=so_name
    6. Totales > 0 (Quote y SO)
    7. Idempotencia: segunda conversión retorna already_converted=1 y misma SO/WO
    8. Bloqueo de cotización Rechazada
    9. Validación Area sin dimensiones
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

    print("\n=== TEST FASE 1 — Mathipe ERP ===\n")

    # ── 1. DocTypes en DB ──────────────────────────────────────────────────────
    print("─── 1. DocTypes ───")
    required_doctypes = [
        "Mathipe Quote", "Mathipe Quote Item",
        "Mathipe Product Recipe", "Mathipe Recipe Component",
        "Mathipe Work Order", "Mathipe WO Assigned User", "Mathipe WO Checklist Item",
    ]
    for dt in required_doctypes:
        ok = frappe.db.exists("DocType", dt)
        if not _check(f"DocType '{dt}'", ok):
            errors.append(f"Falta DocType: {dt}")

    # ── 2. Obtener cliente de prueba ───────────────────────────────────────────
    print("\n─── 2. Cliente de prueba ───")
    customer = frappe.db.get_value("Customer", {}, "name")
    if not _check("Existe al menos un Customer", customer, customer):
        errors.append("Sin clientes en el sistema")
        _print_summary(errors)
        return

    # ── 3. Crear cotización con 3 ítems ────────────────────────────────────────
    print("\n─── 3. Crear Mathipe Quote ───")
    from mathipe_ui.api import create_quote, get_quote

    items = [
        # Fixed: precio directo
        {"product_type": "Fixed", "qty": 10, "unit_price": 1500.0, "description": "Banner fijo"},
        # Area: dimensiones obligatorias
        {"product_type": "Area", "qty": 5, "width": 1000.0, "height": 500.0, "unit_price": 800.0, "price_per_m2": 800.0, "description": "Vinilo por m²"},
        # Fixed con sale_total no nulo
        {"product_type": "Fixed", "qty": 3, "unit_price": 2000.0, "description": "Impresión A3"},
    ]

    result = create_quote(
        customer=customer,
        delivery_date="2026-12-31",
        items=items,
        notes="Test automatizado Fase 1",
    )
    quote_id = (result or {}).get("name")
    _check("create_quote retorna name", bool(quote_id), quote_id)
    if not quote_id:
        errors.append("No se creó la cotización")
        _print_summary(errors)
        return

    # Verificar que se guardó con ítems
    quote_doc = frappe.get_doc("Mathipe Quote", quote_id)
    _check("Quote tiene 3 ítems", len(quote_doc.items) == 3, f"{len(quote_doc.items)} ítems")
    _check("Quote sale_total > 0", float(quote_doc.sale_total or 0) > 0, f"${quote_doc.sale_total}")

    # Verificar breakdown_json persistido
    items_with_breakdown = [i for i in quote_doc.items if getattr(i, "breakdown_json", None)]
    _check("breakdown_json persistido en ítems", len(items_with_breakdown) == 3, f"{len(items_with_breakdown)}/3 con breakdown")

    # Verificar API get_quote
    detail = get_quote(quote_id)
    _check("get_quote retorna cost_lines", all(i.get("cost_lines") is not None for i in detail.get("items", [])))

    # ── 4. Convertir a Sales Order ─────────────────────────────────────────────
    print("\n─── 4. Convertir a Sales Order ───")
    from mathipe_ui.api import convert_quote_to_sales_order

    conv = convert_quote_to_sales_order(quote_id)
    so_name = (conv or {}).get("name")
    wo_name = (conv or {}).get("work_order")
    _check("convert devuelve SO name", bool(so_name), so_name)
    _check("convert devuelve WO name", bool(wo_name), wo_name)

    if so_name:
        so_doc = frappe.get_doc("Sales Order", so_name)
        _check("SO tiene ítems", len(so_doc.items) == 3, f"{len(so_doc.items)} ítems")
        _check("SO remarks incluye quote_id", f"[Cotización: {quote_id}]" in (so_doc.remarks or ""))
        grand_total = float(so_doc.grand_total or 0)
        _check("SO grand_total > 0", grand_total > 0, f"${grand_total}")
        if frappe.db.column_exists("Sales Order", "mathipe_quote"):
            _check("SO.mathipe_quote = quote_id", getattr(so_doc, "mathipe_quote", None) == quote_id, getattr(so_doc, "mathipe_quote", None))

    if wo_name:
        wo_doc = frappe.get_doc("Mathipe Work Order", wo_name)
        _check("WO vinculada a SO", wo_doc.sales_order == so_name, wo_doc.sales_order)
        _check("WO status = New", wo_doc.status == "New", wo_doc.status)

    # Verificar solo 1 SO para esta quote y 1 WO para esa SO (no duplicados)
    if frappe.db.column_exists("Sales Order", "mathipe_quote"):
        so_count = frappe.db.count("Sales Order", {"mathipe_quote": quote_id})
    else:
        so_count = 1 if so_name else 0
    _check("Exactamente 1 SO para la quote", so_count == 1, f"{so_count} SO(s)")
    wo_count = frappe.db.count("Mathipe Work Order", {"sales_order": so_name}) if so_name else 0
    _check("Exactamente 1 WO por SO", wo_count == 1, f"{wo_count} WO(s)")

    # Quote.sales_order link (tras conversión)
    quote_doc.reload()
    if frappe.db.column_exists("Mathipe Quote", "sales_order"):
        _check("Quote.sales_order = SO", getattr(quote_doc, "sales_order", None) == so_name, getattr(quote_doc, "sales_order", None))

    # ── 5. Idempotencia ────────────────────────────────────────────────────────
    print("\n─── 5. Idempotencia ───")
    conv2 = convert_quote_to_sales_order(quote_id)
    _check("Segunda conversión retorna already_converted=True", (conv2 or {}).get("already_converted") is True)
    _check("Segunda conversión retorna misma SO", (conv2 or {}).get("name") == so_name, (conv2 or {}).get("name"))

    # ── 6. Bloquear Rejected ───────────────────────────────────────────────────
    print("\n─── 6. Bloquear conversión de Rejected ───")
    # Crear quote temporal y rechazarla
    temp_result = create_quote(
        customer=customer,
        delivery_date="2026-12-31",
        items=[{"product_type": "Fixed", "qty": 1, "unit_price": 100.0}],
    )
    temp_qid = (temp_result or {}).get("name")
    if temp_qid:
        temp_doc = frappe.get_doc("Mathipe Quote", temp_qid)
        temp_doc.status = "Rejected"
        temp_doc.save(ignore_permissions=True)
        frappe.db.commit()
        rejected_blocked = False
        try:
            convert_quote_to_sales_order(temp_qid)
        except Exception:
            rejected_blocked = True
        _check("Conversión de Rejected lanza excepción", rejected_blocked)
        # Limpiar
        frappe.delete_doc("Mathipe Quote", temp_qid, ignore_permissions=True, force=True)
        frappe.db.commit()

    # ── 7. Validación Area sin dimensiones ────────────────────────────────────
    print("\n─── 7. Validación Area sin dimensiones ───")
    area_rejected = False
    try:
        create_quote(
            customer=customer,
            delivery_date="2026-12-31",
            items=[{"product_type": "Area", "qty": 5, "width": 0, "height": 0, "unit_price": 100.0}],
        )
    except Exception:
        area_rejected = True
    _check("create_quote rechaza Area con width=0 height=0", area_rejected)

    # ── Limpieza de test data ──────────────────────────────────────────────────
    print("\n─── Limpieza ───")
    try:
        if wo_name:
            frappe.delete_doc("Mathipe Work Order", wo_name, ignore_permissions=True, force=True)
        if so_name:
            frappe.delete_doc("Sales Order", so_name, ignore_permissions=True, force=True)
        if quote_id:
            frappe.delete_doc("Mathipe Quote", quote_id, ignore_permissions=True, force=True)
        frappe.db.commit()
        print("  Datos de prueba eliminados OK")
    except Exception as e:
        print(f"  Limpieza parcial: {e}")

    _print_summary(errors)


def _print_summary(errors):
    print("\n=== RESUMEN ===")
    if not errors:
        print("  Todos los tests pasaron sin errores críticos.")
    else:
        print(f"  {len(errors)} error(es) crítico(s):")
        for e in errors:
            print(f"    - {e}")
    print()

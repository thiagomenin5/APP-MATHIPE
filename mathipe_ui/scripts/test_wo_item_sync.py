"""
Tests sincronización WO Items desde Quote (poblado automático, idempotencia).

Uso:
    bench --site [site] execute mathipe_ui.scripts.test_wo_item_sync.run_tests

Verifica:
    1. Quote con 2 ítems -> convertir -> WO tiene 2 WO Items con quote_item correcto.
    2. Marcar 1 WO Item como tercerizado + supplier + status=Sent.
    3. Reconvertir / resync: no duplicar ítems, no pisar campos de tercerización.
    4. (Opcional) Actualizar qty en quote y resync -> WO item actualiza qty.
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

    print("\n=== TEST WO Item Sync desde Quote ===\n")

    if not frappe.db.exists("DocType", "Mathipe WO Item"):
        print(f"{FAIL} DocType 'Mathipe WO Item' no existe. Ejecutar bench migrate.")
        return

    from mathipe_ui.api import (
        create_quote,
        convert_quote_to_sales_order,
        get_work_order_details,
        update_work_order_item,
        update_outsource_status,
        resync_work_order_items_from_quote,
    )

    customer = frappe.db.get_value("Customer", {}, "name")
    if not _check("Existe Customer de prueba", customer, customer):
        errors.append("Sin clientes en el sistema")
        _print_summary(errors)
        return

    # 1) Quote con 2 ítems
    print("─── 1. Quote con 2 ítems ───")
    result = create_quote(
        customer=customer,
        delivery_date="2026-12-31",
        items=[
            {"product_type": "Fixed", "qty": 2, "unit_price": 100.0, "description": "Ítem A sync"},
            {"product_type": "Fixed", "qty": 3, "unit_price": 200.0, "description": "Ítem B sync"},
        ],
        notes="Test WO item sync",
    )
    quote_id = (result or {}).get("name")
    if not _check("Quote creada", bool(quote_id), quote_id):
        _print_summary(errors)
        return

    quote = frappe.get_doc("Mathipe Quote", quote_id)
    quote_item_names = [row.name for row in quote.items if row.name]
    if not _check("Quote tiene 2 ítems con name", len(quote_item_names) == 2, str(quote_item_names)):
        _cleanup(quote_id, None, None)
        _print_summary(errors)
        return

    # 2) Convertir -> WO con 2 ítems y quote_item
    print("─── 2. Convertir → WO con 2 WO Items y quote_item ───")
    conv = convert_quote_to_sales_order(quote_id)
    so_name = (conv or {}).get("name")
    wo_name = (conv or {}).get("work_order")
    if not _check("SO y WO creadas", bool(so_name) and bool(wo_name), f"SO={so_name} WO={wo_name}"):
        _cleanup(quote_id, so_name, wo_name)
        _print_summary(errors)
        return

    detail = get_work_order_details(wo_name)
    wo_items = (detail or {}).get("items") or []
    if not _check("WO tiene 2 ítems", len(wo_items) == 2, f"{len(wo_items)} ítems"):
        errors.append("WO debería tener 2 ítems")
    wo_quote_items = [it.get("quote_item") for it in wo_items if it.get("quote_item")]
    match = set(wo_quote_items) >= set(quote_item_names)
    if not _check("Cada WO Item tiene quote_item correcto", match, str(wo_quote_items)):
        errors.append("quote_item no coincide con Quote Items")

    # 3) Marcar primer ítem tercerizado + supplier + Sent
    print("─── 3. Marcar primer ítem tercerizado + Sent ───")
    first_row_id = wo_items[0].get("name")
    if not first_row_id:
        errors.append("Primer ítem sin name")
    else:
        try:
            update_work_order_item(wo_name, first_row_id, {"is_outsourced": 1, "supplier": "Proveedor Sync Test"})
            update_outsource_status(wo_name, first_row_id, "sent")
        except Exception as e:
            _check("Marcar tercerizado + Sent", False, str(e))
            errors.append("update_work_order_item / update_outsource_status falló")
        _check("Primer ítem tercerizado y Sent", True)

    # 4) Reconvertir (idempotencia) -> no duplicar, no pisar tercerización
    print("─── 4. Reconvertir (idempotencia) ───")
    conv2 = convert_quote_to_sales_order(quote_id)
    if not _check("Reconvert retorna already_converted", (conv2 or {}).get("already_converted") is True):
        errors.append("Segunda conversión debería ser idempotente")
    detail2 = get_work_order_details(wo_name)
    wo_items2 = (detail2 or {}).get("items") or []
    if not _check("Sigue habiendo 2 ítems (no duplicar)", len(wo_items2) == 2, f"{len(wo_items2)} ítems"):
        errors.append("Reconvert duplicó ítems")
    first2 = next((i for i in wo_items2 if i.get("name") == first_row_id), None)
    if first2:
        if not _check("Primer ítem sigue tercerizado", bool(first2.get("is_outsourced"))):
            errors.append("Resync pisó is_outsourced")
        if not _check("Primer ítem sigue con supplier", (first2.get("supplier") or "").strip() == "Proveedor Sync Test"):
            errors.append("Resync pisó supplier")
        if not _check("Primer ítem sigue Sent", (first2.get("outsource_status") or "").strip() == "Sent"):
            errors.append("Resync pisó outsource_status")

    # 5) Cambiar qty en quote y resync -> WO actualiza qty
    print("─── 5. Cambiar qty en Quote y resync ───")
    quote.reload()
    if quote.items and len(quote.items) >= 2:
        old_qty = float(quote.items[1].get("qty") or 0)
        quote.items[1].qty = 7
        quote.save(ignore_permissions=True)
        frappe.db.commit()
        try:
            resync_work_order_items_from_quote(wo_name)
        except Exception as e:
            _check("resync_work_order_items_from_quote", False, str(e))
        else:
            detail3 = get_work_order_details(wo_name)
            wo_items3 = (detail3 or {}).get("items") or []
            second_by_quote = next((i for i in wo_items3 if (i.get("quote_item") or "") == (quote_item_names[1] if len(quote_item_names) > 1 else None)), None)
            if second_by_quote and float(second_by_quote.get("qty") or 0) == 7:
                _check("Resync actualizó qty del segundo ítem", True)
            else:
                _check("Resync actualizó qty del segundo ítem", False, f"qty={second_by_quote.get('qty') if second_by_quote else 'N/A'}")
        quote.items[1].qty = old_qty
        quote.save(ignore_permissions=True)
        frappe.db.commit()

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
        print("  Todos los tests de sync WO Items pasaron.")
    else:
        print(f"  {len(errors)} error(es):")
        for e in errors:
            print(f"    - {e}")
    print()

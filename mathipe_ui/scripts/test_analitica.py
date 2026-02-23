"""
Tests Analítica de Rentabilidad (get_profitability_breakdown).

Uso:
    bench --site [site] execute mathipe_ui.scripts.test_analitica.run_tests

Verifica:
    - 2 clientes, 2 WOs (1 con ítems tercerizados Received + outsource_cost, otra Pending).
    - get_profitability_breakdown con include_without_sales_order=0 y 1.
    - Clientes: revenue/margin > 0 donde aplique.
    - Tipos: product_type presente.
    - Proveedores: received_rate = received_count / count_items.
    - bottom_by_margin_pct respeta min_revenue.
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

    print("\n=== TEST ANALÍTICA (get_profitability_breakdown) ===\n")

    from mathipe_ui.api import (
        create_quote,
        convert_quote_to_sales_order,
        get_work_order_details,
        update_work_order_item,
        update_outsource_status,
        get_profitability_breakdown,
    )

    customers = frappe.get_all("Customer", filters={"disabled": 0}, pluck="name", limit=2)
    if not _check("Al menos 2 clientes", len(customers) >= 2, str(len(customers))):
        errors.append("Se necesitan al menos 2 clientes")
        _print_summary(errors)
        return

    # WO1: cliente 1, ítem tercerizado Received con outsource_cost
    print("─── WO1: Quote → SO → WO, ítem Received + outsource_cost ───")
    r1 = create_quote(
        customer=customers[0],
        delivery_date="2026-06-15",
        items=[{"product_type": "Fixed", "qty": 1, "unit_price": 10000.0, "description": "Analítica A"}],
        notes="Test analítica",
    )
    quote1 = (r1 or {}).get("name")
    if not quote1:
        errors.append("Quote 1 no creada")
        _print_summary(errors)
        return
    conv1 = convert_quote_to_sales_order(quote1)
    so1 = (conv1 or {}).get("name")
    wo1 = (conv1 or {}).get("work_order")
    if not so1 or not wo1:
        _cleanup([(quote1, so1, wo1)])
        _print_summary(errors)
        return
    # Fecha de venta para filtro
    frappe.db.set_value("Sales Order", so1, "transaction_date", "2026-06-01")
    frappe.db.commit()
    detail1 = get_work_order_details(wo1)
    items1 = (detail1 or {}).get("items") or []
    if not items1:
        _cleanup([(quote1, so1, wo1)])
        _print_summary(errors)
        return
    update_work_order_item(wo1, items1[0]["name"], {"is_outsourced": 1, "supplier": "Proveedor Analítica", "outsource_cost": 6000})
    update_outsource_status(wo1, items1[0]["name"], "received")

    # WO2: cliente 2, ítem tercerizado Pending
    print("─── WO2: Quote → SO → WO, ítem Pending ───")
    r2 = create_quote(
        customer=customers[1],
        delivery_date="2026-06-20",
        items=[{"product_type": "Area", "qty": 2, "width": 500, "height": 500, "unit_price": 5000.0, "description": "Analítica B"}],
        notes="Test analítica 2",
    )
    quote2 = (r2 or {}).get("name")
    if not quote2:
        _cleanup([(quote1, so1, wo1)])
        _print_summary(errors)
        return
    conv2 = convert_quote_to_sales_order(quote2)
    so2 = (conv2 or {}).get("name")
    wo2 = (conv2 or {}).get("work_order")
    if not so2 or not wo2:
        _cleanup([(quote1, so1, wo1), (quote2, so2, wo2)])
        _print_summary(errors)
        return
    frappe.db.set_value("Sales Order", so2, "transaction_date", "2026-06-05")
    frappe.db.commit()
    detail2 = get_work_order_details(wo2)
    items2 = (detail2 or {}).get("items") or []
    if not items2:
        _cleanup([(quote1, so1, wo1), (quote2, so2, wo2)])
        _print_summary(errors)
        return
    update_work_order_item(wo2, items2[0]["name"], {"is_outsourced": 1, "supplier": "Proveedor Pending"})
    # Dejar Pending (no llamar update_outsource_status received)

    print("─── get_profitability_breakdown include_without_sales_order=0 ───")
    out0 = get_profitability_breakdown(date_from="2026-06-01", date_to="2026-06-30", include_without_sales_order=0, min_revenue=5000)
    by_c0 = out0.get("by_customer") or {}
    by_type0 = out0.get("by_product_type") or []
    by_supp0 = out0.get("by_supplier") or []
    _check("by_customer existe", "by_customer" in out0)
    _check("by_product_type es lista", isinstance(by_type0, list))
    _check("by_supplier es lista", isinstance(by_supp0, list))
    if by_c0.get("total_customers", 0) > 0:
        top_rev = by_c0.get("top_by_revenue") or []
        if top_rev:
            c = top_rev[0]
            _check("Cliente tiene revenue > 0", (c.get("revenue_total") or 0) > 0)
            _check("Cliente tiene customer_name", bool((c.get("customer_name") or "").strip()))
    for t in by_type0:
        _check("Tipo tiene product_type", bool((t.get("product_type") or "").strip()), t.get("product_type"))
    for s in by_supp0:
        count = int(s.get("count_items") or 0)
        rec = int(s.get("received_count") or 0)
        rate = float(s.get("received_rate") or 0)
        expected_rate = round(rec / count * 100, 1) if count > 0 else 0.0
        _check("Proveedor received_rate correcto", abs(rate - expected_rate) < 0.01, f"rate={rate} expected={expected_rate}")
    min_rev = float(by_c0.get("min_revenue_threshold") or 0)
    bottom = by_c0.get("bottom_by_margin_pct") or []
    for b in bottom:
        if not _check("bottom respeta min_revenue", (b.get("revenue_total") or 0) >= min_rev - 0.01):
            errors.append("bottom_by_margin_pct incluyó cliente con revenue < min_revenue")

    print("─── get_profitability_breakdown include_without_sales_order=1 ───")
    out1 = get_profitability_breakdown(date_from="2026-06-01", date_to="2026-06-30", include_without_sales_order=1, min_revenue=5000)
    _check("Respuesta con include_without_sales_order=1", "by_customer" in (out1 or {}))

    print("─── min_revenue default 5000 ───")
    out_def = get_profitability_breakdown(date_from="2026-06-01", date_to="2026-06-30", min_revenue=None)
    thr = (out_def.get("by_customer") or {}).get("min_revenue_threshold")
    _check("min_revenue_threshold default 5000", thr == 5000.0, str(thr))

    _cleanup([(quote1, so1, wo1), (quote2, so2, wo2)])
    _print_summary(errors)


def _cleanup(pairs):
    for quote_id, so_name, wo_name in pairs:
        if not quote_id:
            continue
        try:
            if wo_name and frappe.db.exists("Mathipe Work Order", wo_name):
                frappe.delete_doc("Mathipe Work Order", wo_name, ignore_permissions=True, force=True)
            if so_name and frappe.db.exists("Sales Order", so_name):
                frappe.delete_doc("Sales Order", so_name, ignore_permissions=True, force=True)
            if quote_id and frappe.db.exists("Mathipe Quote", quote_id):
                frappe.delete_doc("Mathipe Quote", quote_id, ignore_permissions=True, force=True)
        except Exception as e:
            print(f"  Limpieza: {e}")
    frappe.db.commit()
    print("  Limpieza OK")


def _print_summary(errors):
    print("\n=== RESUMEN ===")
    if not errors:
        print("  Tests de analítica OK.")
    else:
        print(f"  {len(errors)} error(es):")
        for e in errors:
            print(f"    - {e}")
    print()

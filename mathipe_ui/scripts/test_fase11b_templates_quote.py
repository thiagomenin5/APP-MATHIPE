"""
Tests Fase 11B — Integración plantillas (Mi Empresa) con Cotizador y rutas.

Uso:
    bench --site [site] execute mathipe_ui.scripts.test_fase11b_templates_quote.run_tests

Verifica:
    - calculate_quote_item_from_template devuelve sale_total>0 y cost_lines no vacíos.
    - create_quote con item.product_template crea Quote Item con breakdown_json.
    - convert_quote_to_sales_order genera WO y stages según route_template del template (si existe).
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
    print("\n=== TEST FASE 11B — Plantillas + Cotizador + Rutas ===\n")

    from mathipe_ui.api import (
        get_company_setup,
        ensure_default_sectors,
        list_materials,
        save_material,
        list_operations,
        save_operation,
        list_machines,
        save_machine,
        save_route_template,
        save_product_template,
        calculate_quote_item_from_template,
        create_quote,
        convert_quote_to_sales_order,
        get_quote,
    )

    if not frappe.db.table_exists("Mathipe Product Template"):
        print(f"{FAIL} Ejecute migración (Fase 11A) para tener Mathipe Product Template.")
        return

    try:
        ensure_default_sectors()
        frappe.db.commit()
    except Exception as e:
        print(f"  [SKIP] ensure_default_sectors: {e}")
    setup = get_company_setup()
    sectors = setup.get("sectors") or []
    sector_name = sectors[0].get("name") if sectors else None
    if not sector_name:
        print(f"{FAIL} No hay sectores. Ejecute migración/patch de sectores y ensure_default_sectors (como Administrator).")
        return

    # Datos de prueba (crear si no existen)
    mat_name = "Test Material F11B"
    op_name = "Test Operation F11B"
    mach_name = "Test Machine F11B"
    if not frappe.db.exists("Mathipe Material", mat_name):
        save_material({"material_name": mat_name, "unit_type": "m2", "cost_per_unit": 10, "active": 1})
    if not frappe.db.exists("Mathipe Operation", op_name):
        save_operation({"operation_name": op_name, "sector_key": sector_name, "costing_mode": "PerUnit", "cost_per_unit": 5, "active": 1})
    if not frappe.db.exists("Mathipe Machine", mach_name):
        save_machine({"machine_name": mach_name, "machine_type": "Digital", "sector_key": sector_name, "cost_per_hour": 50, "active": 1})

    route_name = "Test Route F11B"
    if not frappe.db.exists("Mathipe Route Template", route_name):
        save_route_template({
            "route_name": route_name,
            "description": "Ruta test",
            "steps": [{"sector_key": sector_name, "mandatory": 1, "allow_parallel": 0}],
        })

    template_name = "Test Product Template F11B"
    if not frappe.db.exists("Mathipe Product Template", template_name):
        save_product_template({
            "product_name": template_name,
            "costing_mode": "Automatic",
            "default_margin_pct": 30,
            "default_route_template": route_name,
            "allow_dimensions": 1,
            "allow_qty": 1,
            "components": [
                {"component_type": "Material", "ref_material": mat_name, "qty_mode": "PerM2", "qty_value": 1, "waste_pct": 0},
                {"component_type": "Operation", "ref_operation": op_name, "qty_mode": "PerUnit", "qty_value": 1, "waste_pct": 0},
            ],
        })

    # calculate_quote_item_from_template
    res = calculate_quote_item_from_template({
        "product_template": template_name,
        "qty": 2,
        "width": 1000,
        "height": 500,
        "margin_pct": 30,
    })
    data = res if isinstance(res, dict) else {}
    _check("calculate_quote_item_from_template devuelve sale_total>0", (data.get("sale_total") or 0) > 0)
    _check("calculate_quote_item_from_template devuelve cost_lines no vacíos", len(data.get("cost_lines") or []) > 0)
    _check("breakdown_json presente", bool(data.get("breakdown_json")))

    # create_quote con product_template
    customers = frappe.get_all("Customer", limit=1)
    if not customers:
        print(f"{FAIL} Se necesita al menos un Customer.")
        return
    customer_id = customers[0].name
    items = [{
        "product_template": template_name,
        "qty": 2,
        "width": 1000,
        "height": 500,
        "unit_price": data.get("unit_price"),
        "sale_total": data.get("sale_total"),
        "cost_total": data.get("cost_total"),
        "area_total": data.get("area_total"),
        "margin_pct": data.get("margin_pct"),
        "breakdown_json": data.get("breakdown_json"),
    }]
    out = create_quote(customer_id, frappe.utils.nowdate(), items, notes="Test F11B")
    quote_id = out.get("name")
    _check("create_quote con product_template crea cotización", bool(quote_id))
    if quote_id:
        quote = get_quote(quote_id)
        quote_items = quote.get("items") or []
        _check("Quote tiene ítem con breakdown", len(quote_items) >= 1 and (quote_items[0].get("cost_lines") or quote_items[0].get("product_template")))
        has_template = any(it.get("product_template") == template_name for it in quote_items)
        _check("Quote Item tiene product_template", has_template)

    # convert_quote_to_sales_order -> WO con stages desde route_template
    conv = convert_quote_to_sales_order(quote_id)
    wo_name = conv.get("work_order")
    _check("convert_quote_to_sales_order devuelve work_order", bool(wo_name))
    if wo_name:
        wo = frappe.get_doc("Mathipe Work Order", wo_name)
        stages = getattr(wo, "stages", None) or []
        _check("WO tiene stages", len(stages) >= 1, f"count={len(stages)}")

    print("\n=== Fin tests Fase 11B ===\n")

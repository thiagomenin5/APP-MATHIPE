"""
Tests Fase 11A — Mi Empresa (configurador: máquinas, materiales, operaciones, rutas, productos).

Uso:
    bench --site [site] execute mathipe_ui.scripts.test_fase11_company_setup.run_tests

Verifica:
    - get_company_setup devuelve counts y sectores.
    - list/save/delete para Machine, Material, Operation (create -> update -> delete).
    - Route Template con steps: save, get, delete.
    - Product Template con components: save, get, delete.
    - Guest no puede save (permisos).
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
    print("\n=== TEST FASE 11A — Mi Empresa (Company Setup) ===\n")

    from mathipe_ui.api import (
        get_company_setup,
        list_machines,
        save_machine,
        delete_machine,
        list_materials,
        save_material,
        delete_material,
        list_operations,
        save_operation,
        delete_operation,
        list_route_templates,
        get_route_template,
        save_route_template,
        delete_route_template,
        list_product_templates,
        get_product_template,
        save_product_template,
        delete_product_template,
    )

    if not frappe.db.table_exists("Mathipe Machine"):
        print(f"{FAIL} Ejecute migración (patch add_fase11_company_setup) para instalar DocTypes Mi Empresa.")
        return

    # ── get_company_setup ────────────────────────────────────────────────────
    setup = get_company_setup()
    _check("get_company_setup devuelve dict", isinstance(setup, dict))
    _check("get_company_setup tiene counts", "counts" in setup)
    _check("get_company_setup tiene sectors", "sectors" in setup)

    # Necesitamos al menos un sector para Machine/Operation/Route Step
    sectors = setup.get("sectors") or []
    sector_name = sectors[0].get("name") if sectors else None
    if not sector_name:
        print(f"{FAIL} No hay sectores. Ejecute ensure_default_sectors o patch add_fase9_stages.")
        return

    # ── Machines: create -> update -> delete ───────────────────────────────────
    name_machine = "Test Machine F11"
    save_machine({
        "machine_name": name_machine,
        "machine_type": "Digital",
        "sector_key": sector_name,
        "cost_per_hour": 100,
        "active": 1,
    })
    lst = list_machines()
    _check("list_machines incluye máquina creada", any(m.get("machine_name") == name_machine for m in lst))
    save_machine({"name": name_machine, "cost_per_hour": 150})
    doc = frappe.get_doc("Mathipe Machine", name_machine)
    _check("save_machine update modifica cost_per_hour", float(doc.cost_per_hour or 0) == 150)
    delete_machine(name_machine)
    _check("delete_machine elimina", not frappe.db.exists("Mathipe Machine", name_machine))

    # ── Materials: create -> update -> delete ──────────────────────────────────
    name_material = "Test Material F11"
    save_material({
        "material_name": name_material,
        "unit_type": "m2",
        "cost_per_unit": 10,
        "active": 1,
    })
    lst = list_materials()
    _check("list_materials incluye material creado", any(m.get("material_name") == name_material for m in lst))
    save_material({"name": name_material, "cost_per_unit": 12})
    doc = frappe.get_doc("Mathipe Material", name_material)
    _check("save_material update modifica cost_per_unit", float(doc.cost_per_unit or 0) == 12)
    delete_material(name_material)
    _check("delete_material elimina", not frappe.db.exists("Mathipe Material", name_material))

    # ── Operations: create -> update -> delete ────────────────────────────────
    name_op = "Test Operation F11"
    save_operation({
        "operation_name": name_op,
        "sector_key": sector_name,
        "costing_mode": "Fixed",
        "cost_fixed": 50,
        "active": 1,
    })
    lst = list_operations()
    _check("list_operations incluye operación creada", any(o.get("operation_name") == name_op for o in lst))
    save_operation({"name": name_op, "cost_fixed": 60})
    doc = frappe.get_doc("Mathipe Operation", name_op)
    _check("save_operation update modifica cost_fixed", float(doc.cost_fixed or 0) == 60)
    delete_operation(name_op)
    _check("delete_operation elimina", not frappe.db.exists("Mathipe Operation", name_op))

    # ── Route Template con steps ──────────────────────────────────────────────
    name_route = "Test Route F11"
    save_route_template({
        "route_name": name_route,
        "description": "Ruta de prueba",
        "steps": [
            {"sector_key": sector_name, "mandatory": 1, "allow_parallel": 0},
        ],
    })
    lst = list_route_templates()
    _check("list_route_templates incluye ruta creada", any(r.get("route_name") == name_route for r in lst))
    got = get_route_template(name_route)
    _check("get_route_template devuelve ruta con steps", isinstance(got, dict) and len(got.get("steps") or []) >= 1)
    delete_route_template(name_route)
    _check("delete_route_template elimina", not frappe.db.exists("Mathipe Route Template", name_route))

    # ── Product Template con components ───────────────────────────────────────
    name_prod = "Test Product F11"
    save_product_template({
        "product_name": name_prod,
        "costing_mode": "Manual",
        "default_margin_pct": 30,
        "components": [
            {"component_type": "Fixed", "qty_mode": "PerJob", "qty_value": 1, "notes": "Test"},
        ],
    })
    lst = list_product_templates()
    _check("list_product_templates incluye producto creado", any(p.get("product_name") == name_prod for p in lst))
    got = get_product_template(name_prod)
    _check("get_product_template devuelve producto con components", isinstance(got, dict) and len(got.get("components") or []) >= 1)
    delete_product_template(name_prod)
    _check("delete_product_template elimina", not frappe.db.exists("Mathipe Product Template", name_prod))

    # ── Permisos: Guest no puede save ─────────────────────────────────────────
    frappe.set_user("Guest")
    try:
        save_machine({"machine_name": "Guest Machine", "machine_type": "Otro", "sector_key": sector_name})
        _check("Guest no puede save_machine (debe fallar)", False, "esperaba excepción")
    except (frappe.PermissionError, frappe.AuthenticationError, Exception) as e:
        _check("Guest no puede save_machine (falla esperada)", True, str(e)[:60])
    frappe.set_user("Administrator")

    print("\n=== Fin tests Fase 11A ===\n")

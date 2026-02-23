"""Instala DocTypes Fase 11A (una sola vez). Uso: bench --site [site] execute mathipe_ui.scripts.install_fase11_doctypes.install"""
import os


def _test_import():
    """Comprueba si el modulo doctype es importable (Mi Empresa)."""
    try:
        import mathipe_ui.mi_empresa.doctype.mathipe_machine.mathipe_machine as m
        return True, str(m)
    except Exception as e:
        return False, str(e)


def install():
    import sys
    import frappe
    from frappe.modules.import_file import import_file_by_path

    app_path = frappe.get_app_path("mathipe_ui")
    base = os.path.join(app_path, "mi_empresa", "doctype")
    doctypes = (
        "mathipe_machine",
        "mathipe_material",
        "mathipe_operation",
        "mathipe_route_step",
        "mathipe_route_template",
        "mathipe_product_component",
        "mathipe_product_template",
    )
    for name in doctypes:
        path = os.path.join(base, name, name + ".json")
        if os.path.isfile(path):
            try:
                import_file_by_path(path, force=True, ignore_version=True)
                frappe.db.commit()
                print(f"  Imported {name}")
            except Exception as e:
                print(f"  ERROR {name}: {e}")
    ok, msg = _test_import()
    print("Test import mathipe_machine:", ok, msg)
    print("Done.")

# Copyright (c) 2025, Mathipe UI and contributors
# Reparación y configuración total: JSON en disco, reload DocTypes, datos de prueba.

from __future__ import unicode_literals

import json
import os

import frappe


def fix_install():
    """Repara módulo de DocTypes, recarga definiciones y crea datos de prueba."""
    frappe.connect()

    # Ruta a la carpeta doctype del módulo (mathipe_ui/mathipe_ui/mathipe_ui/doctype/)
    _this_dir = os.path.dirname(os.path.abspath(__file__))
    doctype_base = os.path.join(_this_dir, "mathipe_ui", "doctype")
    doctypes_to_fix = [
        ("mathipe_print_material", "mathipe_print_material.json"),
        ("mathipe_print_product", "mathipe_print_product.json"),
    ]

    # --- 1. Corregir archivos JSON en disco ---
    print("--- 1. Corrigiendo archivos JSON en disco ---")
    for folder, filename in doctypes_to_fix:
        json_path = os.path.join(doctype_base, folder, filename)
        if not os.path.isfile(json_path):
            print("  No encontrado:", json_path)
            continue
        try:
            with open(json_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            data["module"] = "Mathipe UI"
            data["custom"] = 0
            with open(json_path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=1, ensure_ascii=False)
            print("  OK:", filename)
        except Exception as e:
            print("  Error en", filename, ":", e)
    print()

    # --- 2. Importar DocTypes desde JSON (por ruta absoluta, evita resolución errónea de módulo) ---
    print("--- 2. Importando DocTypes desde JSON ---")
    from frappe.modules.import_file import import_file_by_path
    for folder, filename in doctypes_to_fix:
        json_path = os.path.join(doctype_base, folder, filename)
        if not os.path.isfile(json_path):
            print("  No encontrado:", json_path)
            continue
        try:
            import_file_by_path(json_path, force=True)
            print("  OK: importado", filename)
        except Exception as e:
            print("  Error importando", filename, ":", e)
    frappe.db.commit()
    print()

    # --- 3. Forzar módulo en la base de datos (por si el JSON no lo aplicó) ---
    print("--- 3. Corrigiendo módulo en base de datos ---")
    for name in ("Mathipe Print Material", "Mathipe Print Product"):
        if frappe.db.exists("DocType", name):
            frappe.db.set_value("DocType", name, "module", "Mathipe UI")
            print("  OK: DocType", name, "-> module = Mathipe UI")
        else:
            print("  DocType", name, "no existe en DB.")
    frappe.db.commit()
    frappe.clear_cache()
    print()

    # --- 4. Crear datos de prueba ---
    print("--- 4. Creando datos de prueba ---")

    # Ítem comodín
    if frappe.db.exists("Item", "COTIZACION-IMPRESION"):
        print("  Item COTIZACION-IMPRESION: ya existe.")
    else:
        try:
            item = frappe.new_doc("Item")
            item.item_code = "COTIZACION-IMPRESION"
            item.item_name = "Cotización de Imprenta"
            item.item_group = "Services"
            item.is_sales_item = 1
            item.insert()
            print("  Item COTIZACION-IMPRESION: creado.")
        except Exception as e:
            print("  Item COTIZACION-IMPRESION: error -", e)

    # Material
    if frappe.db.table_exists("Mathipe Print Material"):
        if frappe.db.exists("Mathipe Print Material", "Ilustracion 300g"):
            print("  Mathipe Print Material 'Ilustracion 300g': ya existe.")
        else:
            try:
                doc = frappe.new_doc("Mathipe Print Material")
                doc.material_name = "Ilustracion 300g"
                doc.category = "Papel"
                doc.cost_per_sheet = 150
                doc.insert()
                print("  Mathipe Print Material 'Ilustracion 300g': creado.")
            except Exception as e:
                print("  Mathipe Print Material: error -", e)
    else:
        print("  Mathipe Print Material: tabla no existe (reload puede haber fallado).")

    # Producto
    if frappe.db.table_exists("Mathipe Print Product"):
        if frappe.db.exists("Mathipe Print Product", "Tarjeta Personal"):
            print("  Mathipe Print Product 'Tarjeta Personal': ya existe.")
        else:
            try:
                doc = frappe.new_doc("Mathipe Print Product")
                doc.product_name = "Tarjeta Personal"
                doc.base_setup_cost = 5000
                doc.print_cost_per_side = 50
                doc.insert()
                print("  Mathipe Print Product 'Tarjeta Personal': creado.")
            except Exception as e:
                print("  Mathipe Print Product: error -", e)
    else:
        print("  Mathipe Print Product: tabla no existe (reload puede haber fallado).")

    frappe.db.commit()
    print()

    # --- 5. Resultado y sugerencia ---
    print("--- Reparación y configuración finalizada ---")
    print("  DocTypes recargados desde mathipe_ui con module 'Mathipe UI'.")
    print("  Datos de prueba creados o ya existentes.")
    print("  Ejecutá: bench --site <tu-site> clear-cache")


# Comando para ejecutar desde SSH:
#   cd /home/frappe/frappe-bench
#   bench --site app.graficamathipe.com.ar execute mathipe_ui.fix_install.fix_install

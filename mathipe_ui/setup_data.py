# Copyright (c) 2025, Mathipe UI and contributors
# Script de instalación de datos iniciales para el Cotizador Paramétrico.

from __future__ import unicode_literals

import frappe


def install_demo_data():
    """Crea ítem comodín, material y producto de prueba si no existen."""
    frappe.connect()

    # --- Ítem comodín para "Convertir en Orden" ---
    if frappe.db.exists("Item", "COTIZACION-IMPRESION"):
        print("Item COTIZACION-IMPRESION: ya existe.")
    else:
        try:
            item = frappe.new_doc("Item")
            item.item_code = "COTIZACION-IMPRESION"
            item.item_name = "Cotización de Imprenta"
            item.item_group = "Services"
            item.is_sales_item = 1
            item.insert()
            frappe.db.commit()
            print("Item COTIZACION-IMPRESION: creado.")
        except Exception as e:
            print("Item COTIZACION-IMPRESION: error -", e)
            frappe.db.rollback()

    # --- Material de prueba (Mathipe Print Material) ---
    if not frappe.db.table_exists("Mathipe Print Material"):
        print("Mathipe Print Material: DocType no existe (ejecutá bench migrate).")
    elif frappe.db.exists("Mathipe Print Material", "Ilustracion 300g"):
        print("Mathipe Print Material 'Ilustracion 300g': ya existe.")
    else:
        try:
            doc = frappe.new_doc("Mathipe Print Material")
            doc.material_name = "Ilustracion 300g"
            doc.category = "Papel"
            doc.cost_per_sheet = 150
            doc.insert()
            frappe.db.commit()
            print("Mathipe Print Material 'Ilustracion 300g': creado.")
        except Exception as e:
            print("Mathipe Print Material: error -", e)
            frappe.db.rollback()

    # --- Producto de prueba (Mathipe Print Product) ---
    if not frappe.db.table_exists("Mathipe Print Product"):
        print("Mathipe Print Product: DocType no existe (ejecutá bench migrate).")
    elif frappe.db.exists("Mathipe Print Product", "Tarjeta Personal"):
        print("Mathipe Print Product 'Tarjeta Personal': ya existe.")
    else:
        try:
            doc = frappe.new_doc("Mathipe Print Product")
            doc.product_name = "Tarjeta Personal"
            doc.base_setup_cost = 5000
            doc.print_cost_per_side = 50
            doc.insert()
            frappe.db.commit()
            print("Mathipe Print Product 'Tarjeta Personal': creado.")
        except Exception as e:
            print("Mathipe Print Product: error -", e)
            frappe.db.rollback()

    print("install_demo_data() finalizado.")


# Para ejecutar desde la consola SSH:
#   cd /home/frappe/frappe-bench
#   bench --site app.graficamathipe.com.ar execute mathipe_ui.setup_data.install_demo_data

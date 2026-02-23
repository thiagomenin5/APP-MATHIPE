# Copyright (c) 2026, Mathipe and contributors
# License: MIT. See LICENSE

import frappe
from frappe.utils import flt, getdate, nowdate
from datetime import timedelta


@frappe.whitelist()
def get_metrics():
	"""
	Métricas para el Dashboard Mathipe: clientes, inventario, producción, entregas, ventas.
	"""
	out = {}

	# Clientes: nuevos este mes
	try:
		first_day = getdate(nowdate()).replace(day=1)
		out["customers_new_this_month"] = frappe.db.count(
			"Customer",
			filters={"creation": [">=", first_day], "disabled": 0}
		) or 0
	except Exception:
		out["customers_new_this_month"] = 0

	# Cuentas por cobrar (resumen simple desde Sales Invoice)
	try:
		company = _default_company()
		if company:
			total = frappe.db.sql("""
				SELECT SUM(outstanding_amount) FROM `tabSales Invoice`
				WHERE docstatus = 1 AND outstanding_amount > 0 AND company = %s
			""", (company,))
			total = flt(total[0][0]) if total and total[0][0] else 0
			currency = frappe.db.get_value("Company", company, "default_currency") or "ARS"
			out["debtors_summary"] = frappe.format_value(total, {"fieldtype": "Currency", "options": currency})
		else:
			out["debtors_summary"] = "—"
	except Exception:
		out["debtors_summary"] = "—"

	# Inventario: items bajo mínimo
	try:
		out["items_below_min"] = frappe.db.sql("""
			SELECT COUNT(DISTINCT b.item_code)
			FROM `tabBin` b
			INNER JOIN `tabItem` i ON i.name = b.item_code AND i.disabled = 0 AND IFNULL(i.is_stock_item, 0) = 1
			WHERE IFNULL(b.actual_qty, 0) < IFNULL(i.safety_stock, 0)
			AND IFNULL(i.safety_stock, 0) > 0
		""")[0][0] or 0
	except Exception:
		out["items_below_min"] = 0

	# Producción: Work Orders
	try:
		out["work_orders_in_progress"] = frappe.db.count("Work Order", {"status": ["in", ["In Process", "Not Started"]], "docstatus": 1}) or 0
		out["work_orders_delayed"] = frappe.db.count("Work Order", {"status": "In Process", "docstatus": 1, "planned_end_date": ["<", nowdate()]}) or 0
	except Exception:
		out["work_orders_in_progress"] = 0
		out["work_orders_delayed"] = 0

	# Entregas: Delivery Note
	try:
		today = nowdate()
		tomorrow = (getdate(today) + timedelta(days=1)).strftime("%Y-%m-%d")
		out["deliveries_today"] = frappe.db.count("Delivery Note", {"delivery_date": today, "docstatus": ["!=", 2]}) or 0
		out["deliveries_tomorrow"] = frappe.db.count("Delivery Note", {"delivery_date": tomorrow, "docstatus": ["!=", 2]}) or 0
	except Exception:
		out["deliveries_today"] = 0
		out["deliveries_tomorrow"] = 0

	# Ventas del mes y cotizaciones abiertas
	try:
		first_day = getdate(nowdate()).replace(day=1)
		out["quotations_open"] = frappe.db.count("Quotation", {"status": "Open", "docstatus": 1}) or 0
		grand_total = frappe.db.sql("""
			SELECT SUM(grand_total) FROM `tabSales Order`
			WHERE docstatus = 1 AND transaction_date >= %s
		""", (first_day,))
		total_val = flt(grand_total[0][0]) if grand_total and grand_total[0][0] else 0
		out["sales_this_month"] = frappe.format_value(total_val, {"fieldtype": "Currency"})
	except Exception:
		out["quotations_open"] = 0
		out["sales_this_month"] = "—"

	return out


def _default_company():
	return (
		frappe.defaults.get_user_default("Company")
		or frappe.db.get_single_value("Global Defaults", "default_company")
		or ""
	)

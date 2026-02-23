# Copyright (c) 2025, Mathipe UI and contributors
# License: MIT. See LICENSE

import frappe
from frappe.model.document import Document


class MathipeQuote(Document):
	def before_save(self):
		self.set_totals()

	def set_totals(self):
		cost_total = sum(float(row.get("cost_total") or 0) for row in (self.items or []))
		sale_total = sum(float(row.get("sale_total") or 0) for row in (self.items or []))
		self.cost_total = cost_total
		self.sale_total = sale_total
		if cost_total and cost_total > 0 and sale_total and sale_total > 0:
			self.margin_pct = round((sale_total - cost_total) / cost_total * 100, 2)
		else:
			self.margin_pct = 0

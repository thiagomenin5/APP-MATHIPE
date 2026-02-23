# Copyright (c) 2025, Mathipe UI and contributors
import frappe
from frappe.model.document import Document


class MathipeRecipeComponent(Document):
	def validate(self):
		# waste_pct debe estar entre 0 y 100
		if self.waste_pct is not None:
			try:
				val = float(self.waste_pct)
				if val < 0 or val > 100:
					frappe.throw("Merma % debe estar entre 0 y 100")
			except (TypeError, ValueError):
				frappe.throw("Merma % debe ser un número entre 0 y 100")

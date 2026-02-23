# Copyright (c) 2026, Mathipe UI and contributors
# License: MIT. See LICENSE

import frappe
from frappe.model.document import Document


def _recalculate_financials(wo_doc):
    """Recalcula revenue_total, estimated_cost_total, real_cost_total, gross_margin y gross_margin_pct.

    Regla de costo real por ítem:
    - is_outsourced=1 AND outsource_status='Received' → usa outsource_cost
    - cualquier otro caso → usa cost_total (estimado)
    """
    items = getattr(wo_doc, "items", None) or []

    revenue_total = sum(float(i.get("sale_total") or 0) for i in items)
    estimated_cost_total = sum(float(i.get("cost_total") or 0) for i in items)

    real_cost_total = 0.0
    for i in items:
        if i.get("is_outsourced") and (i.get("outsource_status") or "") == "Received":
            real_cost_total += float(i.get("outsource_cost") or 0)
        else:
            real_cost_total += float(i.get("cost_total") or 0)

    gross_margin = revenue_total - real_cost_total
    gross_margin_pct = round(gross_margin / revenue_total * 100, 2) if revenue_total > 0 else 0.0

    wo_doc.revenue_total = revenue_total
    wo_doc.estimated_cost_total = estimated_cost_total
    wo_doc.real_cost_total = real_cost_total
    wo_doc.gross_margin = gross_margin
    wo_doc.gross_margin_pct = gross_margin_pct


class MathipeWorkOrder(Document):
    def before_save(self):
        _recalculate_financials(self)

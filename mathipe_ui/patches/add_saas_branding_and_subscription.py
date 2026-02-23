# Copyright (c) 2026, Mathipe and contributors
# License: MIT. See LICENSE
"""SAAS: Agrega branding y planes/suscripción a Mathipe Settings. Idempotente."""

def execute():
	import frappe

	# Single DocType: no tiene tabla propia, se guarda en tabSingles
	if not frappe.db.exists("DocType", "Mathipe Settings"):
		return

	# ── Branding (Company Profile en el mismo Single) ────────────────────────
	branding_after = "invoice_provider"
	for fieldname, fieldtype, label, default, options, description in [
		("company_display_name", "Data", "Nombre visible", "APP Mathipe", None, "Nombre mostrado en cabecera y login"),
		("company_legal_name", "Data", "Razón social", None, None, "Opcional"),
		("logo", "Attach Image", "Logo", None, None, "Logo de la empresa"),
		("primary_color", "Data", "Color primario (hex)", None, None, "Ej: #4F46E5"),
		("support_email", "Data", "Email de soporte", None, None, "Opcional"),
		("timezone", "Data", "Zona horaria", None, None, "Default: zona del site"),
	]:
		if frappe.db.exists("Custom Field", {"dt": "Mathipe Settings", "fieldname": fieldname}):
			branding_after = fieldname
			continue
		props = {"label": label, "fieldtype": fieldtype, "insert_after": branding_after, "description": description or label}
		if default is not None:
			props["default"] = default
		if options:
			props["options"] = options
		frappe.get_doc({"doctype": "Custom Field", "dt": "Mathipe Settings", "fieldname": fieldname, **props}).insert()
		branding_after = fieldname

	# currency ya existe en Mathipe Settings

	# ── Subscription / Planes (sin cobros) ───────────────────────────────────
	sub_after = branding_after
	for fieldname, fieldtype, label, default, options, description in [
		("subscription_plan", "Select", "Plan", "Internal", "Internal\nBasic\nPro\nEnterprise", "Plan del tenant (Internal = todo habilitado)"),
		("subscription_status", "Select", "Estado suscripción", "Active", "Active\nTrial\nSuspended", "Active permite features según plan"),
		("trial_ends_on", "Date", "Fin de trial", None, None, "Opcional"),
		("enabled_modules", "Small Text", "Módulos habilitados", None, None, "Lista separada por comas: Finanzas, Analitica, Alertas, Tercerizacion. Vacío = según plan."),
	]:
		if frappe.db.exists("Custom Field", {"dt": "Mathipe Settings", "fieldname": fieldname}):
			sub_after = fieldname
			continue
		props = {"label": label, "fieldtype": fieldtype, "insert_after": sub_after, "description": description or label}
		if default is not None:
			props["default"] = default
		if options:
			props["options"] = options
		frappe.get_doc({"doctype": "Custom Field", "dt": "Mathipe Settings", "fieldname": fieldname, **props}).insert()
		sub_after = fieldname

	frappe.db.commit()

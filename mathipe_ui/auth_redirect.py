# Copyright (c) 2025, Mathipe UI and contributors
# Redirige a la SPA (/dashboard) después del login en lugar del Desk (/app).

from __future__ import unicode_literals

import frappe


def patch_login_redirect():
	"""Después del login, enviar al usuario al Dashboard de la SPA (estilo twist)."""
	from frappe import auth as frappe_auth

	original_set_user_info = frappe_auth.LoginManager.set_user_info

	def set_user_info(self, resume=False):
		original_set_user_info(self, resume=resume)
		if not resume and frappe.local.response.get("message") == "Logged In":
			# Redirigir a la SPA en lugar de /app
			frappe.local.response["home_page"] = "/dashboard"

	frappe_auth.LoginManager.set_user_info = set_user_info
